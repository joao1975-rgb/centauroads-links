#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────
# backup_sqlite.sh — Copia diaria EN CALIENTE y CIFRADA de la base SQLite del acortador
# hacia DigitalOcean Spaces (compatible S3).
#
# Pasos: copia consistente con la API de backup de SQLite → integrity_check de la copia →
# gzip → cifrado AES-256-CBC (openssl, PBKDF2-SHA256 600000) → verificación ida y vuelta →
# HMAC-SHA256 del cifrado (.hmac) → subida → head-object de lo subido → retención.
#
# Toda la configuración llega por variables de entorno (ver scripts/BACKUP.md). Este fichero
# no contiene secretos: la clave de cifrado se lee de BACKUP_ENCRYPTION_KEY y openssl la toma
# con `-pass env:`, así que nunca aparece en la línea de comandos ni en `ps` (el HMAC se calcula
# en bash puro por lo mismo). Las credenciales de Spaces las lee `aws` de AWS_ACCESS_KEY_ID /
# AWS_SECRET_ACCESS_KEY.
#
# Uso:  scripts/backup_sqlite.sh [--dry-run] [--help]
#       scripts/backup_sqlite.sh --verificar <copia.db.gz.enc>
#   --dry-run    hace la copia, la verifica y la cifra, pero NO sube ni borra nada en Spaces;
#                solo lista (lectura) qué copias caducarían si `aws` está disponible.
#   --verificar  comprueba el .sha256 y el .hmac de una copia descargada antes de restaurarla.
#                Solo necesita BACKUP_ENCRYPTION_KEY. Sale con código ≠ 0 si no es auténtica.
# ─────────────────────────────────────────────────────────────
set -Eeuo pipefail
umask 077

# Parámetros fijos del cifrado. Cambiarlos rompe la restauración de copias antiguas: si alguna
# vez se cambian, documentarlo en BACKUP.md. Historial: 200000 iteraciones y sin .hmac hasta
# T075/T076; desde entonces 600000 y .hmac (una copia sin .hmac es del formato antiguo).
readonly CIFRADO="aes-256-cbc"
readonly PBKDF2_ITER=600000
readonly LONGITUD_MINIMA_CLAVE=32
readonly ETIQUETA_HMAC="centaurads-links/backup-hmac/v1"
readonly BLOQUE_SHA256=64
readonly CABECERA_OPENSSL_HEX="53616c7465645f5f" # «Salted__»

MODO_PRUEBA=0
VERIFICAR=""
DIR_TRABAJO=""
CONTENEDOR_ID=""
TMP_CONTENEDOR=""

# ── Registro ────────────────────────────────────────────────
log() {
    local linea
    linea="$(date -u +%Y-%m-%dT%H:%M:%SZ) [backup_sqlite] $*"
    printf '%s\n' "$linea" >&2
    if [[ -n "${BACKUP_LOG_FILE:-}" ]]; then
        printf '%s\n' "$linea" >>"$BACKUP_LOG_FILE" || true
    fi
}

morir() {
    log "ERROR: $*"
    exit 1
}

al_fallar() {
    local codigo=$? linea=$1
    log "ERROR: fallo inesperado en la línea ${linea} (código ${codigo}). No se completó la copia."
    exit "$codigo"
}

# Borra el temporal (sin cifrar) de dentro del contenedor. Si no se puede, lo dice: no se calla.
borrar_tmp_contenedor() {
    [[ -n "$TMP_CONTENEDOR" && -n "$CONTENEDOR_ID" ]] || return 0
    local ruta=$TMP_CONTENEDOR
    TMP_CONTENEDOR=""
    if ! docker exec "$CONTENEDOR_ID" rm -f "$ruta"; then
        log "AVISO: no se pudo borrar el temporal ${ruta} dentro del contenedor ${CONTENEDOR_ID}." \
            "Contiene una copia SIN cifrar de la base: bórralo a mano."
    fi
}

