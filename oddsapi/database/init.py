from sqlalchemy import QueuePool
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

from oddsapi.settings import DATABASE_CONNECTION, DB_ECHO

engine = None


def get_engine():
    global engine

    if engine:
        return engine

    engine = create_async_engine(
        DATABASE_CONNECTION,
        echo=DB_ECHO,
        pool_size=10,
        poolclass=QueuePool,
    )
    return engine


engine = get_engine()

SessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass
