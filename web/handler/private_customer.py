#!/usr/bin/env python 
# -*- coding: utf-8 -*- 
# Author : kuan
# Software : PyCharm
from django.urls import reverse
from django.utils.safestring import mark_safe
from mystark.service.v1 import StarkHandler, get_choice_text, get_many2many_text, StarkModelForm
from web import models
from .base import PermissionHandler


class PrivateCustomerModelForm(StarkModelForm):
    class Meta:
        model = models.Customer
        exclude = ['consultant', ]  # 剔除某一字段


class PrivateCustomerHandler(PermissionHandler, StarkHandler):

    def display_record(self, obj=None, is_header=None, *args, **kwargs):
        if is_header:
            return "跟进记录"
        record_url = self.get_reverse_commons_url('web_consultrecord_list', customer_id=obj.pk)
        return mark_safe("<a target='_blank' href='%s'>打开</a>" % record_url)

    def display_payment_record(self, obj=None, is_header=None, *args, **kwargs):
        if is_header:
            return "缴费记录"
        record_url = reverse('stark:web_paymentrecord_list', kwargs={'customer_id': obj.pk})
        return mark_safe("<a target='_blank' href='%s'>查看</a>" % record_url)

    list_display = [StarkHandler.display_checkbox, 'name', 'qq', get_choice_text("状态", "status"),
                    get_many2many_text('咨询的课程', 'course'), 'consultant', display_record, display_payment_record]

    model_form_class = PrivateCustomerModelForm

    def get_queryset(self, request, *args, **kwargs):
        current_user_id = request.session["user_info"]["user_id"]
        return self.model_class.objects.filter(consultant_id=current_user_id)  # 获取当前操作人的数据

    def save(self, request, form, is_update, *args, **kwargs):
        if not is_update:
            current_user_id = request.session["user_info"]["user_id"]
            form.instance.consultant_id = current_user_id
        form.save()

    def select_multi_remove(self, request, *args, **kwargs):
        """
        批量操作申请到私人用户
        :param request:
        :return:
        """
        current_user_id = request.session["user_info"]["user_id"]
        pk_list = request.POST.getlist('pk')  # pk_list [1,2,3]
        self.model_class.objects.filter(id__in=pk_list, consultant_id=current_user_id).update(consultant=None)

    select_multi_remove.text = "批量移除到公共账户"
    select_list = [select_multi_remove, ]
