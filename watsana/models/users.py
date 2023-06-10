import datetime
import mongoengine as me

from flask import url_for
from flask_login import UserMixin


class User(me.Document, UserMixin):
    username = me.StringField(required=True, unique=True, max_length=200)

    title = me.StringField(max_length=50)
    email = me.StringField(required=True, unique=True, max_length=200)
    first_name = me.StringField(required=True, max_length=200)
    last_name = me.StringField(required=True, max_length=200)

    title_th = me.StringField(max_length=50, default="")
    first_name_th = me.StringField(max_length=200, default="")
    last_name_th = me.StringField(max_length=200, default="")

    biography = me.StringField()

    picture = me.ImageField(thumbnail_size=(800, 600, True))

    status = me.StringField(required=True, default="disactive")
    roles = me.ListField(me.StringField(), default=["user"], max_length=200)

    created_date = me.DateTimeField(required=True, default=datetime.datetime.now)
    updated_date = me.DateTimeField(required=True, default=datetime.datetime.now)
    last_login_date = me.DateTimeField(
        required=True, default=datetime.datetime.now, auto_now=True
    )

    resources = me.DictField()

    meta = {"collection": "users", "strict": False}

    @property
    def fullname(self):
        return self.get_fullname()

    def get_fullname(self):
        return f"{self.first_name} {self.last_name}"

    def has_roles(self, *roles):
        for role in roles:
            if role in self.roles:
                return True
        return False

    def get_picture(self):
        if self.picture:
            return url_for(
                "accounts.picture", user_id=self.id, filename=self.picture.filename
            )
        if "google" in self.resources:
            return self.resources["google"].get("picture", "")
        return url_for("static", filename="images/user.png")
