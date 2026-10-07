"""
Textos de los perfiles (especificación 005).

Los textos de cada perfil de cliente —su mensaje y sus tres asuntos— dejan de exigir un programador:
un administrador los cambia en el panel y llegan a todos los compositores sin desplegar nada. El
servidor guarda solo lo cambiado; lo demás es el texto de serie que trae el motor.
"""

from fastapi import APIRouter

from .pantalla import router as _pantalla
from .rutas import router as _rutas

router = APIRouter()
router.include_router(_rutas)
router.include_router(_pantalla)
