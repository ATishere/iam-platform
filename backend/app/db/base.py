"""Declarative base cho tất cả models.

Import tất cả models ở đây để Alembic autogenerate nhìn thấy chúng
khi gọi `Base.metadata`.
"""

from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase

# Naming convention giúp Alembic sinh tên constraint ổn định
# (tránh migration lỗi khi rename/drop constraint).
NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING_CONVENTION)


# Import muộn để tránh vòng lặp import; dòng noqa giữ lint yên.
from app.models import (  # noqa: E402,F401
    audit_log,
    organization,
    password_reset_token,
    permission,
    refresh_token,
    role,
    role_permission,
    session,
    user,
    user_role,
)
