"""
T066 · Pruebas de scripts/backup_sqlite.sh (copia en caliente, cifrada, hacia Spaces).

El script se ejecuta de verdad con bash contra una base SQLite temporal. `aws` y `docker` se
sustituyen por dobles en PATH que registran cómo se les llama, así que nada sale de la máquina.
Se comprueba lo que importa el día que haya que restaurar: que la copia cifrada se puede
descifrar con la clave, que pasa integrity_check y que trae también lo que aún estaba en el WAL.

T075/T076: PBKDF2 con 600 000 iteraciones, HMAC-SHA256 del cifrado (`.hmac`, clave derivada de
BACKUP_ENCRYPTION_KEY) comprobado contra la implementación estándar de Python, `--verificar` para
la restauración, mínimo de copias en la retención (BACKUP_MIN_KEEP), comprobación del objeto
subido con `s3api head-object` antes de borrar nada y temporal del contenedor con `mktemp`.

En Windows se usa el bash de Git for Windows (el de System32 es WSL y no ve estas rutas). Si no
hay bash o faltan openssl/gzip/sha256sum, las pruebas se saltan con el motivo.
"""

import gzip
import hashlib
import hmac
import os
import re
import shutil
import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
SCRIPT = RAIZ / "scripts" / "backup_sqlite.sh"

# Valor sintético, solo para estas pruebas.
CLAVE = "clave-sintetica-solo-para-pruebas-no-es-real"
NOMBRE = "centaurads_links"
ITERACIONES = 600_000
ITERACIONES_ANTIGUAS = 200_000
ETIQUETA_HMAC = b"centaurads-links/backup-hmac/v1"


def _buscar_bash() -> str | None:
    if os.name == "nt":
        for ruta in (
            r"C:\Program Files\Git\bin\bash.exe",
            r"C:\Program Files (x86)\Git\bin\bash.exe",
        ):
            if Path(ruta).is_file():
                return ruta
        return None
    return shutil.which("bash")


BASH = _buscar_bash()


def _herramientas_disponibles() -> bool:
    if not BASH:
        return False
    r = subprocess.run(
        [BASH, "-c", "command -v openssl && command -v gzip && command -v sha256sum"],
        capture_output=True,
    )
    return r.returncode == 0


pytestmark = pytest.mark.skipif(
    not _herramientas_disponibles(),
    reason="Se necesita bash (Git Bash en Windows) con openssl, gzip y sha256sum",
)

AWS_FALSO = r"""#!/usr/bin/env bash
printf '%s\n' "$*" >>"$FAKE_AWS_LOG"
while [[ $# -gt 0 && "$1" != "s3" && "$1" != "s3api" ]]; do shift; done
servicio=$1; shift
sub=$1; shift
if [[ "${FAKE_AWS_FALLAR:-}" == "$sub" ]]; then echo "fallo simulado de aws" >&2; exit 1; fi
if [[ "$servicio" == "s3api" ]]; then
  clave=""
  while [[ $# -gt 0 ]]; do if [[ "$1" == "--key" ]]; then clave=$2; fi; shift; done
  f="$FAKE_BUCKET/$(basename "$clave")"
  if [[ "$sub" == "head-object" ]]; then
    if [[ ! -e "$f" ]]; then echo "Not Found (404)" >&2; exit 254; fi
    if [[ -n "${FAKE_HEAD_TAMANO:-}" ]]; then echo "$FAKE_HEAD_TAMANO"; else wc -c <"$f" | tr -d ' '; fi
  fi
  exit 0
fi
posicionales=()
for a in "$@"; do [[ "$a" == --* ]] || posicionales+=("$a"); done
case "$sub" in
  cp) cp "${posicionales[0]}" "$FAKE_BUCKET/$(basename "${posicionales[1]}")" ;;
  ls) if [[ -n "${FAKE_AWS_LS:-}" ]]; then cat "$FAKE_AWS_LS"; fi
      for f in "$FAKE_BUCKET"/*; do
        if [[ -e "$f" ]]; then echo "2026-01-01 00:00:00 1 $(basename "$f")"; fi
      done ;;
  rm) ;;
esac
"""

