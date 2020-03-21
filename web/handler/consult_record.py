#!/usr/bin/env python 
# -*- coding: utf-8 -*- 
# Author : kuan
# Software : PyCharm
from django.conf.urls import url
from django.shortcuts import HttpResponse
from django.utils.safestring import mark_safe
from mystark.service.v1 import StarkHandler, StarkModelForm
from web import models
from .base import PermissionHandler


class ConsultRecordModelForm(StarkModelForm):
    class Meta:
        model = models.ConsultRecord
        fields = ["note", ]


class ConsultRecordHandler(PermissionHandler, StarkHandler):
    changelist_templates = 'consult_record.html'
    model_form_class = ConsultRecordModelForm
    list_display = ['customer', 'note', 'date', 'consultant']

    def get_urls(self):
        """
        为子类的ConsultRecordHandler重写此方法.
        :return:
        """
        patterns = [
            url(r'^list/(?P<customer_id>\d+)/$', self.wrapper(self.changelist_view), name=self.get_list_url_name),
            url(r'^add/(?P<customer_id>\d+)/$', self.wrapper(self.add_view), name=self.get_add_url_name),
            url(r'^change/(?P<customer_id>\d+)/(?P<pk>\d+)/$', self.wrapper(self.change_view),
                name=self.get_change_url_name),
            url(r'^delete/(?P<customer_id>\d+)/(?P<pk>\d+)/$', self.wrapper(self.delete_view),
                name=self.get_delete_url_name),
        ]
        patterns.extend(self.extra_url())
        return patterns

    def display_edit_and_del(self, obj=None, is_header=None, *args, **kwargs):
        """
        自定义编辑和删除
        :param obj:
        :param is_header:
        :return:
        """
        customer_id = kwargs.get('customer_id')
        if is_header:
            return '操作'
        tpl = "<a href='%s'>编辑</a> <a href='%s'>删除</a> " % (
            self.get_reverse_change_url(pk=obj.pk, customer_id=customer_id),
            self.get_reverse_delete_url(pk=obj.pk, customer_id=customer_id)
        )
        return mark_safe(tpl)

    def get_queryset(self, request, *args, **kwargs):
        """
        获取用户当前使用的model_class, 如果用户使用的model需要使用条件筛选，调用此方法即可。
        使用方法参考 public_customer.py
        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        # print(args,kwargs)
        customer_id = kwargs.get('customer_id')
        current_user_id = request.session["user_info"]["user_id"]
        # 当前查看的客户必须是操作人自己的客户才能查看记录。customer__consultant_id=current_user_id
        return self.model_class.objects.filter(customer_id=customer_id, customer__consultant_id=current_user_id)

    def get_change_object(self, request, pk, *args, **kwargs):
        current_user_id = request.session ["user_info"] ["user_id"]
        customer_id = kwargs.get('customer_id')
        #  编辑跟进记录时，必须是当前销售的客户and当前客户的跟进记录才能进行修改
        return models.ConsultRecord.objects.filter(pk=pk, customer_id=customer_id,
                                                   customer__consultant_id=current_user_id).first()

    def get_delete_object(self, request, pk, *args, **kwargs):
        current_user_id = request.session ["user_info"] ["user_id"]
        customer_id = kwargs.get('customer_id')
        delete_queryset = self.model_class.objects.filter(pk=pk, customer_id=customer_id,
                                                          customer__consultant_id=current_user_id).first()
        if not delete_queryset:
            return HttpResponse("删除操作发生错误，请重新选择")
        delete_queryset.delete()

    def save(self, request, form, is_update, *args, **kwargs):
        current_user_id = request.session ["user_info"] ["user_id"]
        customer_id = kwargs.get('customer_id')
        #  必须是当前客户的销售才能进行保存。
        ojb_exists = models.Customer.objects.filter(id=customer_id, consultant_id=current_user_id).exists()
        if not ojb_exists:
            return
        if not is_update:
            form.instance.customer_id = customer_id
            form.instance.consultant_id = current_user_id
        form.save()
