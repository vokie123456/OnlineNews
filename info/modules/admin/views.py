"""
    后台运维管理视图
date: 18-11-16 下午6:51
"""
import time
from datetime import datetime, timedelta

from flask import request, render_template, current_app, session, redirect, url_for, g, jsonify

from info import constants, RET, mysql_db
from info.models import User, News, Category
from info.utils.common import storage
from . import admin_blu


@admin_blu.route("/login", methods=["GET", "POST"])
def login():
    """
        后台运维管理登陆
    :return:
    """
    # 请求方式==GET
    if request.method == "GET":
        return render_template("admin/login.html")
    # 获取表单请求体
    data_dict = request.form
    # 获取用户名
    username = data_dict.get("username")
    # 获取密码
    password = data_dict.get("password")
    # 判断参数数据不为空
    if not all([username, password]):
        return render_template("admin/login.html", errmsg="参数不齐")
    try:
        # 根据用户名查询数据库
        user = User.query.filter(User.mobile == username).first()
    except Exception as e:
        current_app.logger.error(e)
        return render_template("admin/login.html", errmsg="数据库查询失败")
    # 判断用户是否存在
    if not user:
        return render_template("admin/login.html", errmsg="用户不存在")
    # 判断用户输入密码是否正确
    if not user.check_passowrd(password):
        return render_template("admin/login.html", errmsg="密码错误")
    # 判断用户是否管理员
    if not user.is_admin:
        return render_template("admin/login.html", errmsg="此用户不是管理员身份")
    # 保存用户ID
    session["admin_user_id"] = user.id
    # 重定向后台运维管理首页
    return redirect(url_for("admin.index"))


@admin_blu.route("/logout")
def logout():
    # 保存用户ID
    session.pop("admin_user_id", None)
    # 移除全局g对象中的user信息 -- 如果全局g对象有user属性
    g.user = False
    # 返回
    return render_template("admin/login.html", errmsg="退出成功")


@admin_blu.route("/")
def index():
    """
        后台运维管理首页
    :return:
    """
    # 获取登陆用户信息
    user = g.user
    # 封装返回数据
    data = {
        "user": user
    }
    return render_template("admin/index.html", data=data)


@admin_blu.route("/user_count")
def user_count():
    """
        用户统计
    :return:
    """
    # 总人数
    total_count = 0
    # 月新增总数
    mon_count = 0
    # 日新增总数
    day_count = 0
    # 当前时间
    now_time = time.localtime()
    """总人数/月新增总数/日新增总数"""
    try:
        # 获取当前数据库中非管理员的用户总数
        total_count = User.query.filter(User.is_admin == False).count()
    except Exception as e:
        current_app.logger.error(e)

    try:
        # 获取当前时间 yyyy-mm-01 格式日期
        mon_begin = "%d-%02d-01" % (now_time.tm_year, now_time.tm_mon)
        # 通过字符串, 格式化日期
        mon_begin_data = datetime.strptime(mon_begin, "%Y-%m-%d")
        # 获取当前数据库中 本月新增用户总数
        mon_count = User.query.filter(User.is_admin == False, User.create_time >= mon_begin_data).count()
    except Exception as e:
        current_app.logger.error(e)

    try:
        # 获取当前时间 yyyy-mm-dd 格式日期
        day_begin = '%d-%02d-%02d' % (now_time.tm_year, now_time.tm_mon, now_time.tm_mday)
        # 通过字符串, 格式化日期
        day_begin_date = datetime.strptime(day_begin, '%Y-%m-%d')
        # 获取当前数据库中 当天新增用户总数
        day_count = User.query.filter(User.is_admin == False, User.create_time > day_begin_date).count()
    except Exception as e:
        current_app.logger.error(e)
    """查询图表信息"""
    # 当天 00:00:00 时间
    now_date = datetime.strptime(datetime.now().strftime('%Y-%m-%d'), '%Y-%m-%d')
    # 近30天日期
    active_date = []
    # 近30天新增用户数
    active_count = []

    # 依次添加数据, 再反转
    # 循环31天
    for i in range(0, 31):
        # 新增用户总数
        count = 0
        # 开始时间 = 当前时间 - i天数 (i=1, 1天前)
        begin_date = now_date - timedelta(days=i)
        # 结束时间 = 当前时间 - i - 1 天数 (i=1, 0天前)
        end_date = now_date - timedelta(days=(i - 1))
        # 添加日期, 格式化开始时间
        active_date.append(begin_date.strftime('%Y-%m-%d'))
        try:
            # 获取数据库中 (非管理员, 创建时间 大于等于 开始时间, 创建时间 小于 结束时间)的用户总数
            # 即 -- 某天中, 新增用户数( 倒序获取 )
            count = User.query.filter(User.is_admin == False, User.create_time >= begin_date, User.create_time < end_date).count()
        except Exception as e:
            current_app.logger.error(e)
        # 添加新增用户总数
        active_count.append(count)
    # 翻转列表
    active_date.reverse()
    # 翻转列表
    active_count.reverse()
    # 封装返回数据
    data = {
        "total_count": total_count,
        "mon_count": mon_count,
        "day_count": day_count,
        "active_date": active_date,
        "active_count": active_count
    }

    return render_template('admin/user_count.html', data=data)