DOCKER_FALSO = r"""#!/usr/bin/env bash
printf '%s\n' "$*" >>"$FAKE_DOCKER_LOG"
case "$1" in
  ps) filtro="${4#name=}"
      for c in ${FAKE_CONTENEDORES:-}; do if [[ "$c" == *"$filtro"* ]]; then echo "id-$c"; fi; done ;;
  exec) shift 2
        if [[ "${FAKE_DOCKER_RM_FALLAR:-}" == 1 && "$1" == rm ]]; then echo "rm: fallo simulado" >&2; exit 1; fi
        exec "$@" ;;
  cp) cp "${2#*:}" "$3" ;;
esac
"""


def _escribir_ejecutable(ruta: Path, contenido: str) -> None:
    ruta.write_text(contenido, encoding="utf-8", newline="\n")
    ruta.chmod(0o755)


def _posix(ruta: Path) -> str:
    return ruta.as_posix()


def _crear_base_en_wal(ruta: Path) -> tuple[sqlite3.Connection, list[tuple]]:
    """Base en WAL con filas que siguen en el -wal (sin checkpoint) mientras la conexión vive."""
    con = sqlite3.connect(ruta)
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("PRAGMA wal_autocheckpoint=0")
    con.execute("CREATE TABLE links (id INTEGER PRIMARY KEY, codigo TEXT NOT NULL)")
    filas = [(i, f"codigo-{i}") for i in range(1, 51)]
    con.executemany("INSERT INTO links VALUES (?, ?)", filas)
    con.commit()
    return con, filas


@pytest.fixture
def entorno(tmp_path):
    bin_falso = tmp_path / "bin"
    bin_falso.mkdir()
    _escribir_ejecutable(bin_falso / "aws", AWS_FALSO)
    _escribir_ejecutable(bin_falso / "docker", DOCKER_FALSO)

    bucket = tmp_path / "bucket"
    bucket.mkdir()
    salida = tmp_path / "salida"
    temporales = tmp_path / "tmp"
    temporales.mkdir()
    base = tmp_path / "origen.db"

    env = os.environ.copy()
    for var in list(env):
        if var.startswith(("BACKUP_", "AWS_")):
            del env[var]
    env.update(
        {
            "PATH": str(bin_falso) + os.pathsep + env.get("PATH", ""),
            "BACKUP_DB_PATH": _posix(base),
            "BACKUP_BUCKET": "bucket-de-prueba",
            "BACKUP_S3_ENDPOINT": "https://nyc3.digitaloceanspaces.example.test",
            "BACKUP_S3_REGION": "nyc3",
            "BACKUP_ENCRYPTION_KEY": CLAVE,
            "BACKUP_PREFIX": "centaurads-links",
            "BACKUP_RETENTION_DAYS": "30",
            "BACKUP_OUTPUT_DIR": _posix(salida),
            "BACKUP_LOG_FILE": _posix(tmp_path / "backup.log"),
            "BACKUP_PYTHON": _posix(Path(sys.executable)),
            "TMPDIR": _posix(temporales),
            "FAKE_AWS_LOG": _posix(tmp_path / "aws.log"),
            "FAKE_DOCKER_LOG": _posix(tmp_path / "docker.log"),
            "FAKE_BUCKET": _posix(bucket),
        }
    )
    return {
        "env": env,
        "tmp": tmp_path,
        "base": base,
        "bucket": bucket,
        "salida": salida,
        "temporales": temporales,
    }


def _ejecutar(entorno, *args, **extra_env) -> subprocess.CompletedProcess:
    env = {**entorno["env"], **extra_env}
    return subprocess.run(
        [BASH, _posix(SCRIPT), *args],
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=120,
    )


def _llamadas_aws(entorno) -> list[str]:
    log = entorno["tmp"] / "aws.log"
    return log.read_text(encoding="utf-8").splitlines() if log.exists() else []


def _borrados(entorno) -> list[str]:
    return sorted(c.rsplit("/", 1)[-1] for c in _llamadas_aws(entorno) if " s3 rm " in f" {c} ")


