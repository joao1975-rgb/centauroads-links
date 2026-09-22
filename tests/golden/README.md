# Referencia byte a byte de las plantillas

Estos 14 ficheros son la salida **exacta** de `prototipos/mail/build.js` con el motor tal y como
estaba en el commit `8745a4b`, antes de partirlo en bloques y recetas (fase 1 de
[002-entregas](../../specs/002-entregas/tasks.md)).

No son ejemplos ni documentación: son la red. La refactorización del motor no puede cambiar ni un
byte de lo que el equipo ya usa (FR-126, SC-105). Quien los mire para entender el formato está
usándolos bien; quien los edite a mano, no.

## Cómo se comprueban

- `node prototipos/mail/build.js` compara su salida con esta carpeta y **falla** si difiere.
- `pytest tests/test_plantillas_identicas.py` hace la misma comprobación desde las pruebas.

## Cómo se actualizan

Solo cuando el cambio de contenido es **querido**, y mirando lo que cambia:

```bash
node prototipos/mail/build.js            # falla y dice qué ficheros difieren
git diff --stat tests/golden             # (tras actualizarlos) qué cambió de verdad
GOLDEN_UPDATE=1 node prototipos/mail/build.js
```

Actualizarlos para "que deje de fallar" es desactivar la puerta. Si el cambio no era querido, lo
que se corrige es el motor.
