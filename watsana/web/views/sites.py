from flask import Blueprint, render_template, redirect, url_for
import datetime

from watsana import models

module = Blueprint("sites", __name__)


@module.route("/")
def index():
    now = datetime.datetime.now()
    return render_template("/sites/index.html")
