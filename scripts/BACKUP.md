# Respaldo de la base SQLite del acortador

`scripts/backup_sqlite.sh` hace una copia **en caliente** (API de backup de SQLite, compatible con
WAL), la verifica con `PRAGMA integrity_check`, la comprime con gzip, la cifra con AES-256
(`openssl enc -aes-256-cbc -pbkdf2 -iter 600000 -md sha256`), comprueba que el descifrado
reproduce la copia, calcula un **HMAC-SHA256** del fichero cifrado, sube a DigitalOcean Spaces
el `.enc` con su `.sha256` y su `.hmac`, comprueba cada objeto subido con `s3api head-object`
(mismo tamaño que el local) y solo entonces borra las copias que superan la retención,
conservando siempre las `BACKUP_MIN_KEEP` más recientes. Ante cualquier fallo sale con código
≠ 0 y un mensaje `ERROR: ...`; si lo subido no cuadra, **no borra nada**.

```bash
scripts/backup_sqlite.sh --dry-run            # todo menos subir/borrar (solo lista qué caducaría)
scripts/backup_sqlite.sh                      # copia real
scripts/backup_sqlite.sh --verificar F.enc    # antes de restaurar: autentica una copia descargada
```

### Por qué `.hmac` además de `.sha256`

AES-CBC no autentica: un fichero alterado puede descifrarse a basura (o a algo manipulado) sin
error. El `.sha256` vive en el mismo bucket y no lleva clave, así que quien pueda escribir en el
bucket puede cambiar el `.enc` y rehacer el `.sha256`. El `.hmac` sí depende de la clave:

- clave AES = PBKDF2-SHA256(`BACKUP_ENCRYPTION_KEY`, sal del propio `.enc`, 600000)[:32]
  (la misma que usa `openssl enc`; se obtiene con `openssl enc ... -S <sal> -P`);
- clave HMAC = HMAC-SHA256(clave AES, `centaurads-links/backup-hmac/v1`);
- `.hmac` = HMAC-SHA256(clave HMAC, fichero `.enc` completo), en hexadecimal.

Derivarla con PBKDF2 evita que el `.hmac` sirva de atajo rápido para adivinar la clave. El
script calcula el HMAC en bash puro para que ninguna clave aparezca en `ps`.

## Variables de entorno

| Variable | Obligatoria | Ejemplo / valor por defecto |
|---|---|---|
| `BACKUP_DB_PATH` | sí | `/app/data/centaurads_links.db` (ruta dentro del contenedor si se usa `BACKUP_DOCKER_CONTAINER`) |
| `BACKUP_BUCKET` | sí | nombre del bucket de Spaces |
| `BACKUP_S3_ENDPOINT` | sí | `https://nyc3.digitaloceanspaces.com` |
| `BACKUP_S3_REGION` | sí | `nyc3` |
| `BACKUP_ENCRYPTION_KEY` | sí | ≥ 32 caracteres. Generar con `openssl rand -base64 48` y guardarla **también fuera del droplet** (gestor de contraseñas): sin ella las copias no sirven |
| `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` | sí (salvo `--dry-run`) | claves de Spaces; las lee `aws` directamente |
| `BACKUP_PREFIX` | no | `centaurads-links` |
| `BACKUP_NAME` | no | `centaurads_links` → objetos `centaurads_links-AAAAMMDDTHHMMSSZ.db.gz.enc` |
| `BACKUP_RETENTION_DAYS` | no | `30` (entero ≥ 1; solo borra objetos con ese patrón de nombre) |
| `BACKUP_MIN_KEEP` | no | `7` (entero ≥ 1): nunca se borran las N copias más recientes (contando la de hoy), aunque hayan superado la retención. Protege si el cron estuvo parado semanas |
| `BACKUP_DOCKER_CONTAINER` | no | filtro de nombre del contenedor (p. ej. `centauro_links`); si se define, la copia se hace dentro con `docker exec` |
| `BACKUP_DOCKER_PYTHON` | no | `python` (intérprete dentro del contenedor) |
| `BACKUP_LOG_FILE` | no | fichero donde añadir el registro (además de stderr) |
| `BACKUP_OUTPUT_DIR` | no | deja también una copia local del `.enc`, su `.sha256` y su `.hmac` |
| `BACKUP_PYTHON` | no | intérprete del host si no hay `sqlite3` |

Herramientas en el host: `bash` ≥ 4, `openssl`, `gzip`, `sha256sum`, `od`, GNU `date`, AWS CLI
(`snap install aws-cli --classic` o el instalador oficial v2) y `sqlite3` (`apt install sqlite3`)
o Python 3. En modo contenedor basta con `docker` y Python 3 en el host para la verificación.

## Dónde está la base en producción

El acortador corre en Docker Swarm gestionado por EasyPanel. La imagen usa
`DATABASE_URL=sqlite:///./data/centaurads_links.db` con `WORKDIR /app`, así que **dentro del
contenedor** la base es `/app/data/centaurads_links.db`, montada desde un volumen. Para
localizarla en el host:

```bash
docker ps --format '{{.ID}}  {{.Names}}' | grep -i links            # nombre real de la tarea
docker inspect <ID> --format '{{range .Mounts}}{{.Source}} -> {{.Destination}}{{"\n"}}{{end}}'
```

