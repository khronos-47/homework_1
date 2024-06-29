from sqlalchemy import Column, text
from sqlalchemy.dialects.postgresql import INTEGER, TEXT, TIMESTAMP, UUID
from sqlalchemy.sql import func

from shortener.db import DeclarativeBase


class UrlStorage(DeclarativeBase):
    __tablename__ = "url_storage"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid(),
        unique=True,
        doc="Unique id of the string in table",
    )
    long_url = Column(
        TEXT,
        nullable=False,
        index=True,
        doc="Long version of url",
    )
    short_url = Column(
        TEXT,
        nullable=False,
        index=True,
        unique=True,
        doc="Suffix of short url",
    )
    secret_key = Column(
        UUID(as_uuid=True),
        index=True,
        server_default=func.gen_random_uuid(),
        unique=True,
        doc="Secret code to access administrator features",
    )
    number_of_clicks = Column(
        INTEGER,
        nullable=False,
        server_default=text("0"),
        doc="Number of clicks on the link",
    )
    dt_created = Column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),  # pylint: disable=not-callable
        nullable=False,
        doc="Date and time when string in table was created",
    )

    def __repr__(self):
        columns = {column.name: getattr(self, column.name) for column in self.__table__.columns}
        return f'<{self.__tablename__}: {", ".join(map(lambda x: f"{x[0]}={x[1]}", columns.items()))}>'
