from flask import Blueprint, render_template, redirect, url_for, request
from flask_login import current_user, login_required

from watsana import models
from watsana.web import acl, forms

import datetime

module = Blueprint("users", __name__, url_prefix="/users")


@module.route("/")
@acl.roles_required("admin")
def index():
    users = models.User.objects.all().order_by("-username")
    return render_template("/admin/users/index.html", users=users)


@module.route("/<user_id>", methods=["GET", "POST"])
@acl.roles_required("admin")
def view(user_id):
    user = models.User.objects.get(id=user_id)
    form = forms.accounts.AdminForm(
        obj=user,
    )
    if not form.validate_on_submit():
        return render_template("/admin/users/view.html", form=form, user=user)

    form.populate_obj(user)

    user.updated_date = datetime.datetime.now()
    user.save()

    return redirect(url_for("admin.users.view", user_id=user.id))
