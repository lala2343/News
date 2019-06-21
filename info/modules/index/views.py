from flask import current_app, jsonify
from flask import g
from flask import render_template
from flask import request

from info import constants
from info.models import User, News, Category
from info.utils.common import user_login_data
from info.utils.response_code import RET
from . import index_blu


@index_blu.route("/")
@user_login_data
def index():
    """
    判断用户是否已经登陆过，若登陆过则将用户的信息直接传至模板
    :return:
    """
    user = g.user
    # user = None
    # user_id = session.get("user_id")
    # if user_id:
    #     try:
    #         user = User.query.get(user_id)
    #     except Exception as e:
    #         current_app.logger.error(e)

    news_list = []
    news_dict_li = []
    try:
        news_list = News.query.order_by(News.clicks.desc()).limit(constants.CLICK_RANK_MAX_NEWS)
    except Exception as e:
        current_app.logger.error(e)

    for news in news_list:
        news_dict_li.append(news.to_basic_dict())

    categories = Category.query.all()
    category_li = []
    for category in categories:
        category_li.append(category.to_dict())

    data = {
        "user": user.to_dict() if user else None,
        "news_dict_li": news_dict_li,
        "category_li": category_li
    }
    return render_template("news/index.html", data=data)


@index_blu.route('/favicon.ico')
def favicon():
    return current_app.send_static_file("news/favicon.ico")


@index_blu.route("/news_list")
def news_list():
    # 获取参数
    cid = request.args.get("cid", "1")
    page = request.args.get("page", "1")
    per_page = request.args.get("per_page", "10")

    # 校验参数
    try:
        cid = int(cid)
        page = int(page)
        per_page = int(per_page)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    # 查询数据
    filters = [News.status == 0]
    if cid != 1:
        filters.append(News.category_id == cid)

    try:
        paginate = News.query.filter(*filters).order_by(News.create_time.desc()).paginate(page, per_page, False)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="数据查询错误")

    news_li = paginate.items
    total_page = paginate.pages
    current_page = paginate.page
    news_dict_li = []
    for news in news_li:
        news_dict_li.append(news.to_basic_dict())

    data = {
        "total_page": total_page,
        "current_page": current_page,
        "news_dict_li": news_dict_li,
    }

    return jsonify(errno=RET.OK, errmsg="OK", data=data)
