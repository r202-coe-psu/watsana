import random
import datetime

from flask import Blueprint, render_template, request, redirect, url_for
from flask_login import login_required, current_user

import pandas

from watsana import models
from watsana.web import forms


module = Blueprint("students", __name__, url_prefix="/students")


@module.route("")
@login_required
def index():
    students = models.Student.objects.aggregate(
        [
            {
                "$group": {
                    "_id": ["$year", "$curriculum"],
                    "count": {"$sum": 1},
                    "brothers": {
                        "$sum": {
                            "$cond": {
                                "if": {"$ifNull": ["$brother", False]},
                                "then": 1,
                                "else": 0,
                            }
                        }
                    },
                }
            }
        ]
    )
    return render_template("admin/students/index.html", students=students)


@module.route("/show-brother/<curriculum>/<int:year>")
def show_brother(curriculum, year):
    students = models.Student.objects(curriculum__iexact=curriculum, year=year)
    return render_template(
        "admin/students/show-brother.html",
        curriculum=curriculum,
        year=year,
        students=students,
    )


@module.route("/create", methods=["GET", "POST"], defaults=dict(student_id=None))
@login_required
def create_or_edit(student_id):
    form = forms.students.StudentForm()
    student = None
    if student_id:
        student = models.Student.objects.get(id=student_id)
        form = forms.students.StudentForm(obj=student)

    if not form.validate_on_submit():
        print(form.errors)
        return render_template("admin/students/create-edit.html", form=form)

    if not student:
        student = models.Student()

    form.populate_obj(student)
    student.updated_date = datetime.datetime.now()
    student.last_updated_by = current_user._get_current_object()
    student.save()

    return redirect(url_for("admin.students.index"))


@module.route("/import-from-file", methods=["GET", "POST"])
@login_required
def import_student_from_file():
    form = forms.students.StudentFileForm()
    if not form.validate_on_submit():
        return render_template(
            "admin/students/import-student-from-file.html", form=form
        )

    dfs = pandas.read_excel(form.student_file.data)
    dfs.columns = dfs.columns.str.lower()
    for index, row in dfs.iterrows():
        student = models.Student.objects(student_id=str(row["student_id"])).first()

        if not student:
            student = models.Student(student_id=str(row["student_id"]))

        student.first_name = row["first_name"]
        student.last_name = row["last_name"]
        student.title = row["title"]
        student.year = row["year"]
        student.curriculum = row["curriculum"]
        student.last_updated_by = current_user._get_current_object()
        student.updated_date = datetime.datetime.now()
        student.save()

    return redirect(url_for("admin.students.index"))


def match_student_id(curriculum, year):
    students = models.Student.objects(
        curriculum__iexact=curriculum, year=year, brother=None
    )
    for student in students:
        old_student = models.Student.objects(
            curriculum__iexact=curriculum,
            year__ne=year,
            student_id__endswith=student.student_id[-4:],
        ).first()

        if not old_student:
            continue

        if old_student.year == student.year - 1:
            student.brother = old_student
            student.save()
            continue

        last_bother = old_student
        while next_bother := last_bother.get_next_brother():
            last_bother = next_bother

        student.brother = last_bother
        student.save()


def get_previous_year_students(curriculum, year):
    students = models.Student.objects(
        curriculum__iexact=curriculum, year=year, brother__ne=None
    ).only("brother")

    brother_ids = [s.brother.id for s in students]

    previous_year_students = list(
        models.Student.objects(
            curriculum__iexact=curriculum, year=year - 1, id__nin=brother_ids
        )
    )
    return previous_year_students


def match_random_student(curriculum, year):
    students = models.Student.objects(
        curriculum__iexact=curriculum, year=year, brother=None
    )

    previous_year_students = get_previous_year_students(curriculum, year)
    if not previous_year_students:
        return

    for student in students:
        if not previous_year_students:
            break

        student.brother = random.choice(previous_year_students)
        previous_year_students.remove(student.brother)
        student.save()


@module.route("/group/<curriculum>/<int:year>")
@login_required
def group(curriculum, year):
    # match student id
    match_student_id(curriculum, year)
    match_random_student(curriculum, year)

    return redirect(url_for("admin.students.index"))
