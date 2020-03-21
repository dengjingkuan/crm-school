#!/usr/bin/env python
# -*- coding:utf-8 -*-
from django.conf.urls import url
from django.shortcuts import HttpResponse, render
from django.forms.models import modelformset_factory
from django.urls import reverse
from django.utils.safestring import mark_safe
from mystark.service.v1 import StarkHandler, StarkModelForm, get_datetime_text
from web import models
from .base import PermissionHandler


class StudyRecordModelForm(StarkModelForm):
    class Meta:
        model = models.StudyRecord
        fields = ['record', ]


class CourseRecordModelForm(StarkModelForm):
    class Meta:
        model = models.CourseRecord
        fields = ['day_num', 'teacher']


class CourseRecordHandler(PermissionHandler, StarkHandler):
    def display_attendance_record(self, obj=None, is_header=None, *args, **kwargs):
        if is_header:
            return "考勤"
        name = "%s:%s" % (self.site.namespace, self.get_url_name("attendance"))
        record_url = reverse(name, kwargs={'course_record_id': obj.pk})
        return mark_safe("<a target='_blank' href='%s'>打开</a>" % record_url)

    model_form_class = CourseRecordModelForm
    list_display = [StarkHandler.display_checkbox, 'class_object', 'day_num', 'teacher',
                    get_datetime_text('时间', 'date'), display_attendance_record]

    def display_edit_del(self, obj=None, is_header=None, *args, **kwargs):
        if is_header:
            return '操作'
        class_id = kwargs.get('class_id')
        tpl = '<a href="%s">编辑</a> <a href="%s">删除</a>' % (
            self.get_reverse_change_url(pk=obj.pk, class_id=class_id),
            self.get_reverse_delete_url(pk=obj.pk, class_id=class_id))
        return mark_safe(tpl)

    def get_urls(self):
        patterns = [
            url(r'^list/(?P<class_id>\d+)/$', self.wrapper(self.changelist_view), name=self.get_list_url_name),
            url(r'^add/(?P<class_id>\d+)/$', self.wrapper(self.add_view), name=self.get_add_url_name),
            url(r'^change/(?P<class_id>\d+)/(?P<pk>\d+)/$', self.wrapper(self.change_view),
                name=self.get_change_url_name),
            url(r'^delete/(?P<class_id>\d+)/(?P<pk>\d+)/$', self.wrapper(self.delete_view),
                name=self.get_delete_url_name),
            url(r'^attendance/(?P<course_record_id>\d+)/$', self.wrapper(self.attendance_view),
                name=self.get_url_name("attendance")),
        ]
        patterns.extend(self.extra_url())
        return patterns

    def get_queryset(self, request, *args, **kwargs):
        class_id = kwargs.get('class_id')
        return self.model_class.objects.filter(class_object_id=class_id)

    def save(self, request, form, is_update, *args, **kwargs):
        class_id = kwargs.get('class_id')

        if not is_update:
            form.instance.class_object_id = class_id
        form.save()

    def select_multi_delete(self, request, *args, **kwargs):
        #  获取考勤记录班级的id
        class_id = kwargs.get('class_id')
        #  获取批量POST提交的每个考勤id
        course_record_id_list = request.POST.getlist('pk')
        #  获取每个班级的对象
        class_list_obj = models.ClassList.objects.filter(id=class_id).first()
        if not class_list_obj:
            return HttpResponse('班级不存在')
        #  获取班级里的每个学生, （班级反向关联）
        student_object_list = class_list_obj.student_set.all()

        for course_record_id in course_record_id_list:
            #  判断上课记录是否合法, 上课记录id 与班级id 需相同
            course_record_obj = models.CourseRecord.objects.filter(id=course_record_id,
                                                                   class_object_id=class_id).first()
            if not class_list_obj:
                continue
            #  判断考勤记录是否存在
            study_record_exists = models.StudyRecord.objects.filter(course_record=course_record_obj).exists()
            if study_record_exists:
                continue
            # 生成考勤记录
            study_record_object_list = [models.StudyRecord(student_id=stu.id, course_record_id=course_record_id) for stu
                                        in student_object_list]

            models.StudyRecord.objects.bulk_create(study_record_object_list, batch_size=50)

    select_multi_delete.text = "批量生成考勤"
    select_list = [select_multi_delete, ]

    def attendance_view(self, request, course_record_id, *args , **kwargs ):
        """
        批量的考勤管理操作
        :param request:
        :param course_record_id:
        :param args:
        :param kwargs:
        :return:
        """
        #  1. 获取StudyRecord的所有数据, queryset
        study_record_object_list = models.StudyRecord.objects.filter(course_record_id=course_record_id)
        #  2. 生成一个study_record modelformset
        study_model_formset = modelformset_factory(models.StudyRecord, form=StudyRecordModelForm, extra=0)
        #  4.收到form post请求, 进行校验保存
        if request.method == "POST":
            formset = study_model_formset(queryset=study_record_object_list, data=request.POST)
            if formset.is_valid():
                formset.save()
            return render(request, 'attendance.html', {'formset': formset})

        #  3.实例化study_record modelformset，传入queryset
        formset = study_model_formset(queryset=study_record_object_list)

        return render(request, "attendance.html", {'formset': formset})
