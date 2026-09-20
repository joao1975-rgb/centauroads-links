"""
Las dependencias de FastAPI que resuelven "quién eres" y "qué puedes hacer".

Aquí vive la regla que el cliente eligió (FR-004a): **una cuenta personal solo la usa su
titular**; `mercadeo@` es compartida. Está en un solo sitio a propósito — si la comprobación
estuviera repartida por las rutas, bastaría olvidarla en una para que alguien firmara un correo
con el nombre de otra persona.
"""

import logging
from typing import Optional

from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session

from ..database import get_db
from .. import models
from . import sesion

log = logging.getLogger("centaurads.auth")


def usuario_actual_opcional(
    request: Request,
    db: Session = Depends(get_db),
) -> Optional[models.PanelUser]:
    """
    Quién está entrando, o None si nadie. No falla: para las páginas que se comportan distinto
    según haya sesión o no (la pantalla de entrada, por ejemplo).
    """
    datos = sesion.leer(request.cookies.get(sesion.COOKIE))
    if not datos:
        return None

    usuario = db.query(models.PanelUser).filter(
        models.PanelUser.id == datos.get("uid")
    ).first()

    # Una sesión válida de alguien a quien ya se le retiró el acceso no sirve. Se comprueba en
    # cada petición, no solo al entrar, para que la baja tenga efecto inmediato.
    if not usuario or not usuario.activo:
        return None
    return usuario


def usuario_actual(
    usuario: Optional[models.PanelUser] = Depends(usuario_actual_opcional),
) -> models.PanelUser:
    """Exige sesión. Es la dependencia normal de todo lo que hay dentro del panel."""
    if usuario is None:
        raise HTTPException(status_code=401, detail="Hay que entrar al panel")
    return usuario


def solo_admin(
    usuario: models.PanelUser = Depends(usuario_actual),
) -> models.PanelUser:
    """Para lo que administra a otras personas: altas, bajas y permisos."""
    if usuario.rol != "admin":
        raise HTTPException(status_code=403, detail="Hace falta rol de administrador")
    return usuario


def cuentas_permitidas(db: Session, usuario: models.PanelUser) -> list[models.SenderAccount]:
    """Las cuentas remitentes que esa persona puede usar. Un admin no las tiene todas por serlo."""
    return (
        db.query(models.SenderAccount)
        .join(models.SenderPermission,
              models.SenderPermission.sender_account_id == models.SenderAccount.id)
        .filter(models.SenderPermission.panel_user_id == usuario.id,
                models.SenderAccount.activa.is_(True))
        .all()
    )


def exigir_cuenta(
    db: Session, usuario: models.PanelUser, sender_account_id: int
) -> models.SenderAccount:
    """
    Comprueba que esa persona puede enviar desde esa cuenta, y devuelve la cuenta.

    Dos capas, a propósito:
      1) ¿Tiene permiso explícito?
      2) Si la cuenta es `personal`, ¿es suya? Aunque alguien concediera el permiso por error, una
         cuenta personal sigue siendo de su titular. El correo lleva su nombre en la firma.
    """
    cuenta = db.query(models.SenderAccount).filter(
        models.SenderAccount.id == sender_account_id
    ).first()
    if not cuenta or not cuenta.activa:
        raise HTTPException(status_code=404, detail="Cuenta remitente no disponible")

    permiso = db.query(models.SenderPermission).filter(
        models.SenderPermission.panel_user_id == usuario.id,
        models.SenderPermission.sender_account_id == cuenta.id,
    ).first()
    if not permiso:
        log.warning("%s intentó usar %s sin permiso", usuario.email, cuenta.email)
        raise HTTPException(
            status_code=403,
            detail=f"No tienes permiso para enviar desde {cuenta.email}",
        )

    if cuenta.tipo == "personal" and cuenta.email.strip().lower() != usuario.email.strip().lower():
        log.warning("%s intentó usar la cuenta personal de %s", usuario.email, cuenta.email)
        raise HTTPException(
            status_code=403,
            detail=f"{cuenta.email} es una cuenta personal: solo la usa su titular",
        )

    return cuenta


def puede_conceder(cuenta: models.SenderAccount, usuario: models.PanelUser) -> bool:
    """
    ¿Tiene sentido dar a esa persona permiso sobre esa cuenta?

    La regla se valida también al conceder, no solo al enviar, para que la base de permisos no
    acumule combinaciones imposibles que confundan a quien las revise.
    """
    if cuenta.tipo == "compartida":
        return True
    return cuenta.email.strip().lower() == usuario.email.strip().lower()
