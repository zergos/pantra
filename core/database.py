from core.defaults import db_params
from db.models import db


def connect():
    db.connect(**db_params)


def disconnect():
    db.disconnect()

