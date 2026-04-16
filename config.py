import os

class Config:

    SECRET_KEY = os.environ.get("SECRET_KEY", "clave-super-secreta")

    DATABASE_URL = os.environ.get("DATABASE_URL")

    if DATABASE_URL:
        if DATABASE_URL.startswith("postgres://"):
            DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

    SQLALCHEMY_DATABASE_URI = DATABASE_URL if DATABASE_URL else "sqlite:///local.db"

    SQLALCHEMY_TRACK_MODIFICATIONS = False
