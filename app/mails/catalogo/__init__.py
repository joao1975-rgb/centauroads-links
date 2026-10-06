"""
Catálogo de líneas de negocio (especificación 003).

Lo que el compositor ofrece como servicios deja de estar escrito en el motor: vive en la base,
nace igual que el de serie y lo administra el panel. Una línea nueva sale en los correos del equipo
sin desplegar nada, y cada línea dice en qué plantillas aparece.
"""

from fastapi import APIRouter

from .pantalla import router as _pantalla
from .rutas import router as _rutas

router = APIRouter()
router.include_router(_rutas)
router.include_router(_pantalla)
