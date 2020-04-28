from core.defaults import DB_PARAMS
from db.models import db


def connect():
    db.connect(**DB_PARAMS)


def disconnect():
    db.disconnect()

