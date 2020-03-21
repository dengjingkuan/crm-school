#!/usr/bin/env python 
# -*- coding: utf-8 -*- 
# Author : kuan
# Software : PyCharm
from django.conf.urls import url
from mystark.service.v1 import StarkHandler, StarkModelForm
from web import models
from .base import PermissionHandler


class ScoreRecordModelForm(StarkModelForm):
    class Meta:
        model = models.ScoreRecord
        exclude = ['student', 'user']


class ScoreRecordHandler(PermissionHandler, StarkHandler):
    list_display = ['student', 'content', 'score', 'user']
    model_form_class = ScoreRecordModelForm

    def get_urls(self):
        """
        为子类的ConsultRecordHandler重写此方法.
        :return:
        """
        patterns = [
            url(r'^list/(?P<student_id>\d+)/$', self.wrapper(self.changelist_view), name=self.get_list_url_name),
            url(r'^add/(?P<student_id>\d+)/$', self.wrapper(self.add_view), name=self.get_add_url_name),
        ]
        patterns.extend(self.extra_url())
        return patterns

    def get_list_display(self, request, *args, **kwargs):
        """
        获取页面上应该显示的列，预留的自定义扩展，例如：以后根据用户的不同显示不同的列
        :return:
        """
        value = []
        if self.list_display:
            value.extend(self.list_display)
        return value

    def get_queryset(self, request, *args, **kwargs):
        student_id = kwargs.get('student_id')
        return self.model_class.objects.filter(student_id=student_id)

    def save(self, request, form, is_update, *args, **kwargs):
        student_id = kwargs.get('student_id')
        current_user_id = request.session ["user_info"] ["user_id"]

        # 对ScoreRecord进行数据保存
        form.instance.student_id = student_id
        form.instance.user_id = current_user_id
        form.save()

        # 对score进行计算
        score = form.instance.score  # 表单提交的分值
        if score > 0:
            form.instance.student.score += abs(score)  # 数据库原来的分值
        else:
            form.instance.student.score -= abs(score)
        form.instance.student.save()


