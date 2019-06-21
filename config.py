import logging
from redis import StrictRedis


class Config(object):
    """项目的配置"""
    # DEBUG = True
    # 为mysql添加配置
    SQLALCHEMY_DATABASE_URI = "mysql://root:mysql@127.0.0.1:3306/flask_news"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # SQLALCHEMY在teardown中默认提交
    SQLALCHEMY_COMMIT_ON_TEARDOWN = True

    # 为redis添加配置
    REDIS_HOST = "127.0.0.1"
    REDIS_PORT = 6379

    # 为Session添加配置
    # 设置session储存格式为redis
    SECRET_KEY = "hZFMKpXT/jc3XCHQJXUDNzAfXAXJKvztitzNZqBfw1XwYP6VoHHlqCoyccDZqQcG"
    # 设置session存储位置
    SESSION_TYPE = "redis"
    # 指定session的存储的redis
    SESSION_REDIS = StrictRedis(host=REDIS_HOST, port=REDIS_PORT)
    # 开启session签名
    SESSION_USE_SIGNER = True
    # 开启session过期时间
    SESSION_PERMANENT = False
    # 设置session过期时间为2天
    PERMANENT_SESSION_LIFETIME = 86400 * 2

    # 设置日志等级
    LOG_LEVEL = logging.DEBUG


class DevelopmentConfig(Config):
    """开发环境下的配置"""
    DEBUG = True


class ProductionConfig(Config):
    """生产环境下的配置"""
    DEBUG = False
    LOG_LEVEL = logging.WARNING


class TestingConfig(Config):
    """测试环境下的配置"""
    DEBUG = True
    TESTING = True


config = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig
}
