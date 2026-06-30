from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from app.core.config import settings

engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {},
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    from app.models import project, meeting, transcript, requirement  # noqa
    Base.metadata.create_all(bind=engine)
    _ensure_processing_job_columns()


def _ensure_processing_job_columns():
    inspector = inspect(engine)
    if "processing_jobs" not in inspector.get_table_names():
        return

    existing = {column["name"] for column in inspector.get_columns("processing_jobs")}
    columns = {
        "job_payload": "TEXT DEFAULT '{}'",
    }
    with engine.begin() as conn:
        for name, definition in columns.items():
            if name not in existing:
                conn.execute(text(f"ALTER TABLE processing_jobs ADD COLUMN {name} {definition}"))
