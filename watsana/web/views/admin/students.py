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
                                "if": {"$eq": ["$brothers", []]},
                                "then": 0,
                                "else": 1,
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
@module.route("/<student_id>/edit", methods=["GET", "POST"])
@login_required
def create_or_edit(student_id):
    form = forms.students.StudentForm()
    student = None
    if student_id:
        student = models.Student.objects.get(id=student_id)
        form = forms.students.StudentForm(obj=student)

    if not form.validate_on_submit():
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
        curriculum__iexact=curriculum, year=year, brothers=[]
    )
    for student in students:
        old_student = models.Student.objects(
            curriculum__iexact=curriculum,
            year__ne=year,
            student_id__endswith=student.student_id[-4:],
        ).first()

        if not old_student:
            continue

        if old_student.year > student.year:
            continue

        print("match", student.student_id, old_student.student_id)

        if old_student.year == student.year - 1:
            student.brothers.append(old_student)
            student.save()
            continue

        last_bother = old_student
        while next_bothers := last_bother.get_little_brothers():
            # need discussion
            last_bother = random.choice(next_bothers)

        student.brothers.append(last_bother)
        student.save()


def get_previous_year_students(curriculum, year):
    students = models.Student.objects(
        curriculum__iexact=curriculum, year=year, brothers__ne=None
    ).only("brothers")

    brothers = []
    for student in students:
        for brother in student.brothers:
            brothers.append(brother)
    brother_ids = [brother.id for brother in brothers]

    previous_year_students = list(
        models.Student.objects(
            curriculum__iexact=curriculum, year=year - 1, id__nin=brother_ids
        )
    )
    return previous_year_students


def match_random_student(curriculum, year):
    students = models.Student.objects(
        curriculum__iexact=curriculum, year=year, brothers=[]
    )

    previous_year_students = get_previous_year_students(curriculum, year)

    for student in students:
        if not previous_year_students:
            previous_year_students = list(
                models.Student.objects(curriculum__iexact=curriculum, year=year - 1)
            )

        brother = random.choice(previous_year_students)
        student.brothers.append(brother)
        previous_year_students.remove(brother)
        student.save()


def match_final(curriculum, year):
    previous_students = list(
        models.Student.objects(curriculum__iexact=curriculum, year=year - 1)
    )

    students = models.Student.objects(curriculum__iexact=curriculum, year=year)

    for student in students:
        for brother in student.brothers:
            if brother in previous_students:
                previous_students.remove(brother)

    student_choices = list(students)
    for ps in previous_students:
        student = random.choice(student_choices)
        student.brothers.append(ps)
        student.save()


@module.route("/group/<curriculum>/<int:year>")
@login_required
def group(curriculum, year):
    final = request.args.get("final")

    # match student id
    print("match student id")
    match_student_id(curriculum, year)
    print("match random student")
    match_random_student(curriculum, year)

    if final == "true":
        print("match random student final")
        match_final(curriculum, year)

    return redirect(
        url_for("admin.students.show_brother", curriculum=curriculum, year=year)
    )


def get_brothers(student, brothers):
    for brother in student.brothers:
        if brother not in brothers:
            brothers.append(brother)

        get_brothers(brother, brothers)


def get_little_brothers(student, brothers):
    for brother in student.get_little_brothers():
        if brother not in brothers:
            brothers.append(brother)

        get_little_brothers(brother, brothers)


@module.route("/brothers/<student_id>")
@login_required
def list_brother(student_id):
    students = []

    student = models.Student.objects(student_id=student_id).first()
    if student:
        students.append(student)
        brothers = []

        get_brothers(student, brothers)
        get_little_brothers(student, brothers)
        students.extend(brothers)

    return render_template(
        "/admin/students/list-brother.html",
        students=students,
    )
