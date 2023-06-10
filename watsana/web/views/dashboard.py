from flask import Blueprint, render_template, request, redirect, url_for
from flask_login import login_required, current_user

from watsana import models
from .. import forms

import datetime

module = Blueprint("dashboard", __name__, url_prefix="/dashboard")


def index_student():
    projects = models.Project.objects(students=current_user._get_current_object())

    classes = models.Class.objects.all()
    available_class = []
    user = current_user._get_current_object()

    for class_ in classes:
        if class_.is_in_time() and user.username in class_.student_ids:
            available_class.append(class_)

    return render_template(
        "/dashboard/index-student.html",
        projects=projects,
        available_class=available_class,
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