@admin_blu.route("/user_list")
def user_list():
    """
        用户列表
    :return:
    """
    # 封装返回用户列表
    user_list = []
    # 实体用户列表
    user_enitiy_list = []
    # 获取请求体 -- 页码
    page = request.args.get("page", 1)
    # 当前页码
    current_page = 1
    # 总页数
    total_page = 1

    try:
        # 转类型
        page = int(page)
    except Exception as e:
        current_app.logger.error(e)
        page = 1
    try:
        # 分页查询( 非管理员, 最后登陆倒序)
        paginate = User.query.filter(User.is_admin == False).order_by(User.last_login.desc()).paginate(page, constants.ADMIN_USER_PAGE_MAX_COUNT, False)
        # 当前页码查询数据
        user_enitiy_list = paginate.items
        # 当前页码
        current_page = paginate.page
        # 总页数
        total_page = paginate.pages
    except Exception as e:
        current_app.logger.error(e)
    # 循环实体用户列表
    for user in user_enitiy_list:
        # 封装
        user_list.append(user.to_dict())
    # 封装返回数据
    data = {
        "user_list": user_list,
        "current_page": current_page,
        "total_page": total_page
    }

    return render_template('admin/user_list.html', data=data)


@admin_blu.route("/news_review")
def news_review():
    """
        新闻审核页面和功能
    :return:
    """
    # 封装新闻审核列表
    news_review_list = []
    # 新闻审核实体列表
    news_review_entity_list = []
    # 页码 请求体
    page = request.args.get("page", 1)
    # 关键字
    keywords = request.args.get("keywords", "")
    # 当前页码
    current_page = 1
    # 总页数
    total_page = 1
    try:
        # 转类型
        page = int(page)
    except Exception as e:
        current_app.logger.error(e)
    try:
        # 查询条件
        filters = []
        # 如果有关键字
        if keywords:
            # 新闻标题包含关键字
            filters.append(News.title.contains(keywords))
        # 新闻 条件查询后, 分页查询(创建时间倒序)
        paginate = News.query.filter(*filters).order_by(News.create_time.desc()).paginate(page, constants.ADMIN_NEWS_PAGE_MAX_COUNT, False)
        # 获取当前页码查询数据
        news_review_entity_list = paginate.items
        # 当前页码
        current_page = paginate.page
        # 总页数
        total_page = paginate.pages
    except Exception as e:
        current_app.logger.error(e)
    # 循环新闻审核实体列表
    for news in news_review_entity_list:
        # 封装
        news_review_list.append(news.to_dict())
    # 封装返回数据
    data = {
        "news_review_list": news_review_list,
        "current_page": current_page,
        "total_page": total_page
    }
    # 返回
    return render_template("admin/news_review.html", data=data)


