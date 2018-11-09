"""
    首页路由
date: 18-11-8 下午8:24
"""
import logging
from flask import render_template
from . import index_blu


# 定义路由函数
@index_blu.route("/")
def index():
    """
        路由函数
    :return:
    """
    logging.debug("调试日志")
    return render_template("news/index.html")
