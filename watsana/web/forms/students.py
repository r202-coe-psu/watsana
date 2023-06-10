from flask_mongoengine.wtf import model_form
from flask_wtf import FlaskForm, file
from wtforms import fields, widgets, validators

import datetime

from .fields import TagListField, TextListField

from watsana import models

BaseStudentForm = model_form(
    models.Student,
    FlaskForm,
    exclude=[
        "created_date",
        "updated_date",
        "last_updated_by",
        "brother",
    ],
    field_args={
        "student_id": {"label": "Student ID"},
        "first_name": {"label": "First Name"},
        "last_name": {
            "label": "Last Name",
        },
        "curriculum": {"label": "Curriculum"},
        "year": {"label": "Year"},
    },
)


class StudentForm(BaseStudentForm):
    pass


class StudentFileForm(FlaskForm):
    student_file = file.FileField("Student File", validators=[file.FileRequired()])
