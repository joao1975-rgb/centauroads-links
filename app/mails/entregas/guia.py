"""
La guía personalizada (plantilla I, especificación 012): lo que la entrega guarda de ella.

Es la F («Que te conozcan / Que te recuerden / Que te compren») por cliente: sus textos y hasta tres
fases, cada una con UN producto del catálogo. La presentación propia de cada fase no vive aquí: es el
espacio de la entrega de ese producto (004), como en la H. Por eso el producto no se puede repetir.

Se guarda como JSON en `entregas.guia`. Este módulo solo valida la forma; los textos se guardan tal
cual llegan (el motor del correo es quien los pinta y escapa).
"""

import json
from typing import List, Literal, Optional

from pydantic import BaseModel, Field, field_validator

from . import almacen

FASES = ("conozcan", "recuerden", "compren")
FORMATOS = ("H", "I")


class FaseGuia(BaseModel):
    clave: Literal["conozcan", "recuerden", "compren"]
    on: bool = True
    fase: str = Field(default="", max_length=120)
    titulo: str = Field(default="", max_length=300)
    texto: str = Field(default="", max_length=3000)
    etiqueta: str = Field(default="", max_length=120)
    detalle: str = Field(default="", max_length=1000)
    linea: str = Field(min_length=1, max_length=64)

    @field_validator("linea")
    @classmethod
    def _linea_con_forma(cls, v: str) -> str:
        if not almacen.linea_valida(v):
            raise ValueError("producto no válido")
        return v


class Guia(BaseModel):
    entrada: str = Field(default="", max_length=3000)
    saludo: str = Field(default="", max_length=300)
    parrafo: str = Field(default="", max_length=3000)
    caja_titulo: str = Field(default="", max_length=300)
    caja_texto: str = Field(default="", max_length=1000)
    cta_texto: str = Field(default="", max_length=1000)
    boton: str = Field(default="", max_length=120)
    fases: List[FaseGuia] = Field(default_factory=list, max_length=len(FASES))

    @field_validator("fases")
    @classmethod
    def _sin_repetir(cls, v: List[FaseGuia]) -> List[FaseGuia]:
        if len({f.clave for f in v}) != len(v):
            raise ValueError("una fase repetida")
        if len({f.linea for f in v}) != len(v):
            raise ValueError("un producto no puede estar en dos fases")
        return v


def a_texto(guia: Optional[Guia]) -> Optional[str]:
    return guia.model_dump_json() if guia is not None else None


def de_texto(texto: Optional[str]) -> Optional[dict]:
    return json.loads(texto) if texto else None
