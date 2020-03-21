#!/usr/bin/env python 
# -*- coding: utf-8 -*- 
# Author : kuan
# Software : PyCharm
from django.conf.urls import url
from mystark.service.v1 import StarkHandler, get_choice_text
from .base import PermissionHandler


class CheckPaymentRecordHandler(PermissionHandler, StarkHandler):
    has_add_btn = None
    list_display = [StarkHandler.display_checkbox, 'customer', 'consultant', get_choice_text('费用类型', 'pay_type'),
                    'paid_fee', 'class_list', 'apply_date', get_choice_text('状态', 'confirm_status')]

    def get_urls(self):
        """
         URL最终的分发,如果要修改,可以在子类的handler重写此方法.
        :return:
        """
        patterns = [
            url(r'^list/$', self.wrapper(self.changelist_view), name=self.get_list_url_name),
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

    def select_multi_checked(self, request, *args, **kwargs):
        """
        批量确认审核函数。
        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        pk_list = request.POST.getlist('pk')  # []
        for pk in pk_list:
            payment_object = self.model_class.objects.filter(id=pk, confirm_status=1).first()
            if not payment_object:
                continue
            #  修改确认状态
            payment_object.confirm_status = 2
            payment_object.save()
            #  修改客户状态
            payment_object.customer.status = 1
            payment_object.customer.save()
            #  修改学员状态
            payment_object.customer.student.student_status = 2
            payment_object.customer.student.save()

    select_multi_checked.text = "确认审核"

    def select_multi_cancel(self, request, *args, **kwargs):
        """
        批量驳回缴费申请
        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        pk_list = request.POST.getlist('pk')  # []
        self.model_class.objects.filter(id__in=pk_list, confirm_status=1).update(confirm_status=3)

    select_multi_cancel.text = "缴费驳回"

    select_list = [select_multi_checked, select_multi_cancel]