@admin_blu.route("/news_review_detail", methods=["GET", "POST"])
def news_review_detail():
    """
        新闻审核详情页面和功能
    :return:
    """
    if request.method == "GET":
        # 获取新闻id
        news_id = request.args.get("news_id")
        # 判断是否有新闻ID
        if not news_id:
            return render_template('admin/news_review_detail.html', data={"errmsg": "未查询到此新闻"})
        # 当前新闻详情
        news = None
        try:
            # 通过ID查询新闻
            news = News.query.get(news_id)
        except Exception as e:
            current_app.logger.error(e)
        # 判断是否有此新闻
        if not news:
            return render_template('admin/news_review_detail.html', data={"errmsg": "未查询到此新闻"})
        # 返回数据
        data = {"news": news.to_review_dict()}
        return render_template('admin/news_review_detail.html', data=data)
    # 新闻详情
    news = None
    # 获取请求体
    data_dict = request.json
    # 获取新闻ID
    news_id = data_dict.get("news_id")
    # 获取动作
    action = data_dict.get("action")
    # 判断是否所有参数都有数据
    if not all([news_id, action]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")
    # 判断动作参数是否规定数据
    if action not in ("accept", "reject"):
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")
    try:
        # 根据新闻ID查询数据
        news = News.query.get(news_id)
    except Exception as e:
        current_app.logger.error(e)
    # 判断是否获取到新闻数据
    if not news:
        return jsonify(errno=RET.NODATA, errmsg="未查询到数据")
    # 判断执行的动作 -- 通过审核
    if action == "accept":
        # 通过审核
        news.status = 0
    # 拒绝通过
    else:
        # 拒绝通过, 需要获取拒绝原因
        reason = data_dict.get("reason")
        # 判断
        if not reason:
            return jsonify(errno=RET.PARAMERR, errmsg="参数错误")
        # 设置数据
        news.reason = reason
        # 未通过
        news.status = -1
    # 保存数据库
    try:
        mysql_db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        mysql_db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg="数据保存失败")
    # 返回
    return jsonify(errno=RET.OK, errmsg="操作成功")


@admin_blu.route("/news_edit")
def news_edit():
    """
        新闻板式列表页面
    :return:
    """
    # 封装新闻板式编辑列表
    news_edit_list = []
    # 新闻板式编辑实体列表
    news_edit_entity_list = []
    # 页码 请求体
    page = request.args.get("page", 1)
    # 关键字
    keywords = request.args.get("keywords", "")
    # 当前页码
    current_page = 1
    # 总页数
    total_page = 1
    try:
        # 转类型
        page = int(page)
    except Exception as e:
        current_app.logger.error(e)
    try:
        # 查询条件
        filters = []
        # 如果有关键字
        if keywords:
            # 新闻标题包含关键字
            filters.append(News.title.contains(keywords))
        # 新闻 条件查询后, 分页查询(创建时间倒序)
        paginate = News.query.filter(*filters).order_by(News.create_time.desc()).paginate(page, constants.ADMIN_NEWS_PAGE_MAX_COUNT, False)
        # 获取当前页码查询数据
        news_edit_entity_list = paginate.items
        # 当前页码
        current_page = paginate.page
        # 总页数
        total_page = paginate.pages
    except Exception as e:
        current_app.logger.error(e)
    # 循环新闻板式编辑实体列表
    for news in news_edit_entity_list:
        # 封装
        news_edit_list.append(news.to_dict())
    # 封装返回数据
    data = {
        "news_edit_list": news_edit_list,
        "current_page": current_page,
        "total_page": total_page
    }
    # 返回
    return render_template("admin/news_edit.html", data=data)


