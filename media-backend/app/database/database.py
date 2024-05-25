import logging
import os
import sqlalchemy as _sql
import sqlalchemy.ext.declarative as _declarative
import sqlalchemy.orm as _orm

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://myuser:1234@db:5432/fastapi_database")

engine = _sql.create_engine(DATABASE_URL)

def init_db():
    from app.database.models import Media, Artist, Album, User, Post
    logging.info("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    logging.info("Database tables created.")

SessionLocal = _orm.sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = _declarative.declarative_base()