def _openssl_descifrar(entorno, cifrado: Path, salida: Path, iteraciones: int):
    return subprocess.run(
        [
            BASH, "-c",
            f"openssl enc -d -aes-256-cbc -pbkdf2 -iter {iteraciones} -md sha256 "
            '-pass env:BACKUP_ENCRYPTION_KEY -in "$1" -out "$2"',
            "_", _posix(cifrado), _posix(salida),
        ],
        env=entorno["env"],
        capture_output=True,
        text=True,
    )


def _descifrar(entorno, cifrado: Path, destino: Path) -> None:
    """Restaura como indica BACKUP.md: openssl enc -d (600 000 iteraciones) → gunzip."""
    comprimido = destino.with_suffix(".gz")
    r = _openssl_descifrar(entorno, cifrado, comprimido, ITERACIONES)
    assert r.returncode == 0, r.stderr
    destino.write_bytes(gzip.decompress(comprimido.read_bytes()))


def _hmac_esperado(cifrado: Path, clave: str = CLAVE) -> str:
    """HMAC-SHA256 estándar (módulo hmac de Python) con la derivación que documenta BACKUP.md:
    clave AES = PBKDF2-SHA256(clave, sal del fichero, 600 000)[:32];
    clave HMAC = HMAC-SHA256(clave AES, etiqueta); resultado = HMAC-SHA256(clave HMAC, fichero)."""
    datos = cifrado.read_bytes()
    assert datos[:8] == b"Salted__"
    clave_aes = hashlib.pbkdf2_hmac("sha256", clave.encode(), datos[8:16], ITERACIONES, 48)[:32]
    clave_hmac = hmac.new(clave_aes, ETIQUETA_HMAC, hashlib.sha256).digest()
    return hmac.new(clave_hmac, datos, hashlib.sha256).hexdigest()


def _env_solo_clave(entorno) -> dict:
    """Entorno de restauración: solo la clave, nada de la configuración de la copia."""
    env = {k: v for k, v in entorno["env"].items() if not k.startswith("BACKUP_")}
    env["BACKUP_ENCRYPTION_KEY"] = CLAVE
    return env


def _verificar(entorno, cifrado: Path, **extra_env) -> subprocess.CompletedProcess:
    return subprocess.run(
        [BASH, _posix(SCRIPT), "--verificar", _posix(cifrado)],
        env={**_env_solo_clave(entorno), **extra_env},
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=120,
    )


def _unico(directorio: Path, patron: str) -> Path:
    encontrados = sorted(directorio.glob(patron))
    assert len(encontrados) == 1, encontrados
    return encontrados[0]


def _copia_en_salida(entorno) -> Path:
    """Hace una copia --dry-run y devuelve el .enc que queda en BACKUP_OUTPUT_DIR."""
    _crear_base_en_wal(entorno["base"])[0].close()
    r = _ejecutar(entorno, "--dry-run")
    assert r.returncode == 0, r.stderr
    return _unico(entorno["salida"], f"{NOMBRE}-*.db.gz.enc")


def _listado_remoto(entorno, *nombres: str) -> str:
    ruta = entorno["tmp"] / "listado.txt"
    ruta.write_text(
        "".join(f"2026-01-01 00:00:00 123 {n}\n" for n in nombres),
        encoding="utf-8",
        newline="\n",
    )
    return _posix(ruta)


def _temporal_del_contenedor(entorno) -> str:
    lineas = (entorno["tmp"] / "docker.log").read_text(encoding="utf-8").splitlines()
    chmods = [l.split()[-1] for l in lineas if l.startswith("exec ") and " chmod 600 " in f"{l} "]
    assert len(chmods) == 1, lineas
    return chmods[0]


# ── Camino feliz ────────────────────────────────────────────


