from flask import Blueprint, render_template, redirect

from watsana import models
from watsana.web import acl


module = Blueprint("admin", __name__, url_prefix="/admin")


@module.route("/")
@acl.roles_required("admin")
def index():
    return render_template(
        "/admin/index.html",
    )
