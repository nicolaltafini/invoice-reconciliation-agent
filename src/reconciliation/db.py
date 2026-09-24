from collections.abc import Iterator

from sqlalchemy import URL, create_engine
from sqlalchemy.orm import Session

from reconciliation.config import settings

database_url = URL.create(
    "postgresql+psycopg",
    username=settings.db_user,
    password=settings.db_password,
    host=settings.db_host,
    port=settings.db_port,
    database=settings.db_name,
)

engine = create_engine(database_url, pool_pre_ping=True)


def get_session() -> Iterator[Session]:
    with Session(engine) as session:
        yield session