import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'clave-super-secreta'
    SQLALCHEMY_DATABASE_URI = 'postgresql://postgres:NEWPASSWORD@localhost:5432/creditos_fintech1'
    SQLALCHEMY_TRACK_MODIFICATIONS = False