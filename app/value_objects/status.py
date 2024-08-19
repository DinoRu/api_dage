from enum import Enum
from typing import Union, Dict, Any

from pydantic.v1 import ConstrainedStr

from app.value_objects.base import ValueObject


class StatusState(Enum):
    EXECUTING = "Выполняется"
    CHECKING = "Проверяется"
    COMPLETED = "Выполнено"
    OVERDUE = "Просрочено"
    DELETED = "Удалено"


class Status(ValueObject[StatusState]):
    value: StatusState