limpiar() {
    borrar_tmp_contenedor
    if [[ -n "$DIR_TRABAJO" && -d "$DIR_TRABAJO" ]]; then
        rm -rf "$DIR_TRABAJO" || log "AVISO: no se pudo borrar el directorio temporal ${DIR_TRABAJO}"
    fi
}

trap 'al_fallar $LINENO' ERR
trap limpiar EXIT

ayuda() {
    sed -n '2,22p' "$0" | sed 's/^# \{0,1\}//'
}

# ── Argumentos ──────────────────────────────────────────────
while (($# > 0)); do
    case "$1" in
        --dry-run) MODO_PRUEBA=1 ;;
        --verificar)
            [[ -n "${2:-}" ]] || morir "--verificar necesita la ruta de la copia (.db.gz.enc)"
            VERIFICAR=$2
            shift
            ;;
        -h | --help) ayuda; exit 0 ;;
        *) morir "argumento desconocido: $1 (usa --help)" ;;
    esac
    shift
done

requerir_var() {
    [[ -n "${!1:-}" ]] || morir "falta la variable de entorno $1 (ver scripts/BACKUP.md)"
}

requerir_cmd() {
    command -v "$1" >/dev/null 2>&1 || morir "no se encuentra el comando '$1' en PATH"
}

hash_de() {
    sha256sum "$1" | cut -d' ' -f1
}

