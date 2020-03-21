#!/usr/bin/env python 
# -*- coding: utf-8 -*- 
# Author : kuan
# Software : PyCharm
from django import forms
from django.utils.safestring import mark_safe
from django.urls import reverse
from mystark.service.v1 import StarkHandler, get_many2many_text, StarkModelForm, SearchOption
from mystark.forms.widgets import DateTimePickerInput
from web import models
from .base import PermissionHandler


class ClassListModelForm(StarkModelForm):
    class Meta:
        model = models.ClassList
        fields = "__all__"
        widgets = {
            'start_date': DateTimePickerInput,
            'graduate_date': DateTimePickerInput,
        }


class ClassListHandler(PermissionHandler, StarkHandler):

    def display_course(self, obj=None, is_header=None):
        if is_header:
            return "班级"
        return "%s(%s)期" % (obj.course.name, obj.semester)

    def display_course_record(self, obj=None, is_header=None, *args, **kwargs):
        if is_header:
            return "上课记录"
        record_url = reverse('stark:web_courserecord_list', kwargs={'class_id': obj.pk})
        return mark_safe("<a target='_blank' href='%s'>查看</a>" % record_url)

    list_display = ['school', display_course, 'price', 'start_date',
                    'class_teacher', get_many2many_text('讲师', 'teach_teacher'),
                    display_course_record]
    search_group = [
        SearchOption('school'),
        SearchOption('course'),
    ]

    model_form_class = ClassListModelForm