def test_dry_run_cifra_una_copia_restaurable_sin_subir_nada(entorno):
    con, filas = _crear_base_en_wal(entorno["base"])
    try:
        # La conexión sigue abierta y las filas están en el -wal: es una copia EN CALIENTE.
        assert Path(str(entorno["base"]) + "-wal").stat().st_size > 0
        antiguo = f"{NOMBRE}-20200101T000000Z.db.gz.enc"
        r = _ejecutar(entorno, "--dry-run", BACKUP_MIN_KEEP="1",
                      FAKE_AWS_LS=_listado_remoto(entorno, antiguo))
    finally:
        con.close()

    assert r.returncode == 0, r.stderr
    llamadas = _llamadas_aws(entorno)
    assert llamadas and all(" s3 ls " in f" {c} " for c in llamadas), llamadas
    assert not any(entorno["bucket"].iterdir()), "en --dry-run no se sube nada"
    assert "Se borraría por retención" in r.stderr and antiguo in r.stderr

    cifrado = _unico(entorno["salida"], f"{NOMBRE}-*.db.gz.enc")
    suma = cifrado.with_name(cifrado.name + ".sha256")
    esperado = suma.read_text(encoding="utf-8").split()[0]
    assert hashlib.sha256(cifrado.read_bytes()).hexdigest() == esperado
    etiqueta = cifrado.with_name(cifrado.name + ".hmac").read_text(encoding="utf-8").split()
    assert etiqueta == [_hmac_esperado(cifrado), cifrado.name]

    restaurada = entorno["tmp"] / "restaurada.db"
    _descifrar(entorno, cifrado, restaurada)
    rc = sqlite3.connect(restaurada)
    try:
        assert rc.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        assert rc.execute("SELECT id, codigo FROM links ORDER BY id").fetchall() == filas
        assert rc.execute("PRAGMA journal_mode").fetchone()[0] == "delete"
    finally:
        rc.close()

    assert not any(entorno["temporales"].iterdir()), "los temporales deben borrarse"
    assert "Terminado" in (entorno["tmp"] / "backup.log").read_text(encoding="utf-8")


def test_sube_a_spaces_y_aplica_la_retencion_solo_a_sus_copias(entorno):
    con, _ = _crear_base_en_wal(entorno["base"])
    con.close()
    antiguo = f"{NOMBRE}-20200101T000000Z.db.gz.enc"
    antiguo_suma = antiguo + ".sha256"
    antiguo_hmac = antiguo + ".hmac"
    reciente = f"{NOMBRE}-20990101T000000Z.db.gz.enc"
    ajeno_viejo = "otra_base-20200101T000000Z.db.gz.enc"
    listado = _listado_remoto(entorno, antiguo, antiguo_suma, antiguo_hmac, reciente, ajeno_viejo,
                              "notas.txt")

    r = _ejecutar(entorno, BACKUP_MIN_KEEP="1", FAKE_AWS_LS=listado)

    assert r.returncode == 0, r.stderr
    llamadas = _llamadas_aws(entorno)
    subidas = [c for c in llamadas if " s3 cp " in f" {c} "]
    assert len(subidas) == 3
    for c in subidas:
        assert "--endpoint-url https://nyc3.digitaloceanspaces.example.test" in c
        assert "--region nyc3" in c
        assert "s3://bucket-de-prueba/centaurads-links/" in c
    subidos = sorted(p.name for p in entorno["bucket"].iterdir())
    assert len(subidos) == 3
    assert subidos[1:] == [subidos[0] + ".hmac", subidos[0] + ".sha256"]

    # Cada objeto subido se comprueba con head-object ANTES de la retención.
    cabeceras = [c for c in llamadas if " s3api head-object " in f" {c} "]
    assert len(cabeceras) == 3
    for nombre in subidos:
        assert any(f"--bucket bucket-de-prueba --key centaurads-links/{nombre} " in f"{c} "
                   for c in cabeceras), (nombre, cabeceras)
    primer_rm = next(i for i, c in enumerate(llamadas) if " s3 rm " in f" {c} ")
    assert all(llamadas.index(c) < primer_rm for c in cabeceras)

    assert _borrados(entorno) == sorted([antiguo, antiguo_suma, antiguo_hmac])
    assert not any(entorno["temporales"].iterdir())


