"""
Modelos de base de datos
"""

from sqlalchemy import (
    Column, Integer, String, Text, Boolean, DateTime, ForeignKey, UniqueConstraint,
)
from sqlalchemy.orm import relationship
from datetime import datetime, timezone

from .database import Base


def ahora():
    return datetime.now(timezone.utc)


class Link(Base):
    __tablename__ = "links"

    id = Column(Integer, primary_key=True, index=True)
    slug = Column(String(100), unique=True, index=True, nullable=False)
    target_url = Column(Text, nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text, default="")
    category = Column(String(100), default="general")
    is_active = Column(Boolean, default=True)
    click_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    last_clicked_at = Column(DateTime, nullable=True)

    clicks = relationship("Click", back_populates="link", cascade="all, delete-orphan")
    deliveries = relationship("Delivery", back_populates="link", cascade="all, delete-orphan")

class Delivery(Base):
    __tablename__ = "deliveries"

    id = Column(Integer, primary_key=True, index=True)
    link_id = Column(Integer, ForeignKey("links.id"), nullable=False)
    channel = Column(String(50), default="whatsapp") # 'whatsapp', 'instagram', 'email', 'tiktok', etc.
    delivered_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Módulo de mails. Todas opcionales: las entregas anteriores a este módulo no tienen estos
    # datos, y esa ausencia es la verdad, no un hueco que rellenar.
    contact_id = Column(Integer, ForeignKey("contacts.id"), nullable=True, index=True)
    perfil = Column(String(30), nullable=True)            # general | agencia | nuevo | phygital
    formato = Column(String(2), nullable=True)            # A | B | C | D
    sender_account_id = Column(Integer, ForeignKey("sender_accounts.id"), nullable=True)
    panel_user_id = Column(Integer, ForeignKey("panel_users.id"), nullable=True)

    link = relationship("Link", back_populates="deliveries")
    contact = relationship("Contact", back_populates="deliveries")


class Click(Base):
    __tablename__ = "clicks"

    id = Column(Integer, primary_key=True, index=True)
    link_id = Column(Integer, ForeignKey("links.id"), nullable=False)
    ip = Column(String(50), default="")
    user_agent = Column(Text, default="")
    referer = Column(Text, default="")
    clicked_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # El distintivo que viajaba en el enlace (/slug?c=<token>). Nulo = apertura anónima, que es un
    # caso legítimo: alguien entró por el enlace genérico o reenviado.
    contact_token = Column(String(64), nullable=True, index=True)

    link = relationship("Link", back_populates="clicks")


# ---------------------------------------------------------------------------
# Módulo de mails — tablas nuevas. No tocan ninguna de las anteriores.
# ---------------------------------------------------------------------------

class Contact(Base):
    """A quién escribimos. Su `token` es lo que convierte una apertura en atribuible."""
    __tablename__ = "contacts"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(200), nullable=False)
    email = Column(String(200), index=True, default="")
    empresa = Column(String(200), default="")
    origen = Column(String(50), default="")  # whatsapp | instagram | correo | evento | llamada
    token = Column(String(64), unique=True, index=True, nullable=False)
    notas = Column(Text, default="")
    created_at = Column(DateTime, default=ahora)

    deliveries = relationship("Delivery", back_populates="contact")


class PanelUser(Base):
    """
    Quién entra al panel. Retirar el acceso es poner `activo` en falso, nunca borrar la fila:
    la bitácora tiene que seguir señalando a alguien.
    """
    __tablename__ = "panel_users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(200), unique=True, index=True, nullable=False)
    nombre = Column(String(200), default="")
    rol = Column(String(30), default="comercial")  # admin | comercial
    # Solo para los usuarios de excepción (FR-001b). Vacío = entra por Google.
    password_hash = Column(String(255), nullable=True)
    activo = Column(Boolean, default=True)
    created_at = Column(DateTime, default=ahora)
    last_login_at = Column(DateTime, nullable=True)

    permisos = relationship("SenderPermission", back_populates="usuario",
                            cascade="all, delete-orphan")


class SenderAccount(Base):
    """Un buzón desde el que puede salir correo."""
    __tablename__ = "sender_accounts"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(200), unique=True, nullable=False)
    etiqueta = Column(String(100), default="")
    # 'personal' solo la usa su titular; 'compartida' admite varias personas (FR-004a).
    tipo = Column(String(20), default="personal")
    firma_nombre = Column(String(200), default="")
    firma_cargo = Column(String(200), default="")
    activa = Column(Boolean, default=True)
    # Etapa 2: REFERENCIA al token cifrado en disco. Nunca el token.
    token_ref = Column(String(200), nullable=True)

    permisos = relationship("SenderPermission", back_populates="cuenta",
                            cascade="all, delete-orphan")


class SenderPermission(Base):
    """Quién puede usar qué cuenta."""
    __tablename__ = "sender_permissions"
    __table_args__ = (
        UniqueConstraint("panel_user_id", "sender_account_id", name="uq_permiso_usuario_cuenta"),
    )

    id = Column(Integer, primary_key=True, index=True)
    panel_user_id = Column(Integer, ForeignKey("panel_users.id"), nullable=False, index=True)
    sender_account_id = Column(Integer, ForeignKey("sender_accounts.id"), nullable=False, index=True)

    usuario = relationship("PanelUser", back_populates="permisos")
    cuenta = relationship("SenderAccount", back_populates="permisos")


class Alert(Base):
    """
    El aviso de interés. La clave única sobre (contacto, enlace, ventana) es lo que impide los
    duplicados: lo rechaza la base de datos, no la memoria del programador.
    """
    __tablename__ = "alerts"
    __table_args__ = (
        UniqueConstraint("contact_id", "link_id", "ventana_inicio", name="uq_alerta_ventana"),
    )

    id = Column(Integer, primary_key=True, index=True)
    contact_id = Column(Integer, ForeignKey("contacts.id"), nullable=False, index=True)
    link_id = Column(Integer, ForeignKey("links.id"), nullable=False, index=True)
    motivo = Column(String(50), default="interes_repetido")
    conteo = Column(Integer, default=0)
    ventana_inicio = Column(DateTime, nullable=False)
    ventana_fin = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=ahora)
    visto_por = Column(Integer, ForeignKey("panel_users.id"), nullable=True)
