from flask import abort, jsonify
from flask import current_app
from flask import g
from flask import render_template
from flask import request

from info import constants, db
from info.models import News, Comment, CommentLike, User
from info.modules.news import news_blu
from info.utils.common import user_login_data
from info.utils.response_code import RET


@news_blu.route("/<int:news_id>")
@user_login_data
def news_detail(news_id):
    """
    :param news_id:
    :return:
    """
    user = g.user

    # 右侧新闻点击数排序的查询
    news_list = []
    news_dict_li = []
    try:
        news_list = News.query.order_by(News.clicks.desc()).limit(constants.CLICK_RANK_MAX_NEWS)
    except Exception as e:
        current_app.logger.error(e)

    for news in news_list:
        news_dict_li.append(news.to_basic_dict())

    news = None
    try:
        news = News.query.get(news_id)
    except Exception as e:
        current_app.logger.error(e)

    if not news:
        abort(404)

    news.clicks += 1

    # 是否收藏
    is_collected = False
    if user:
        if news in user.collection_news:
            is_collected = True

    # 查询评论数据
    comments = []
    try:
        comments = Comment.query.filter(Comment.news_id == news_id).order_by(Comment.create_time.desc()).all()
    except Exception as e:
        current_app.logger.error(e)

    comment_liked_ids = []
    if user:
        try:
            comment_ids = [comment.id for comment in comments]
            comment_likes = CommentLike.query.filter(CommentLike.comment_id.in_(comment_ids),
                                                     CommentLike.user_id == user.id).all()
            comment_liked_ids = [com_like.comment_id for com_like in comment_likes]
        except Exception as e:
            current_app.logger.error(e)

    comment_dict_li = []
    for comment in comments:
        comment_dict = comment.to_dict()
        comment_dict["is_like"] = False
        if comment.id in comment_liked_ids:
            comment_dict["is_like"] = True
        comment_dict_li.append(comment_dict)

    is_followed = False
    if news.user and user:
        if news.user in user.followed:
            is_followed = True

    data = {
        "user": user.to_dict() if user else None,
        "news_dict_li": news_dict_li,
        "news": news.to_dict(),
        "is_collected": is_collected,
        "comments": comment_dict_li,
        "is_followed": is_followed
    }
    return render_template("news/detail.html", data=data)


@news_blu.route("/news_collect", methods=["POST"])
@user_login_data
def news_collect():
    # 取参数
    user = g.user
    if not user:
        return jsonify(errno=RET.SESSIONERR, errmsg="用户未登陆")

    param_dict = request.json
    news_id = param_dict.get("news_id")
    action = param_dict.get("action")

    # 校验参数
    if not all([news_id, action]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    if action not in ["collect", "cancel_collect"]:
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    try:
        news_id = int(news_id)
    except Exception as e:
        current_app.logger.error(e)

    # 查询新闻数据,并判断是否存在
    try:
        news = News.query.get(news_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="数据查询错误")

    if not news:
        return jsonify(errno=RET.NODATA, errmsg="未查询到新闻数据")

    if action == "collect":
        # 收藏
        if news not in user.collection_news:
            user.collection_news.append(news)
    else:
        # 取消收藏
        if news in user.collection_news:
            user.collection_news.remove(news)

    return jsonify(errno=RET.OK, errmsg="操作成功")


@news_blu.route("/comment_like", methods=["POST"])
@user_login_data
def comment_like():
    user = g.user
    if not user:
        return jsonify(errno=RET.SESSIONERR, errmsg="用户未登陆")

    params_dict = request.json
    comment_id = params_dict.get("comment_id")
    # news_id = params_dict.get("news_id")
    action = params_dict.get("action")

    if not all([comment_id, action]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    if action not in ["add", "remove"]:
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    try:
        comment_id = int(comment_id)
        # news_id = int(news_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    try:
        comment = Comment.query.get(comment_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="数据查询错误")

    if not comment:
        return jsonify(errno=RET.NODATA, errmsg="评论不存在")

    if action == "add":
        com_like = CommentLike.query.filter(CommentLike.comment_id == comment_id,
                                            CommentLike.user_id == user.id).first()
        if not com_like:
            com_like = CommentLike()
            com_like.user_id = user.id
            com_like.comment_id = comment_id
            comment.like_count += 1
            db.session.add(com_like)
    else:
        com_like = CommentLike.query.filter(CommentLike.comment_id == comment_id,
                                            CommentLike.user_id == user.id).first()
        if com_like:
            db.session.delete(com_like)
            comment.like_count -= 1
    # try:
    #     db.session.commit()
    # except Exception as e:
    #     db.session.rollback()
    #     current_app.logger.error(e)
    #     return jsonify(errno=RET.DBERR, errmsg="数据库操作失败")

    return jsonify(errno=RET.OK, errmsg="操作成功")


@news_blu.route("/news_comment", methods=["POST"])
@user_login_data
def news_comment():
    user = g.user
    if not user:
        return jsonify(errno=RET.SESSIONERR, errmsg="用户未登陆")

    # 获取参数
    params_dict = request.json
    news_id = params_dict.get("news_id")
    comment_content = params_dict.get("comment")
    parent_id = params_dict.get("parent_id")

    if not all([news_id, comment_content]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    # 校验参数
    try:
        news_id = int(news_id)
        if parent_id:
            parent_id = int(parent_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    # 查询新闻数据,并判断是否存在
    try:
        news = News.query.get(news_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="数据查询错误")

    if not news:
        return jsonify(errno=RET.NODATA, errmsg="未查询到新闻数据")

    # 初始化评论模型
    comment = Comment()
    comment.user_id = user.id
    comment.news_id = news_id
    comment.content = comment_content
    if parent_id:
        comment.parent_id = parent_id

    try:
        db.session.add(comment)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="保存评论到数据库失败")

    return jsonify(errno=RET.OK, errmsg="OK", data=comment.to_dict())


@news_blu.route("/followed_user", methods=["POST"])
@user_login_data
def followed_user():
    user = g.user
    if not user:
        return jsonify(errno=RET.SESSIONERR, errmsg="未登陆")
    param = request.json
    user_id = param.get("user_id")
    action = param.get("action")

    if not all([user_id, action]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    if action not in ["follow", "unfollow"]:
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    try:
        other = User.query.get(user_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="数据查询错误")

    if not other:
        return jsonify(errno=RET.NODATA, errmsg="未查询到数据")

    if action == "follow":
        if other not in user.followed:
            user.followed.append(other)
            # other.followers.append(user)
        else:
            return jsonify(errno=RET.DATAEXIST, errmsg="已被关注")
    else:
        if other in user.followed:
            user.followed.remove(other)
        else:
            return jsonify(errno=RET.DATAEXIST, errmsg="未被关注")

    return jsonify(errno=RET.OK, errmsg="OK")
