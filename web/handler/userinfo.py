#!/usr/bin/env python 
# -*- coding: utf-8 -*- 
# Author : kuan
# Software : PyCharm
from django import forms
from django.core.exceptions import ValidationError
from django.utils.safestring import mark_safe
from django.shortcuts import render, HttpResponse, redirect
from django.conf.urls import url
from mystark.service.v1 import site, StarkHandler, StarkModelForm, StarkForm, get_choice_text, SearchOption
from web import models
from web.utils.md5 import md5_has
from .base import PermissionHandler


#  通过自定义model_form 可以重新定制显示的字段
class UserInfoAddModelForm(StarkModelForm):
    confirm_password = forms.CharField(label='确认密码', max_length=32)

    class Meta:
        model = models.UserInfo
        fields = ['name', 'nickname', 'password', 'confirm_password', 'gender', 'phone', 'email', 'depart', 'roles']

    def clean_confirm_password(self):
        password = self.cleaned_data['password']
        confirm_password = self.cleaned_data['confirm_password']
        if password != confirm_password:
            raise ValidationError("两次密码不一致.")
        return confirm_password

    def clean(self):
        password = self.cleaned_data['password']
        self.cleaned_data['password'] = md5_has(password)
        return self.cleaned_data


class UserInfoChangeModelForm(StarkModelForm):

    class Meta:
        model = models.UserInfo
        fields = ['name', 'nickname', 'gender', 'phone', 'email', 'depart', 'roles']


class ResetPasswordForm(StarkForm):
    password = forms.CharField(label="密码", max_length=32, widget=forms.PasswordInput)
    confirm_password = forms.CharField(label="确认密码", max_length=32, widget=forms.PasswordInput)

    def clean_confirm_password(self):
        password = self.cleaned_data.get('password')
        confirm_password = self.cleaned_data.get('confirm_password')
        print(password, confirm_password)
        if confirm_password != password:
            raise ValidationError('两次密码不一致')
        return password

    def clean(self):
        password = self.cleaned_data.get('password')
        if password:
            self.cleaned_data['password'] = md5_has(password)
            return self.cleaned_data


class UserInfoHandler(PermissionHandler, StarkHandler):

    def display_reset_password(self, obj=None, is_header=None, *args, **kwargs):
        if is_header:
            return "重置密码"
        return mark_safe("<a href='%s'>重置密码</a>" % self.get_reverse_reset_password_url(pk=obj.pk))

    list_display = ['nickname', get_choice_text('性别', 'gender'), 'phone', 'email', 'depart', display_reset_password]
    order_list = ['-id']
    search_list = ['nickname__contains', 'name__contains']
    search_group = [
        SearchOption('gender'),
        SearchOption('depart', is_multi=True),
    ]

    def get_model_form_class(self, is_add, request, pk, *args, **kwargs):
        if is_add:
            return UserInfoAddModelForm
        return UserInfoChangeModelForm

    def reset_password_view(self, request, pk):
        """
        重置密码的视图函数
        :param request:
        :param pk:
        :return:
        """
        userinfo_object = models.UserInfo.objects.filter(id=pk).first()
        if not userinfo_object:
            return HttpResponse("用户不存在, 重置密码失败。")
        if request.method == 'GET':
            form = ResetPasswordForm()
            return render(request, 'stark/change.html', {'form': form})
        form = ResetPasswordForm(data=request.POST)  # 获取数据
        if form.is_valid():
            userinfo_object.password = form.cleaned_data['password']
            userinfo_object.save()
            return redirect(self.get_reverse_list_url())
        return render(request, 'stark/change.html', {'form': form})

    @property
    def get_reset_password_url_name(self):
        return self.get_url_name('reset_password')

    def get_reverse_reset_password_url(self, *args, **kwargs):
        """
        快速生成修改按钮的URL
        :return:
        """
        return self.get_reverse_commons_url(self.get_reset_password_url_name, *args, **kwargs)

    def extra_url(self):
        patterns = [
            url(r'^reset/password/(?P<pk>\d+)/$', self.wrapper(self.reset_password_view),
                name=self.get_reset_password_url_name),
        ]
        return patterns