#!/usr/bin/env python
# -*- coding:utf-8 -*-
from django.shortcuts import render, redirect, HttpResponse, render_to_response
from web import models
from web.utils.md5 import md5_has
from rbac.service.init_permission import init_permission


def login(request):
    if request.method == 'GET':
        return render(request, 'login.html')

    user = request.POST.get('username')
    pwd = md5_has(request.POST.get('password', ''))

    user_object = models.UserInfo.objects.filter(name=user, password=pwd).first()
    if not user_object:
        return render(request, 'login.html', {'error': '用户名或密码错误'})
    #  获取登录信息存放至session
    request.session["user_info"] = {"user_id": user_object.id, "nickname": user_object.nickname}

    # 用户权限信息的初始化
    init_permission(user_object, request)

    return redirect('/index/')


# def get_ValidCode_img(request):
#     with open("abc.png", "rb") as f:
#         date = f.read()
#     return HttpResponse(date)

def logout(request):
    """
    注销
    :param request:
    :return:
    """
    request.session.delete()
    return redirect('/login/')


def index(request):
    """
    首页
    :param request:
    :return:
    """
    return render(request, 'index.html')
