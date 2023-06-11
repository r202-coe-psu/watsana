import datetime
import mongoengine as me

from flask import url_for

CURRICULUMS = (("AIE", "AIE"), ("CoE", "CoE"))


class Student(me.Document):
    student_id = me.StringField(required=True, unique=True, max_length=200)

    title = me.StringField(max_length=50)
    first_name = me.StringField(required=True, max_length=200)
    last_name = me.StringField(required=True, max_length=200)
    curriculum = me.StringField(required=True, max_length=10, choices=CURRICULUMS)
    year = me.IntField(required=True)

    last_updated_by = me.ReferenceField("User", dbref=True, required=True)
    created_date = me.DateTimeField(required=True, default=datetime.datetime.now)
    updated_date = me.DateTimeField(
        required=True, default=datetime.datetime.now, auto_now=True
    )

    brothers = me.ListField(me.ReferenceField("Student", dbref=True))

    meta = {
        "collection": "students",
        "indexes": [
            "student_id",
            "$student_id",
            "#student_id",
        ],
    }

    @property
    def fullname(self):
        return self.get_fullname()

    def get_fullname(self):
        return f"{self.first_name} {self.last_name}"

    def get_picture(self):
        if self.picture:
            return url_for(
                "accounts.picture", user_id=self.id, filename=self.picture.filename
            )
        if "google" in self.resources:
            return self.resources["google"].get("picture", "")
        return url_for("static", filename="images/user.png")

    def get_little_brothers(self):
        return Student.objects(brothers=self)
