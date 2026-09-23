"""
Entregas a medida (especificación 002).

La presentación propia que ya se le armó a un cliente, con lo necesario para entregársela: su
enlace, las imágenes sacadas de ella y los servicios que la acompañan.

El envío sigue siendo manual: aquí no hay nada que mande un correo.
"""

from fastapi import APIRouter

from .rutas import router as _panel
from .publicas import router as _publicas

router = APIRouter()
router.include_router(_panel)
router.include_router(_publicas)