La línea que termina en `-> /app/data` da la carpeta del host. Hay dos formas de respaldar:

- **Modo contenedor (recomendado)**: `BACKUP_DOCKER_CONTAINER=<filtro>` y
  `BACKUP_DB_PATH=/app/data/centaurads_links.db`. No depende de la ruta del volumen, que cambia
  si se recrea el servicio. El filtro debe coincidir con **un solo** contenedor en ejecución.
- **Ruta del host**: `BACKUP_DB_PATH=<Source>/centaurads_links.db`, con `sqlite3` instalado.

Nunca copiar el `.db` con `cp`: con WAL activo, los cambios recientes viven en `-wal`/`-shm`.

En modo contenedor la copia intermedia (sin cifrar) se crea dentro con `mktemp` y `chmod 600`
antes de escribirla, y se borra al terminar; si no se puede borrar, el registro lo dice con
`AVISO: no se pudo borrar el temporal ...` (hay que borrarlo a mano).

## Programarlo con cron (host)

1. Copiar el script, p. ej. a `/opt/centaurads-links/scripts/backup_sqlite.sh` (`chmod 700`).
2. Guardar las variables en `/etc/centaurads/backup.env`, propiedad de root y con `chmod 600`
   (líneas `export VAR=valor`). Ese fichero no se versiona.
3. `/etc/cron.d/centaurads-backup`:

```cron
SHELL=/bin/bash
15 3 * * * root . /etc/centaurads/backup.env && /opt/centaurads-links/scripts/backup_sqlite.sh >>/var/log/centaurads-backup.log 2>&1
```

Probar primero con `--dry-run` a mano. El aviso ante fallos lo da el monitoreo externo (T069):
por ejemplo, encadenar `&& curl -fsS <url-de-heartbeat>` para que la ausencia de latido avise.

## Restaurar

```bash
. /etc/centaurads/backup.env        # o: read -rs BACKUP_ENCRYPTION_KEY && export BACKUP_ENCRYPTION_KEY
EP=https://nyc3.digitaloceanspaces.com; B=s3://<bucket>/centaurads-links
aws --endpoint-url "$EP" s3 ls "$B/"                              # elegir la copia
F=centaurads_links-AAAAMMDDTHHMMSSZ.db.gz.enc
for x in "" .sha256 .hmac; do aws --endpoint-url "$EP" s3 cp "$B/$F$x" .; done

scripts/backup_sqlite.sh --verificar "$F"                         # 1. sha256 + HMAC: debe decir «HMAC correcto»
openssl enc -d -aes-256-cbc -pbkdf2 -iter 600000 -md sha256 \
  -pass env:BACKUP_ENCRYPTION_KEY -in "$F" | gunzip > restaurada.db   # 2. descifrar y descomprimir
sqlite3 restaurada.db "PRAGMA integrity_check;"                   # 3. debe decir: ok
```

Si `--verificar` dice `HMAC no coincide`, **no restaurar esa copia**: está alterada o la clave no
es la correcta. Probar con la copia anterior.

### Verificar sin el script

Equivalente con `openssl` (hace falta el `.hmac`). Úsalo solo en un equipo de confianza: aquí las
claves derivadas pasan como argumento y se ven en `ps` mientras corre.

```bash
SAL=$(head -c 16 "$F" | tail -c 8 | od -An -v -tx1 | tr -d " \n")
KAES=$(openssl enc -aes-256-cbc -pbkdf2 -iter 600000 -md sha256 -S "$SAL" -pass env:BACKUP_ENCRYPTION_KEY -P | sed -n 's/^key=//p')
KMAC=$(printf %s centaurads-links/backup-hmac/v1 | openssl dgst -sha256 -mac HMAC -macopt hexkey:"$KAES" -r | cut -d' ' -f1)
openssl dgst -sha256 -mac HMAC -macopt hexkey:"$KMAC" -r "$F" | cut -d' ' -f1   # debe ser igual a:
cut -d' ' -f1 "$F.hmac"
```

### Copias antiguas (sin `.hmac`)

Las copias hechas antes de T075/T076 no tienen `.hmac` y se cifraron con **200000** iteraciones
(la presencia del `.hmac` indica el formato: con `.hmac` → 600000). No se pueden autenticar, solo
comprobar contra accidentes con su `.sha256`:

```bash
sha256sum -c "$F.sha256"
openssl enc -d -aes-256-cbc -pbkdf2 -iter 200000 -md sha256 \
  -pass env:BACKUP_ENCRYPTION_KEY -in "$F" | gunzip > restaurada.db
```

Con la retención por defecto (30 días) dejan de existir un mes después del despliegue del cambio.

4. **Reemplazar**: detener el servicio en EasyPanel (o `docker service scale <servicio>=0`);
   guardar aparte la base actual **con** sus `-wal` y `-shm`; copiar `restaurada.db` como
   `<Source>/centaurads_links.db`; **borrar los `centaurads_links.db-wal` y `-shm` antiguos**
   (si quedan, SQLite aplicaría el WAL viejo sobre la base restaurada y la corrompería); arrancar
   el servicio y comprobar `/health` y un enlace corto conocido.

La restauración de prueba cronometrada se documenta en
`specs/001-saneamiento-ecosistema/checklists/restauracion.md` (T070).
