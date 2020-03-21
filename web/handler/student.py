#!/usr/bin/env python 
# -*- coding: utf-8 -*- 
# Author : kuan
# Software : PyCharm
from django.conf.urls import url
from django.urls import reverse
from django.utils.safestring import mark_safe
from mystark.service.v1 import StarkHandler, get_choice_text, get_many2many_text, SearchOption
from .base import PermissionHandler


class StudentHandler(PermissionHandler, StarkHandler):
    def display_score(self, obj=None, is_header=None, *args, **kwargs):
        if is_header:
            return "分值"
        record_url = reverse('stark:web_scorerecord_list', kwargs={'student_id': obj.pk})
        return mark_safe('<a target="_blank" href="%s">%s</a>' % (record_url, obj.score))

    has_add_btn = False
    list_display = ['customer', 'qq', 'mobile', 'emergency_contract', get_many2many_text('已报班级', 'class_list'),
                    display_score, get_choice_text('学员状态', 'student_status')]
    search_list = ['customer__name', 'qq__contains', 'mobile__contains']
    def get_urls(self):
        """
         URL最终的分发,如果要修改,可以在子类的handler重写此方法.
        :return:
        """
        patterns = [
            url(r'^list/$', self.wrapper(self.changelist_view), name=self.get_list_url_name),
            url(r'^change/(?P<pk>\d+)/$', self.wrapper(self.change_view), name=self.get_change_url_name),
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
            value.append(type(self).display_edit)
        return value

    search_group = [
        SearchOption('class_list', text_func=lambda x:"%s-%s" %(x.school, str(x)))
    ]