@admin_blu.route("/news_edit_detail", methods=["GET", "POST"])
def news_edit_detail():
    """
        新闻板式编辑页面和功能
    :return:
    """
    if request.method == "GET":
        # 获取新闻id
        news_id = request.args.get("news_id")
        # 判断是否有新闻ID
        if not news_id:
            return render_template('admin/news_edit_detail.html', data={"errmsg": "未查询到此新闻"})
        # 当前新闻详情
        news = None
        try:
            # 通过ID查询新闻
            news = News.query.get(news_id)
        except Exception as e:
            current_app.logger.error(e)
        # 判断是否有此新闻
        if not news:
            return render_template('admin/news_edit_detail.html', data={"errmsg": "未查询到此新闻"})
        # 获取新闻分类全部数据 -- 实体
        categories = Category.query.all()
        # 封装返回新闻分类数据
        categories_list = []
        # 循环新闻分类实体
        for category in categories:
            # 转为字典
            c_dict = category.to_dict()
            # 默认不是选中
            c_dict["is_selected"] = False
            # 判断当前分类ID 和 新闻详情中分类ID一致
            if category.id == news.category_id:
                # 设置为选中
                c_dict["is_selected"] = True
            # 封装
            categories_list.append(c_dict)
        # 移除最新分类
        categories_list.pop(0)
        # 返回数据
        data = {"news": news.to_dict(), "categories": categories_list}
        # 返回
        return render_template('admin/news_edit_detail.html', data=data)
    # 新闻实体
    news = None
    # 请求体
    data_dict = request.form
    # 新闻ID
    news_id = data_dict.get("news_id")
    # 新闻标题
    title = data_dict.get("title")
    # 新闻摘要
    digest = data_dict.get("digest")
    # 新闻内容
    content = data_dict.get("content")
    # 新闻上传图片
    index_image = request.files.get("index_image")
    # 新闻分类
    category_id = data_dict.get("category_id")
    # 判断参数是否都有数据
    if not all([title, digest, content, category_id]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数有误")
    try:
        # 根据新闻ID获取新闻详情
        news = News.query.get(news_id)
    except Exception as e:
        current_app.logger.error(e)
    # 判断是否有此新闻
    if not news:
        return jsonify(errno=RET.NODATA, errmsg="未查询到新闻数据")
    # 判断是否有上传图片
    if index_image:
        try:
            # 读取二进制文件
            index_image = index_image.read()
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.PARAMERR, errmsg="参数有误")
        try:
            # 将上传图片上传至七牛云
            url = storage(index_image)
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.THIRDERR, errmsg="上传图片错误")
        # 拼接上传图片路径
        news.index_image_url = constants.QINIU_DOMIN_PREFIX + url
    # 设置新闻相关信息
    news.title = title
    news.digest = digest
    news.content = content
    news.category_id = category_id
    try:
        # 事务提交
        mysql_db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        mysql_db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg="保存数据失败")
    # 返回
    return jsonify(errno=RET.OK, errmsg="操作成功")


@admin_blu.route("/news_type")
def news_type():
    """
        新闻分类列表
    :return:
    """
    # 查询所有新闻分类数据 -- 实体
    categories = Category.query.all()
    # 封装
    categories_dicts = []
    # 循环实体
    for category in categories:
        # 封装数据
        categories_dicts.append(category.to_dict())
    # 移除最新分类
    categories_dicts.pop(0)
    # 返回内容
    return render_template('admin/news_type.html', data={"categories": categories_dicts})


@admin_blu.route("/add_category", methods=["POST"])
def add_category():
    """
        新闻分类页面和功能
    :return:
    """
    # 请求体
    data_dict = request.json
    # 分类ID
    category_id = data_dict.get("id")
    # 分类名称
    category_name = data_dict.get("name")
    # 判断分类名称是否有数据
    if not category_name:
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")
    # 判断分类ID是否有数据
    if category_id:
        try:
            # 判断数据库中是否有此分类ID
            category = Category.query.get(category_id)
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.DBERR, errmsg="查询数据失败")
        # 如果没有此分类数据
        if not category:
            return jsonify(errno=RET.NODATA, errmsg="未查询到分类信息")
        # 修改分类名称
        category.name = category_name
    else:
        # 如果没有分类id，则是添加分类
        category = Category()
        # 保存分类名称
        category.name = category_name
        # 新增数据
        mysql_db.session.add(category)
    try:
        # 事务提交
        mysql_db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        mysql_db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg="保存数据失败")
    # 返回
    return jsonify(errno=RET.OK, errmsg="保存数据成功")
