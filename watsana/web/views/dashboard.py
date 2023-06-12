from flask import Blueprint, render_template, request, redirect, url_for
from flask_login import login_required, current_user

from watsana import models
from .. import forms
from .admin import students as students_view

import datetime

module = Blueprint("dashboard", __name__, url_prefix="/dashboard")


def index_student():
    students = []

    student = models.Student.objects(student_id=current_user.username).first()
    if student:
        students.append(student)
        brothers = []

        stuents_view.get_brothers(student, brothers)
        student_view.get_little_brothers(student, brothers)
        students.extend(brothers)

    return render_template(
        "/dashboard/index-student.html",
        students=students,
    )


def index_user():
    return render_template("/dashboard/index.html")


@module.route("")
@login_required
def index():
    user = current_user
    if "student" in user.roles:
        return index_student()
    elif "admin" in user.roles:
        return redirect(url_for("admin.index"))

    return index_user()
