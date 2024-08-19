

from sqlalchemy import Column, String, UUID
from uuid6 import uuid7

from app.db.session import Base


class User(Base):
    __tablename__ = "users"

    user_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid7)
    username = Column(String, unique=True, index=True)
    first_name = Column(String)
    middle_name = Column(String, nullable=True)
    last_name = Column(String)
    department = Column(String)
    password = Column(String)

