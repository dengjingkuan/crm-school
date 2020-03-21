#!/usr/bin/env python 
# -*- coding: utf-8 -*- 
# Author : kuan
# Software : PyCharm
from django.db import transaction
from django.conf.urls import url
from django.utils.safestring import mark_safe
from django.shortcuts import HttpResponse, render
from mystark.service.v1 import StarkHandler, StarkModelForm, get_choice_text, get_many2many_text
from web import models
from .base import PermissionHandler


class PublicCustomerModelForm(StarkModelForm):
    class Meta:
        model = models.Customer
        exclude = ['consultant']  # 剔除某一字段


class PublicCustomerHandler(PermissionHandler, StarkHandler):

    def display_record(self, obj=None, is_header=None):
        if is_header:
            return "跟进记录"
        return mark_safe("<a href='%s'>查看</a>" % self.get_reverse_record_url(pk=obj.pk))

    def get_queryset(self, request, *args, **kwargs):
        return self.model_class.objects.filter(consultant__isnull=True)

    def extra_url(self):
        patterns = [
            url(r'^record/(?P<pk>\d+)/$', self.wrapper(self.record_detail),
                name=self.get_record_url_name),
        ]
        return patterns

    def record_detail(self, request, pk):
        record_list = models.ConsultRecord.objects.filter(customer_id=pk)
        return render(request, 'record_detail.html', {'record_list': record_list})

    @property
    def get_record_url_name(self):
        return self.get_url_name('record')

    def get_reverse_record_url(self, *args, **kwargs):
        """
        快速生成修改按钮的URL
        :return:
        """
        return self.get_reverse_commons_url(self.get_record_url_name, *args, **kwargs)

    def select_multi_apply(self, request, *args, **kwargs):
        """
        批量操作申请到私人用户
        :param request:
        :return:
        """
        current_user_id = request.session["user_info"]["user_id"]
        pk_list = request.POST.getlist('pk')  # pk_list [1,2,3]
        private_customer_count = models.Customer.objects.filter(consultant_id=current_user_id, status=2).count()

        if int((len(pk_list) + private_customer_count)) > int(models.Customer.MAX_PRIVATE_CUSTOMER_COUNT):
            return HttpResponse("超过最大允许申请数，最多还允许申请%s个客户" %
                                (models.Customer.MAX_PRIVATE_CUSTOMER_COUNT - private_customer_count))
        flag = False
        with transaction.atomic():  # 事务
            # # 给数据库上锁，防止同一时刻有两名销售同时选择同一个客户
            origin_queryset = models.Customer.objects.filter(id__in=pk_list, status=2,
                                                             consultant__isnull=True).select_for_update()
            if len(origin_queryset) == len(pk_list):
                models.Customer.objects.filter(id__in=pk_list, status=2,
                                               consultant__isnull=True).update(consultant_id=current_user_id)
                flag = True

        if not flag:
            return HttpResponse('发生未知错误，请重新选择')

    select_multi_apply.text = "批量申请到我的账户"

    list_display = [StarkHandler.display_checkbox, 'name', 'qq', get_choice_text("状态", "status"),
                    get_many2many_text('咨询的课程', 'course'), display_record]
    select_list = [select_multi_apply, ]
    model_form_class = PublicCustomerModelForm


