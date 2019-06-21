from flask import Blueprint
from flask import redirect
from flask import request
from flask import session
from flask import url_for

admin_blu = Blueprint("admin", __name__, url_prefix="/admin")

from . import views


@admin_blu.before_request
def check_admin():
    is_admin = session.get("is_admin", False)
    if not is_admin and not request.url.endswith(url_for("admin.login")):
        return redirect("/")
