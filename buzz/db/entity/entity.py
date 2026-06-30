from abc import ABC

from PyQt6.QtSql import QSqlRecord


class Entity(ABC):
    @classmethod
    def from_record(cls, record: QSqlRecord):
        kwargs = {record.fieldName(i): record.value(i) for i in range(record.count())}
        return cls(**kwargs)

    def to_dict(self) -> dict:
        return dict(self.__dict__)
