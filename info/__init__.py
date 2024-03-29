import logging
from logging.handlers import RotatingFileHandler
from flask import Flask
from flask import g
from flask import render_template
from flask.ext.session import Session
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.wtf import CSRFProtect
from flask.ext.wtf.csrf import generate_csrf
from redis import StrictRedis

from config import config

# 初始化mysql
db = SQLAlchemy()
redis_sr = None  # type: StrictRedis


def setup_logging(config_name):
    # 设置日志的记录等级
    logging.basicConfig(level=config[config_name].LOG_LEVEL)  # 调试debug级
    # 创建日志记录器，指明日志保存的路径、每个日志文件的最大大小、保存的日志文件个数上限
    file_log_handler = RotatingFileHandler("logs/log", maxBytes=1024 * 1024 * 100, backupCount=10)
    # 创建日志记录的格式 日志等级 输入日志信息的文件名 行数 日志信息
    formatter = logging.Formatter('%(levelname)s %(filename)s:%(lineno)d %(message)s')
    # 为刚创建的日志记录器设置日志记录格式
    file_log_handler.setFormatter(formatter)
    # 为全局的日志工具对象（flask app使用的）添加日志记录器
    logging.getLogger().addHandler(file_log_handler)


def create_app(config_name):
    # 配置日志
    setup_logging(config_name)
    # 创建Flask对象
    app = Flask(__name__)
    # 加载项目配置
    app.config.from_object(config[config_name])
    # 通过app初始化
    db.init_app(app)
    # 初始化redis
    global redis_sr
    redis_sr = StrictRedis(host=config[config_name].REDIS_HOST, port=config[config_name].REDIS_PORT,
                           decode_responses=True)
    # 开启CSRF保护
    CSRFProtect(app)
    # 初始化session
    Session(app)

    from info.utils.common import do_index_class
    app.add_template_filter(do_index_class, "index_class")

    from info.utils.common import user_login_data

    @app.errorhandler(404)
    @user_login_data
    def page_not_found(err):
        user = g.user
        data = {"user": user.to_dict() if user else None}
        return render_template("news/404.html", data=data)

    @app.after_request
    def after_request(response):
        # 生成csrf_token并存储到cookie中
        csrf_token = generate_csrf()
        response.set_cookie("csrf_token", csrf_token)

        return response

    from info.modules.index import index_blu
    app.register_blueprint(index_blu)

    from info.modules.passport import passport_blu
    app.register_blueprint(passport_blu)

    from info.modules.news import news_blu
    app.register_blueprint(news_blu)

    from info.modules.profile import profile_blu
    app.register_blueprint(profile_blu)

    from info.modules.admin import admin_blu
    app.register_blueprint(admin_blu)
    return app
