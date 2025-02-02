from flask_mongoengine import MongoEngine
from .users import User
from .students import Student
from .oauth2 import OAuth2Token

__all__ = ["User"]

db = MongoEngine()

def init_db(app):
    db.init_app(app)