def test_modo_contenedor_copia_dentro_y_extrae_con_docker_cp(entorno):
    con, filas = _crear_base_en_wal(entorno["base"])
    try:
        r = _ejecutar(
            entorno,
            "--dry-run",
            BACKUP_DOCKER_CONTAINER="links_app",
            BACKUP_DOCKER_PYTHON=_posix(Path(sys.executable)),
            FAKE_CONTENEDORES="centauro_links_app.1.abc",
        )
    finally:
        con.close()

    assert r.returncode == 0, r.stderr
    docker = (entorno["tmp"] / "docker.log").read_text(encoding="utf-8")
    assert "exec id-centauro_links_app.1.abc" in docker
    assert "cp id-centauro_links_app.1.abc:" in docker

    # Temporal impredecible (mktemp dentro del contenedor), chmod 600 antes de escribir en él y
    # borrado al terminar. Antes era /tmp/<nombre>-backup-<PID>.db, adivinable.
    lineas = docker.splitlines()
    temporal = _temporal_del_contenedor(entorno)
    i_mktemp = next(i for i, l in enumerate(lineas) if " mktemp " in f" {l} ")
    i_chmod = next(i for i, l in enumerate(lineas) if " chmod 600 " in f" {l} ")
    i_copia = next(i for i, l in enumerate(lineas) if " copiar " in f" {l} ")
    assert i_mktemp < i_chmod < i_copia
    assert f"rm -f {temporal}" in docker
    assert not re.search(r"-backup-\d+\.db", docker), "el temporal no debe depender del PID"

    restaurada = entorno["tmp"] / "restaurada.db"
    _descifrar(entorno, _unico(entorno["salida"], "*.db.gz.enc"), restaurada)
    rc = sqlite3.connect(restaurada)
    try:
        assert rc.execute("SELECT id, codigo FROM links ORDER BY id").fetchall() == filas
    finally:
        rc.close()


def test_modo_contenedor_avisa_si_no_puede_borrar_el_temporal(entorno):
    con, _ = _crear_base_en_wal(entorno["base"])
    try:
        r = _ejecutar(
            entorno,
            "--dry-run",
            BACKUP_DOCKER_CONTAINER="links_app",
            BACKUP_DOCKER_PYTHON=_posix(Path(sys.executable)),
            FAKE_CONTENEDORES="centauro_links_app.1.abc",
            FAKE_DOCKER_RM_FALLAR="1",
        )
    finally:
        con.close()
        # El doble no borró el temporal (simula el fallo): se limpia aquí.
        registro = entorno["tmp"] / "docker.log"
        if registro.exists() and " chmod 600 " in registro.read_text(encoding="utf-8"):
            subprocess.run([BASH, "-c", 'rm -f "$1"', "_", _temporal_del_contenedor(entorno)])

    # La copia ya está hecha y verificada: no se da por fallida, pero se avisa, no se calla.
    assert r.returncode == 0, r.stderr
    assert "AVISO" in r.stderr and "no se pudo borrar" in r.stderr


# ── Cifrado autenticado (T075/T076) ─────────────────────────


def test_cifra_con_600000_iteraciones(entorno):
    cifrado = _copia_en_salida(entorno)
    assert _openssl_descifrar(entorno, cifrado, entorno["tmp"] / "a.gz", ITERACIONES).returncode == 0
    r = _openssl_descifrar(entorno, cifrado, entorno["tmp"] / "b.gz", ITERACIONES_ANTIGUAS)
    assert r.returncode != 0, "con 200 000 iteraciones no debe descifrar: la copia usa 600 000"


def test_verificar_acepta_una_copia_integra(entorno):
    cifrado = _copia_en_salida(entorno)
    r = _verificar(entorno, cifrado)
    assert r.returncode == 0, r.stderr
    assert "HMAC correcto" in r.stderr


