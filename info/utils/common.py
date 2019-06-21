# 自定义工具类
import functools

from flask import current_app
from flask import g
from flask import session

from info.models import User


def do_index_class(index):
    if index == 1:
        return "first"
    elif index == 2:
        return "second"
    elif index == 3:
        return "third"
    else:
        return ""


def user_login_data(func):
    @functools.wraps(func)
    def wapper(*args, **kwargs):
        user = None
        user_id = session.get("user_id")
        if user_id:
            try:
                user = User.query.get(user_id)
            except Exception as e:
                current_app.logger.error(e)
        g.user = user
        return func(*args, **kwargs)

    return wapper

