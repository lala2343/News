import random
import re
from datetime import datetime

from flask import abort, jsonify
from flask import current_app
from flask import make_response
from flask import request
from flask import session

from info import constants, db
from info import redis_sr
from info.libs.yuntongxun.sms import CCP
from info.models import User
from info.utils.response_code import RET
from . import passport_blu
from info.utils.captcha.captcha import captcha


@passport_blu.route("/image_code")
def get_image_code():
    # 先取到Url中的参数
    image_code_id = request.args.get("imageCodeId", None)
    # 判空
    if not image_code_id:
        return abort(403)
    # 生成图片验证码
    name, text, image = captcha.generate_captcha()
    print(text)
    # 保存数据到redis中
    try:
        redis_sr.set("ImageCodeId_" + image_code_id, text, ex=constants.IMAGE_CODE_REDIS_EXPIRES)
    except Exception as e:
        current_app.logger.error(e)
        abort(500)

    response = make_response(image)
    response.headers["Content-Type"] = "image/jpg"
    return response


@passport_blu.route("/sms_code", methods=["POST"])
def send_sms_code():
    """
    1、参数：手机号，图片验证码内容，图片验证码编号，
    2、校验参数
    3、校验用户传递信息
        校验失败 返回验证码输入错误
        校验成功　生成短信验证码　发送短信　告知发送结果
    :return:
    """
    # print(request)
    # print(request.data)
    # print(request.json)
    # param_dict = json.loads(request.data)

    # 获取参数
    param_dict = request.json
    mobile = param_dict.get("mobile")
    image_code = param_dict.get("image_code")
    image_code_id = param_dict.get("image_code_id")

    # 校验参数(参数是否存在.参数是否合法,参数是否过期,参数是否正确)
    if not all([mobile, image_code, image_code_id]):
        return jsonify(errno=RET.PARAMERR, msg="参数有误")
    if not re.match(r"1[35-9]\d{9}", mobile):
        return jsonify(errno=RET.PARAMERR, msg="手机号输入有误")
    try:
        real_image_code = redis_sr.get("ImageCodeId_" + image_code_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, msg="数据查询失败")
    if not real_image_code:
        return jsonify(errno=RET.NODATA, msg="图片验证码已过期")
    if real_image_code.upper() != image_code.upper():
        return jsonify(errno=RET.DATAERR, msg="验证码输入错误")

    # 若参数校验通过,生成随机验证码发送短信并且保存至redis数据库(5分钟)
    sms_code_str = "%06d" % random.randint(0, 999999)
    current_app.logger.debug("验证码:%s" % sms_code_str)

    # result = CCP().send_template_sms(mobile, [sms_code_str, constants.SMS_CODE_REDIS_EXPIRES / 60], 1)
    # if result != 0:
    #     return jsonify(errno=RET.THIRDERR, msg="发送短信失败")

    try:
        redis_sr.set("SMS_CODE_" + mobile, sms_code_str, ex=constants.SMS_CODE_REDIS_EXPIRES)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, msg="数据保存失败")

    # 返回成功数据
    return jsonify(errno=RET.OK, msg="发送成功")


@passport_blu.route("/register", methods=["POST"])
def register():
    param_dict = request.json
    mobile = param_dict.get("mobile")
    sms_code = param_dict.get("sms_code")
    password = param_dict.get("password")

    if not all([mobile, sms_code, password]):
        return jsonify(errno=RET.PARAMERR, msg="参数有误")

    if not re.match(r"1[35-9]\d{9}", mobile):
        return jsonify(errno=RET.PARAMERR, msg="手机号输入有误")

    try:
        real_sms_code = redis_sr.get("SMS_CODE_" + mobile)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, msg="数据查询失败")

    if not real_sms_code:
        return jsonify(errno=RET.NODATA, msg="手机验证码已过期")

    if real_sms_code != sms_code:
        return jsonify(errno=RET.DATAERR, msg="验证码输入错误")

    # 验证成功之后的逻辑
    user = User()
    user.mobile = mobile
    user.nick_name = mobile
    user.password = password

    user.last_login = datetime.now()

    try:
        db.session.add(user)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()

    # 注册成功后添加session代表默认登陆
    session["user_id"] = user.id
    session["user_mobile"] = user.mobile
    session["user_nick_name"] = user.nick_name

    return jsonify(errno=RET.OK, msg="注册成功")


@passport_blu.route("/login", methods=["POST"])
def login():
    params_dict = request.json
    mobile = params_dict.get("mobile")
    password = params_dict.get("password")

    if not all([mobile, password]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    if not (re.match(r"1[35-9]\d{9}", mobile) or mobile == "admin"):
        return jsonify(errno=RET.PARAMERR, errmsg="手机号输入有误")

    try:
        user = User.query.filter(User.mobile == mobile).first()
    except Exception as e:
        current_app.logger.debug(e)
        return jsonify(errno=RET.DBERR, errmsg="数据查询错误")
    if not user:
        return jsonify(errno=RET.NODATA, errmsg="用户不存在")

    if not user.check_passowrd(password):
        return jsonify(errno=RET.PWDERR, errmsg="用户名或密码错误")

    # 校验用户名密码成功后,使用session保存用户的登陆状态
    session["user_id"] = user.id
    session["user_mobile"] = user.mobile
    session["user_nick_name"] = user.nick_name

    user.last_login = datetime.now()
    # 会在teardown请求钩子中默认提交，不需要写代码
    # db.session.commit()

    return jsonify(errno=RET.OK, errmsg="登陆成功")


@passport_blu.route("/logout")
def logout():
    session.pop("user_id", None)
    session.pop("mobile", None)
    session.pop("nick_name", None)
    session.pop("is_admin", None)
    return jsonify(errno=RET.OK, errmsg="退出成功")