# ── HMAC-SHA256 (RFC 2104) en bash puro ─────────────────────
# `openssl dgst -mac HMAC` solo acepta la clave como argumento (visible en `ps`). Aquí la clave
# vive en un fichero 600 del directorio de trabajo y solo pasan por argv nombres de fichero.
hex_a_fichero() {
    local hex=$1 destino=$2 escapado="" i
    for ((i = 0; i < ${#hex}; i += 2)); do
        escapado+="\\x${hex:i:2}"
    done
    printf '%b' "$escapado" >"$destino"
}

hmac_sha256() {
    local fich_clave=$1 fich_datos=$2 clave_hex ipad="" opad="" byte interno i
    clave_hex="$(od -An -v -tx1 "$fich_clave" | tr -d ' \n\r')"
    if ((${#clave_hex} > 2 * BLOQUE_SHA256)); then
        clave_hex="$(hash_de "$fich_clave")"
    fi
    while ((${#clave_hex} < 2 * BLOQUE_SHA256)); do
        clave_hex+="00"
    done
    for ((i = 0; i < 2 * BLOQUE_SHA256; i += 2)); do
        byte=$((16#${clave_hex:i:2}))
        printf -v ipad '%s\\x%02x' "$ipad" $((byte ^ 0x36))
        printf -v opad '%s\\x%02x' "$opad" $((byte ^ 0x5c))
    done
    printf '%b' "$ipad" >"${DIR_TRABAJO}/hmac.ipad"
    printf '%b' "$opad" >"${DIR_TRABAJO}/hmac.opad"
    interno="$(cat "${DIR_TRABAJO}/hmac.ipad" "$fich_datos" | sha256sum | cut -d' ' -f1)"
    hex_a_fichero "$interno" "${DIR_TRABAJO}/hmac.interno"
    cat "${DIR_TRABAJO}/hmac.opad" "${DIR_TRABAJO}/hmac.interno" | sha256sum | cut -d' ' -f1
    rm -f "${DIR_TRABAJO}/hmac.ipad" "${DIR_TRABAJO}/hmac.opad" "${DIR_TRABAJO}/hmac.interno"
}

# Etiqueta de una copia cifrada. Clave HMAC = HMAC-SHA256(clave AES, ETIQUETA_HMAC), donde la
# clave AES es la que PBKDF2 (600000) deriva de BACKUP_ENCRYPTION_KEY con la sal del propio
# fichero (`openssl enc -P`). Así adivinar la clave cuesta lo mismo por el HMAC que por el
# cifrado (no hay atajo rápido) y la clave AES nunca se usa directamente para el HMAC.
hmac_de_copia() {
    local cifrado=$1 cabecera clave_aes clave_hmac
    cabecera="$(head -c 16 "$cifrado" | od -An -v -tx1 | tr -d ' \n\r')"
    [[ "${cabecera:0:16}" == "$CABECERA_OPENSSL_HEX" && ${#cabecera} -eq 32 ]] \
        || morir "${cifrado} no es un fichero de 'openssl enc' (falta la cabecera Salted__)"
    clave_aes="$(openssl enc -"$CIFRADO" -pbkdf2 -iter "$PBKDF2_ITER" -md sha256 \
        -S "${cabecera:16:16}" -pass env:BACKUP_ENCRYPTION_KEY -P </dev/null \
        | sed -n 's/^key *= *//p' | tr -d '\r')"
    [[ "$clave_aes" =~ ^[0-9A-Fa-f]{64}$ ]] || morir "no se pudo derivar la clave con openssl enc -P"
    hex_a_fichero "$clave_aes" "${DIR_TRABAJO}/hmac.kaes"
    printf '%s' "$ETIQUETA_HMAC" >"${DIR_TRABAJO}/hmac.etiqueta"
    clave_hmac="$(hmac_sha256 "${DIR_TRABAJO}/hmac.kaes" "${DIR_TRABAJO}/hmac.etiqueta")"
    hex_a_fichero "$clave_hmac" "${DIR_TRABAJO}/hmac.kmac"
    hmac_sha256 "${DIR_TRABAJO}/hmac.kmac" "$cifrado"
    rm -f "${DIR_TRABAJO}/hmac.kaes" "${DIR_TRABAJO}/hmac.etiqueta" "${DIR_TRABAJO}/hmac.kmac"
}

# ── Modo --verificar (restauración) ─────────────────────────
verificar_copia_descargada() {
    local cifrado=$1 esperado calculado
    [[ -f "$cifrado" ]] || morir "no existe el fichero: ${cifrado}"
    [[ -f "${cifrado}.hmac" ]] || morir "no hay ${cifrado}.hmac. Si es una copia del formato" \
        "antiguo (sin HMAC, PBKDF2 200000 iteraciones) no se puede autenticar: compruébala con su" \
        ".sha256 y descífrala con -iter 200000 como indica scripts/BACKUP.md («Copias antiguas»)."
    if [[ -f "${cifrado}.sha256" ]]; then
        esperado="$(cut -d' ' -f1 <"${cifrado}.sha256" | tr -d '\r')"
        [[ "$(hash_de "$cifrado")" == "$esperado" ]] \
            || morir "el sha256 no coincide: el fichero está dañado o truncado. NO lo restaures."
    fi
    esperado="$(cut -d' ' -f1 <"${cifrado}.hmac" | tr -d '\r' | tr 'A-F' 'a-f')"
    calculado="$(hmac_de_copia "$cifrado")"
    [[ -n "$esperado" && "$calculado" == "$esperado" ]] || morir "HMAC no coincide: el fichero" \
        "está alterado o BACKUP_ENCRYPTION_KEY no es la clave con que se cifró. NO lo restaures."
    log "HMAC correcto: ${cifrado} está íntegro y lo cifró quien tiene esta clave"
}

requerir_cmd openssl
requerir_cmd sha256sum
requerir_cmd od
requerir_cmd date
DIR_TRABAJO="$(mktemp -d "${TMPDIR:-/tmp}/backup_sqlite.XXXXXX")"

if [[ -n "$VERIFICAR" ]]; then
    requerir_var BACKUP_ENCRYPTION_KEY
    verificar_copia_descargada "$VERIFICAR"
    exit 0
fi

# ── Configuración ───────────────────────────────────────────
requerir_var BACKUP_DB_PATH
requerir_var BACKUP_BUCKET
requerir_var BACKUP_S3_ENDPOINT
requerir_var BACKUP_S3_REGION
requerir_var BACKUP_ENCRYPTION_KEY

BACKUP_PREFIX="${BACKUP_PREFIX:-centaurads-links}"
BACKUP_PREFIX="${BACKUP_PREFIX#/}"
BACKUP_PREFIX="${BACKUP_PREFIX%/}"
BACKUP_NAME="${BACKUP_NAME:-centaurads_links}"
BACKUP_RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-30}"
BACKUP_MIN_KEEP="${BACKUP_MIN_KEEP:-7}"

[[ "$BACKUP_RETENTION_DAYS" =~ ^[0-9]+$ ]] && ((BACKUP_RETENTION_DAYS >= 1)) \
    || morir "BACKUP_RETENTION_DAYS debe ser un entero >= 1 (valor: '$BACKUP_RETENTION_DAYS')"
[[ "$BACKUP_MIN_KEEP" =~ ^[1-9][0-9]*$ ]] \
    || morir "BACKUP_MIN_KEEP debe ser un entero >= 1 (valor: '$BACKUP_MIN_KEEP')"
[[ "$BACKUP_NAME" =~ ^[A-Za-z0-9_.-]+$ ]] \
    || morir "BACKUP_NAME solo admite letras, números, '_', '.' y '-'"
((${#BACKUP_ENCRYPTION_KEY} >= LONGITUD_MINIMA_CLAVE)) \
    || morir "BACKUP_ENCRYPTION_KEY es demasiado corta (mínimo ${LONGITUD_MINIMA_CLAVE} caracteres; genera una con: openssl rand -base64 48)"

# Las versiones recientes de aws-cli v2 añaden cabeceras de checksum que algunos servicios
# compatibles con S3 rechazan. Con `when_required` se comporta como antes. Se respeta si ya viene.
export AWS_REQUEST_CHECKSUM_CALCULATION="${AWS_REQUEST_CHECKSUM_CALCULATION:-when_required}"
export AWS_RESPONSE_CHECKSUM_VALIDATION="${AWS_RESPONSE_CHECKSUM_VALIDATION:-when_required}"

# ── Herramientas ────────────────────────────────────────────
requerir_cmd gzip
if ((MODO_PRUEBA == 0)); then
    requerir_cmd aws
fi

# Motor para abrir SQLite en el host: el CLI sqlite3 si existe; si no, Python (módulo sqlite3).
MOTOR_SQLITE=""
if command -v sqlite3 >/dev/null 2>&1; then
    MOTOR_SQLITE="sqlite3"
else
    for candidato in "${BACKUP_PYTHON:-}" python3 python; do
        if [[ -n "$candidato" ]] && "$candidato" -c 'import sqlite3' >/dev/null 2>&1; then
            MOTOR_SQLITE="$candidato"
            break
        fi
    done
fi
[[ -n "$MOTOR_SQLITE" ]] || morir "se necesita 'sqlite3' (apt install sqlite3) o Python 3 con el módulo sqlite3"

# Código Python auxiliar (se pasa con `-c`, igual en el host que con `docker exec`). No lleva
# barras ni barras invertidas para que Git Bash en Windows no las reescriba como rutas.
readonly PY_SQLITE='
import os, sqlite3, sys
modo, origen = sys.argv[1], sys.argv[2]
if not os.path.isfile(origen):
    sys.exit(modo + ": no existe la base " + origen)
if modo == "copiar":
    src = sqlite3.connect(origen, timeout=30)
    dst = sqlite3.connect(sys.argv[3])
    src.backup(dst)
    dst.execute("PRAGMA journal_mode=DELETE")
    dst.close()
    src.close()
elif modo == "verificar":
    con = sqlite3.connect(origen)
    print(con.execute("PRAGMA integrity_check").fetchone()[0])
    print(con.execute("SELECT count(*) FROM sqlite_master WHERE type=:t", {"t": "table"}).fetchone()[0])
    con.close()
'

# Copia consistente en caliente: la API de backup de SQLite respeta los bloqueos y el WAL,
# a diferencia de `cp`, que puede capturar la base a medio escribir.
copiar_local() {
    local origen=$1 destino=$2
    [[ -f "$origen" ]] || morir "no existe la base de datos: $origen"
    if [[ "$MOTOR_SQLITE" == "sqlite3" ]]; then
        sqlite3 -bail "$origen" ".timeout 30000" ".backup '$destino'"
        sqlite3 -bail "$destino" "PRAGMA journal_mode=DELETE;" >/dev/null
    else
        "$MOTOR_SQLITE" -c "$PY_SQLITE" copiar "$origen" "$destino"
    fi
}

# Variante para cuando la base vive dentro de un contenedor (BACKUP_DOCKER_CONTAINER): la copia se
# hace DENTRO con el Python de la imagen y luego se extrae con `docker cp`. El temporal se crea
# con mktemp (nombre impredecible) y chmod 600 ANTES de escribir la copia en él; SQLite crea su
# -journal con los mismos permisos que el fichero.
copiar_desde_contenedor() {
    local destino=$1 filtro=$BACKUP_DOCKER_CONTAINER ids
    requerir_cmd docker
    ids="$(docker ps -q --filter "name=${filtro}")"
    [[ -n "$ids" ]] || morir "no hay ningún contenedor en ejecución que coincida con '${filtro}'"
    (($(printf '%s\n' "$ids" | wc -l) == 1)) \
        || morir "hay varios contenedores que coinciden con '${filtro}'; usa un nombre más preciso"
    CONTENEDOR_ID="$ids"
    TMP_CONTENEDOR="$(docker exec "$CONTENEDOR_ID" mktemp "/tmp/${BACKUP_NAME}-backup.XXXXXXXX" \
        | tr -d '\r')"
    [[ "$TMP_CONTENEDOR" == /tmp/"${BACKUP_NAME}"-backup.* ]] \
        || morir "mktemp dentro del contenedor no devolvió una ruta válida: '${TMP_CONTENEDOR}'"
    docker exec "$CONTENEDOR_ID" chmod 600 "$TMP_CONTENEDOR"
    log "Copiando dentro del contenedor ${CONTENEDOR_ID} (${BACKUP_DB_PATH})"
    docker exec "$CONTENEDOR_ID" "${BACKUP_DOCKER_PYTHON:-python}" -c "$PY_SQLITE" \
        copiar "$BACKUP_DB_PATH" "$TMP_CONTENEDOR"
    docker cp "${CONTENEDOR_ID}:${TMP_CONTENEDOR}" "$destino"
    borrar_tmp_contenedor
}

verificar_copia() {
    local copia=$1 resultado tablas
    if [[ "$MOTOR_SQLITE" == "sqlite3" ]]; then
        resultado="$(sqlite3 -bail "$copia" "PRAGMA integrity_check;")"
        tablas="$(sqlite3 -bail "$copia" "SELECT count(*) FROM sqlite_master WHERE type='table';")"
    else
        local salida
        salida="$("$MOTOR_SQLITE" -c "$PY_SQLITE" verificar "$copia" | tr -d '\r')"
        resultado="$(printf '%s\n' "$salida" | sed -n 1p)"
        tablas="$(printf '%s\n' "$salida" | sed -n 2p)"
    fi
    [[ "$resultado" == "ok" ]] || morir "integrity_check de la copia falló: ${resultado}"
    [[ "$tablas" =~ ^[0-9]+$ ]] && ((tablas > 0)) \
        || morir "la copia no contiene tablas; ¿BACKUP_DB_PATH apunta a la base correcta?"
    log "Copia verificada: integrity_check=ok, ${tablas} tablas"
}

# ── Copia, verificación, compresión y cifrado ───────────────
SELLO="$(date -u +%Y%m%dT%H%M%SZ)"
ARCHIVO="${BACKUP_NAME}-${SELLO}.db.gz.enc"
COPIA="${DIR_TRABAJO}/${BACKUP_NAME}.db"
CIFRADA="${DIR_TRABAJO}/${ARCHIVO}"
SUMA="${CIFRADA}.sha256"
ETIQUETA="${CIFRADA}.hmac"

if ((MODO_PRUEBA == 1)); then
    log "MODO PRUEBA (--dry-run): no se subirá ni borrará nada en Spaces"
fi

if [[ -n "${BACKUP_DOCKER_CONTAINER:-}" ]]; then
    copiar_desde_contenedor "$COPIA"
else
    log "Copiando en caliente ${BACKUP_DB_PATH}"
    copiar_local "$BACKUP_DB_PATH" "$COPIA"
fi
verificar_copia "$COPIA"
HASH_COPIA="$(hash_de "$COPIA")"

gzip -9 -c "$COPIA" \
    | openssl enc -"$CIFRADO" -pbkdf2 -iter "$PBKDF2_ITER" -md sha256 -salt \
        -pass env:BACKUP_ENCRYPTION_KEY -out "$CIFRADA"

# Ida y vuelta: se descifra lo que se va a subir y se compara con la copia. Así un fallo de
# cifrado o de clave se detecta hoy, no el día que haga falta restaurar.
HASH_IDA_VUELTA="$(openssl enc -d -"$CIFRADO" -pbkdf2 -iter "$PBKDF2_ITER" -md sha256 \
    -pass env:BACKUP_ENCRYPTION_KEY -in "$CIFRADA" | gzip -dc | sha256sum | cut -d' ' -f1)"
[[ "$HASH_IDA_VUELTA" == "$HASH_COPIA" ]] \
    || morir "el descifrado de prueba no reproduce la copia original"

# CBC no autentica: el .sha256 (sin clave) solo detecta daños accidentales; el .hmac (con clave)
# detecta además una alteración deliberada, porque sin BACKUP_ENCRYPTION_KEY no se puede rehacer.
printf '%s  %s\n' "$(hash_de "$CIFRADA")" "$ARCHIVO" >"$SUMA"
HMAC_COPIA="$(hmac_de_copia "$CIFRADA")"
printf '%s  %s\n' "$HMAC_COPIA" "$ARCHIVO" >"$ETIQUETA"
log "Cifrado y verificado: ${ARCHIVO} ($(wc -c <"$CIFRADA" | tr -d ' ') bytes)"

if [[ -n "${BACKUP_OUTPUT_DIR:-}" ]]; then
    mkdir -p "$BACKUP_OUTPUT_DIR"
    cp "$CIFRADA" "$SUMA" "$ETIQUETA" "$BACKUP_OUTPUT_DIR/"
    log "Copia local dejada en ${BACKUP_OUTPUT_DIR}/${ARCHIVO}"
fi

# ── Subida y comprobación de lo subido ──────────────────────
s3() {
    aws --endpoint-url "$BACKUP_S3_ENDPOINT" --region "$BACKUP_S3_REGION" s3 "$@"
}

s3api() {
    aws --endpoint-url "$BACKUP_S3_ENDPOINT" --region "$BACKUP_S3_REGION" s3api "$@"
}

# Antes de borrar nada por retención, se confirma que el objeto existe en Spaces con el tamaño
# exacto del fichero local. Si no, se sale con error y las copias antiguas se quedan.
verificar_subida() {
    local fichero=$1 clave=$2 esperado remoto
    esperado="$(wc -c <"$fichero" | tr -d ' ')"
    if ! remoto="$(s3api head-object --bucket "$BACKUP_BUCKET" --key "$clave" \
        --query ContentLength --output text)"; then
        morir "no se pudo comprobar ${clave} con head-object tras subirlo; no se aplica la retención"
    fi
    remoto="${remoto//[$'\r\n ']/}"
    [[ "$remoto" == "$esperado" ]] || morir "el objeto subido ${clave} no coincide en tamaño" \
        "(local ${esperado} B, remoto ${remoto:-?} B); no se aplica la retención"
}

DESTINO="s3://${BACKUP_BUCKET}/${BACKUP_PREFIX}"
CLAVE_BASE="${BACKUP_PREFIX:+${BACKUP_PREFIX}/}"
if ((MODO_PRUEBA == 1)); then
    log "[dry-run] Se subiría ${ARCHIVO} con su .sha256 y su .hmac a ${DESTINO}/"
else
    for fichero in "$CIFRADA" "$SUMA" "$ETIQUETA"; do
        s3 cp --only-show-errors "$fichero" "${DESTINO}/$(basename "$fichero")"
    done
    for fichero in "$CIFRADA" "$SUMA" "$ETIQUETA"; do
        verificar_subida "$fichero" "${CLAVE_BASE}$(basename "$fichero")"
    done
    log "Subido y comprobado (head-object) en ${DESTINO}/${ARCHIVO}"
fi

# ── Retención ───────────────────────────────────────────────
# Solo se consideran objetos con el nombre exacto que genera este script; nunca se toca nada más
# del bucket. La fecha sale del nombre (UTC), no de la fecha de modificación del objeto. Las
# BACKUP_MIN_KEEP copias más recientes (contando la de hoy) no se borran aunque hayan caducado:
# si el cron dejó de funcionar semanas, no se queda el bucket vacío.
CORTE="$(date -u -d "-${BACKUP_RETENTION_DAYS} days" +%Y%m%dT%H%M%SZ)"
PUNTO_ESCAPADO='\.'
PATRON="^${BACKUP_NAME//./$PUNTO_ESCAPADO}-([0-9]{8}T[0-9]{6}Z)\\.db\\.gz\\.enc(\\.sha256|\\.hmac)?$"

if ((MODO_PRUEBA == 1)) && ! command -v aws >/dev/null 2>&1; then
    log "[dry-run] 'aws' no está disponible: se omite el cálculo de retención"
    LISTADO=""
elif ! LISTADO="$(s3 ls "${DESTINO}/")"; then
    if ((MODO_PRUEBA == 1)); then
        log "[dry-run] No se pudo listar ${DESTINO}/ (¿prefijo vacío o credenciales?)"
        LISTADO=""
    else
        morir "no se pudo listar ${DESTINO}/ para aplicar la retención"
    fi
fi

NOMBRES=()
declare -A SELLOS_COPIAS=(["$SELLO"]=1)
while read -r _fecha _hora _tamano nombre; do
    nombre="${nombre%$'\r'}"
    if [[ -n "${nombre:-}" && "$nombre" =~ $PATRON ]]; then
        NOMBRES+=("$nombre")
        if [[ -z "${BASH_REMATCH[2]}" ]]; then
            SELLOS_COPIAS["${BASH_REMATCH[1]}"]=1
        fi
    fi
done <<<"$LISTADO"

mapfile -t PROTEGIDOS < <(printf '%s\n' "${!SELLOS_COPIAS[@]}" | sort -r | head -n "$BACKUP_MIN_KEEP")
protegido() {
    local p
    for p in "${PROTEGIDOS[@]}"; do
        [[ "$p" == "$1" ]] && return 0
    done
    return 1
}

BORRADOS=0
CONSERVADOS=0
for nombre in "${NOMBRES[@]}"; do
    [[ "$nombre" =~ $PATRON ]] || continue
    sello="${BASH_REMATCH[1]}"
    [[ "$sello" < "$CORTE" ]] || continue
    if protegido "$sello"; then
        CONSERVADOS=$((CONSERVADOS + 1))
        continue
    fi
    if ((MODO_PRUEBA == 1)); then
        log "[dry-run] Se borraría por retención (> ${BACKUP_RETENTION_DAYS} días): ${nombre}"
    else
        s3 rm --only-show-errors "${DESTINO}/${nombre}"
        log "Borrado por retención (> ${BACKUP_RETENTION_DAYS} días): ${nombre}"
    fi
    BORRADOS=$((BORRADOS + 1))
done
if ((CONSERVADOS > 0)); then
    log "Se conservan ${CONSERVADOS} objeto(s) caducado(s) para mantener al menos" \
        "BACKUP_MIN_KEEP=${BACKUP_MIN_KEEP} copias"
fi

log "Terminado: ${ARCHIVO} · sha256 de la base ${HASH_COPIA} · ${BORRADOS} objeto(s) caducado(s)"