def test_verificar_rechaza_una_copia_alterada(entorno):
    cifrado = _copia_en_salida(entorno)
    datos = bytearray(cifrado.read_bytes())
    datos[-1] ^= 0x01
    cifrado.write_bytes(bytes(datos))
    # Se recalcula el .sha256 para que solo el HMAC pueda detectarlo: quien altera el fichero en
    # el bucket también puede reescribir el .sha256, que no lleva clave.
    suma = cifrado.with_name(cifrado.name + ".sha256")
    suma.write_text(f"{hashlib.sha256(bytes(datos)).hexdigest()}  {cifrado.name}\n", encoding="utf-8")

    r = _verificar(entorno, cifrado)
    assert r.returncode != 0
    assert "HMAC no coincide" in r.stderr


def test_verificar_rechaza_una_clave_incorrecta(entorno):
    cifrado = _copia_en_salida(entorno)
    r = _verificar(entorno, cifrado, BACKUP_ENCRYPTION_KEY=CLAVE + "-distinta")
    assert r.returncode != 0
    assert "HMAC no coincide" in r.stderr


def test_verificar_una_copia_antigua_sin_hmac_explica_como_restaurarla(entorno):
    cifrado = _copia_en_salida(entorno)
    cifrado.with_name(cifrado.name + ".hmac").unlink()
    r = _verificar(entorno, cifrado)
    assert r.returncode != 0
    assert "200000" in r.stderr and "BACKUP.md" in r.stderr


def test_verificacion_manual_con_openssl_documentada_en_backup_md(entorno):
    """La alternativa sin el script (BACKUP.md, «Verificar sin el script») da el mismo HMAC."""
    cifrado = _copia_en_salida(entorno)
    manual = "\n".join([
        'SAL=$(head -c 16 "$F" | tail -c 8 | od -An -v -tx1 | tr -d " \\n")',
        "KAES=$(openssl enc -aes-256-cbc -pbkdf2 -iter 600000 -md sha256 -S \"$SAL\" "
        "-pass env:BACKUP_ENCRYPTION_KEY -P | sed -n 's/^key=//p')",
        "KMAC=$(printf %s centaurads-links/backup-hmac/v1 "
        "| openssl dgst -sha256 -mac HMAC -macopt hexkey:\"$KAES\" -r | cut -d' ' -f1)",
        "openssl dgst -sha256 -mac HMAC -macopt hexkey:\"$KMAC\" -r \"$F\" | cut -d' ' -f1",
    ])
    documento = SCRIPT.with_name("BACKUP.md").read_text(encoding="utf-8")
    assert "centaurads-links/backup-hmac/v1" in documento
    r = subprocess.run(
        [BASH, "-c", manual],
        env={**_env_solo_clave(entorno), "F": _posix(cifrado)},
        capture_output=True,
        text=True,
    )
    assert r.returncode == 0, r.stderr
    assert r.stdout.strip() == _hmac_esperado(cifrado)


# ── Retención segura (T075/T076) ────────────────────────────


def test_la_retencion_conserva_un_minimo_de_copias(entorno):
    _crear_base_en_wal(entorno["base"])[0].close()
    viejas = [f"{NOMBRE}-2020010{d}T000000Z.db.gz.enc" for d in (1, 2, 3)]
    listado = _listado_remoto(entorno, *viejas, *(v + ".sha256" for v in viejas))

    # Por defecto (7) no se borra ninguna: solo hay 4 copias contando la de hoy.
    r = _ejecutar(entorno, FAKE_AWS_LS=listado)
    assert r.returncode == 0, r.stderr
    assert _borrados(entorno) == []
    assert "BACKUP_MIN_KEEP" in r.stderr

    # Con 2: se quedan la de hoy y la más reciente de las caducadas.
    (entorno["tmp"] / "aws.log").unlink()
    for f in entorno["bucket"].iterdir():
        f.unlink()
    r = _ejecutar(entorno, BACKUP_MIN_KEEP="2", FAKE_AWS_LS=listado)
    assert r.returncode == 0, r.stderr
    assert _borrados(entorno) == sorted(
        [viejas[0], viejas[0] + ".sha256", viejas[1], viejas[1] + ".sha256"]
    )


