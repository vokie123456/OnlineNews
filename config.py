"""
    Flask框架的配置信息类文件
date: 18-11-7 下午7:55
"""
import base64
import os
from redis import StrictRedis

class Config(object):
    """
        配置信息
    """

    # mysql数据库连接配置
    # SQLALCHEMY_DATABASE_URI = '数据库类型://账号:密码@数据库IP:数据库端口/数据库名称'
    SQLALCHEMY_DATABASE_URI = 'mysql://root:123456@127.0.0.1:3306/informations'
    # 是否追踪对象的修改并且发送信号
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # redis数据库连接配置
    # 数据库地址
    REDIS_HOST = "127.0.0.1"
    # 数据库密码
    REDIS_PASSWORD = "123456"
    # 数据库端口
    REDIS_PORT = 6379
    # Redis默认选择数据库
    REDIS_DATA_DB = 0
    # Redis 1号数据库 -- session存放数据库
    REDIS_SESSION_DB = 14

    # 设置密钥通过 base64.b64encode(os.urandom(48)) 来生成一个指定长度的随机字符串
    # SECRET_KEY = "tOoJdhcvgkaC+tirWXkw9yzdSyDhnG9gc4DbouU9xgdgs8fbIdWYHsc9dwVAIxri"
    SECRET_KEY = base64.b64encode(os.urandom(48)).decode()

    # flask_session 的配置信息
    # 指定 session 保存到 Redis数据库 中
    SESSION_TYPE = "redis"
    # session是否开启加密签名处理
    SESSION_USE_SIGNER = True
    # 设置Redis数据库实例 ( 数据库地址, 数据库端口, 指定数据库 )
    SESSION_REDIS = StrictRedis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_SESSION_DB)
    # session有效时间 86400秒 -- 24小时
    PERMANENT_SESSION_LIFETIME = 86400


class DevelopementConfig(Config):
    """
        开发模式下的配置 -- 用于开发环境的配置信息, 继承配置类
    """
    # 调试模式
    DEBUG = True


class ProductionConfig(Config):
    """
        生产模式下的配置 -- 用于项目上线后运行的配置信息, 继承配置类
    """
    pass

# 定义配置字典 -- 方便使用不同环境的配置信息
config = {
    "development": DevelopementConfig,
    "production": ProductionConfig
}
