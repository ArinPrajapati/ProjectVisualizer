#  all configuration settings for the application

import os


class Config:
    SECERT_KEY = os.getenv("SECRET_KEY", "my_precious")
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///db.sqlite")
    SQLALCHEMY_TRACK_MODIFICATIONS = True