def test_no_aplica_la_retencion_si_el_objeto_subido_no_coincide(entorno):
    _crear_base_en_wal(entorno["base"])[0].close()
    antiguo = f"{NOMBRE}-20200101T000000Z.db.gz.enc"
    r = _ejecutar(entorno, BACKUP_MIN_KEEP="1", FAKE_HEAD_TAMANO="1",
                  FAKE_AWS_LS=_listado_remoto(entorno, antiguo))
    assert r.returncode != 0
    assert "no coincide" in r.stderr
    assert _borrados(entorno) == []


def test_no_aplica_la_retencion_si_head_object_falla(entorno):
    _crear_base_en_wal(entorno["base"])[0].close()
    antiguo = f"{NOMBRE}-20200101T000000Z.db.gz.enc"
    r = _ejecutar(entorno, BACKUP_MIN_KEEP="1", FAKE_AWS_FALLAR="head-object",
                  FAKE_AWS_LS=_listado_remoto(entorno, antiguo))
    assert r.returncode != 0
    assert "head-object" in r.stderr
    assert _borrados(entorno) == []


# ── Fallos: código ≠ 0, mensaje claro y sin efectos a medias ─


@pytest.mark.parametrize(
    "variable",
    ["BACKUP_DB_PATH", "BACKUP_BUCKET", "BACKUP_S3_ENDPOINT", "BACKUP_S3_REGION",
     "BACKUP_ENCRYPTION_KEY"],
)
def test_falla_si_falta_una_variable_obligatoria(entorno, variable):
    del entorno["env"][variable]
    r = _ejecutar(entorno, "--dry-run")
    assert r.returncode != 0
    assert variable in r.stderr


def test_falla_con_clave_de_cifrado_corta(entorno):
    _crear_base_en_wal(entorno["base"])[0].close()
    r = _ejecutar(entorno, "--dry-run", BACKUP_ENCRYPTION_KEY="corta")
    assert r.returncode != 0
    assert "demasiado corta" in r.stderr


def test_falla_si_la_base_no_existe(entorno):
    r = _ejecutar(entorno, "--dry-run")
    assert r.returncode != 0
    assert "no existe" in r.stderr
    assert not entorno["base"].exists(), "no debe crear una base vacía por error"
    assert not any(entorno["temporales"].iterdir())


def test_falla_si_la_base_no_tiene_tablas(entorno):
    sqlite3.connect(entorno["base"]).execute("PRAGMA user_version=1").connection.close()
    r = _ejecutar(entorno, "--dry-run")
    assert r.returncode != 0
    assert "no contiene tablas" in r.stderr


def test_si_falla_la_subida_no_borra_nada_y_sale_con_error(entorno):
    _crear_base_en_wal(entorno["base"])[0].close()
    antiguo = f"{NOMBRE}-20200101T000000Z.db.gz.enc"
    r = _ejecutar(entorno, BACKUP_MIN_KEEP="1", FAKE_AWS_FALLAR="cp",
                  FAKE_AWS_LS=_listado_remoto(entorno, antiguo))
    assert r.returncode != 0
    assert "ERROR" in r.stderr
    assert _borrados(entorno) == []
    assert not any(entorno["temporales"].iterdir())


def test_rechaza_retencion_invalida(entorno):
    r = _ejecutar(entorno, "--dry-run", BACKUP_RETENTION_DAYS="0")
    assert r.returncode != 0
    assert "BACKUP_RETENTION_DAYS" in r.stderr


@pytest.mark.parametrize("valor", ["0", "-1", "siete"])
def test_rechaza_min_keep_invalido(entorno, valor):
    r = _ejecutar(entorno, "--dry-run", BACKUP_MIN_KEEP=valor)
    assert r.returncode != 0
    assert "BACKUP_MIN_KEEP" in r.stderr


def test_modo_contenedor_falla_si_no_hay_contenedor(entorno):
    r = _ejecutar(entorno, "--dry-run", BACKUP_DOCKER_CONTAINER="no_existe",
                  FAKE_CONTENEDORES="otro.1.abc")
    assert r.returncode != 0
    assert "no hay ningún contenedor" in r.stderr
