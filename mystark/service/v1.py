#!/usr/bin/env python
# -*- coding:utf-8 -*-
import copy
import functools
from types import FunctionType
from django.conf.urls import url
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.shortcuts import HttpResponse, render, redirect
from django.http import QueryDict
from django import forms
from django.db.models import Q
from django.db.models import ForeignKey, ManyToManyField
from django.template.response import TemplateResponse

from mystark.utils.pagination import Pagination


def get_choice_text(title, field):
    """
    对于Stark组件中定义列时，choice如果想要显示中文信息，调用此方法即可。
    :param title: 希望页面显示的表头中文字符
    :param field: 希望页面显示的内容中文字符
    :return:
    """

    def inner(self, obj=None, is_header=None, *args, **kwargs):
        if is_header:
            return title
        method = "get_%s_display" % field
        return getattr(obj, method)()

    return inner


def get_datetime_text(title, field, time_format='%Y-%m-%d'):
    """
    对于Stark组件中定义列时，定制时间格式的数据
    :param title: 希望页面显示的表头
    :param field: 字段名称
    :param time_format: 要格式化的时间格式
    :return:
    """

    def inner(self, obj=None, is_header=None, *args, **kwargs):
        if is_header:
            return title
        datetime_value = getattr(obj, field)
        return datetime_value.strftime(time_format)

    return inner


def get_many2many_text(title, field):
    """
    对于Stark组件中定义列时，显示manytomany文本信息
    :param title: 希望页面显示的表头
    :param field: 字段名称
    :param time_format: 要格式化的时间格式
    :return:
    """

    def inner(self, obj=None, is_header=None, *args, **kwargs):
        if is_header:
            return title
        queryset = getattr(obj, field).all()
        text_list = [str(row) for row in queryset]
        return '/'.join(text_list)

    return inner


class SearchGroupRow(object):
    def __init__(self, queryset_and_tuple_list, option, verbose__name, query_dict):
        """
        :param queryset_and_tuple_list: item可能是queryset 或者 是 tuple
        :param option: SearchOption
        :param verbose__name: 组合搜索的列名称
        :param query_dict: request.GET
        """
        self.queryset_and_tuple_list = queryset_and_tuple_list
        self.option = option
        self.verbose__name = verbose__name
        self.query_dict = query_dict

    def __iter__(self):
        yield "<div class='whole'>"
        yield self.verbose__name + ':'
        yield "</div>"
        yield "<div class='others'>"
        total_query_dict = self.query_dict.copy()
        total_query_dict._mutable = True
        origin_value_list = self.query_dict.getlist(self.option.field)  # 获取 'gender': ['1', ...] 里面的值, 用于判断默认选中
        if not origin_value_list:
            yield "<a class='active' href='?%s'>全部</a>" % total_query_dict.urlencode()
        else:
            total_query_dict.pop(self.option.field)
            yield "<a href='?%s'>全部</a>" % total_query_dict.urlencode()

        for field_object in self.queryset_and_tuple_list:
            text = self.option.get_text_func(field_object)
            #  生成带搜索条件的值，需要request.GET和组合搜索按钮背后对应的值
            value = str(self.option.get_value_func(field_object))  # <QueryDict: 如：{'gender': ['1'], 'depart': ['2']}>
            query_dict = self.query_dict.copy()  # 深copy,生成queryset时，不能影响其他用户的默认值
            query_dict._mutable = True

            if not self.option.is_multi:
                # 不支持组合搜索同一字段多选
                query_dict [self.option.field] = value  # <QueryDict: 真正的{'gender': ['1'], 'depart': ['2']}>
                if value in origin_value_list:
                    query_dict.pop(self.option.field)  # 再次点击按钮,把'gender':去除
                    yield "<a href='?%s' class='active'>%s</a> " % (query_dict.urlencode(), text)
                else:
                    yield "<a href='?%s'>%s</a>" % (query_dict.urlencode(), text)
            else:
                #  支持组合搜索同一字段多选
                multi_value_list = query_dict.getlist(self.option.field)  # 多选的'gender': ['1','2'],
                if value in multi_value_list:
                    #  如果组合搜索的值已经在multi_value_list中，需要remove删除
                    multi_value_list.remove(value)
                    query_dict.setlist(self.option.field, multi_value_list)
                    yield "<a href='?%s' class='active'>%s</a> " % (query_dict.urlencode(), text)
                else:
                    multi_value_list.append(value)
                    query_dict.setlist(self.option.field, multi_value_list)
                    yield "<a href='?%s'>%s</a>" % (query_dict.urlencode(), text)
        yield "</div>"


class SearchOption(object):
    def __init__(self, field, db_condition=None, text_func=None, value_func=None, is_multi=False):
        """
        可以根据URL的不同，动态生成不同含条件的组合搜索条件
        :param field:  组合搜索关联的字段名称
        :param db_condition: 数据库关联查询时的条件
        :param text_func: 用户自定制要显示的组合搜索字符
        :param value_func: 用于组合搜索获取按钮的值
        :param is_multi: 用于组合搜索支持同一条件的多选
        """
        self.field = field
        if not db_condition:
            db_condition = {}
        self.db_condition = db_condition
        self.text_func = text_func
        self.value_func = value_func
        self.is_multi = is_multi
        self.choices = False

    def get_db_condition(self, request, *args, **kwargs):
        """
        用户自定义要显示的字段
        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        return self.db_condition

    def get_queryset_or_tuple(self, model_class, request, *args, **kwargs):
        """
        根据search_group列表，反射生成要修改的字段。
        :param model_class: 数据库中的类
        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        field_object = model_class._meta.get_field(self.field)  # 找到search_group中对应的字段 如 UserInfo中的gender
        verbose__name = field_object.verbose_name
        if isinstance(field_object, ForeignKey) or isinstance(field_object, ManyToManyField):
            #  ForeignKey,M2M 生成的是 queryset
            db_condition = self.get_db_condition(request, *args, **kwargs)
            return SearchGroupRow(field_object.remote_field.model.objects.filter(**db_condition), self, verbose__name,
                                  request.GET)
        else:
            self.choices = True
            #  choices 生成的是 tuple self是SearchOption对象
            return SearchGroupRow(field_object.choices, self, verbose__name, request.GET)

    def get_text_func(self, field_object):
        """
        获取文本函数
        :param field_object: queryset_and_tuple_list中的item， 可能是queryset 或者是 tuple
        :return:
        """
        if self.text_func:
            return self.text_func(field_object)
        if self.choices:
            return field_object [1]
        return str(field_object)

    def get_value_func(self, field_object):
        if self.value_func:
            return self.value_func(field_object)
        if self.choices:
            return field_object [0]
        return field_object.pk


class StarkModelForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(StarkModelForm, self).__init__(*args, **kwargs)
        # 统一给ModelForm生成字段添加样式
        for name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'


class StarkForm(forms.Form):

    def __init__(self, *args, **kwargs):
        super(StarkForm, self).__init__(*args, **kwargs)
        # 统一给ModelForm生成字段添加样式
        for name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'


class StarkHandler(object):
    changelist_templates = None
    add_templates = None
    change_templates = None
    delete_templates = None

    list_display = []
    per_page_count = 10  # 默认显示的行条数
    has_add_btn = True   # 默认显示添加按钮
    model_form_class = None   # 默认使用stark的model_form_class
    order_list = []  # 默认显示的数据排序
    search_list = []  # 默认查询的列表
    search_group = []  # 默认显示的组合搜索
    select_list = []  # 全选操作的列表

    def display_checkbox(self, obj=None, is_header=None, *args, **kwargs):
        """
        :param obj:
        :param is_header:
        :return:
        """
        if is_header:
            return "选择"
        return mark_safe('<input type="checkbox" name="pk" value="%s" />' % obj.pk)

    def display_edit(self, obj=None, is_header=None, *args, **kwargs):
        """
        自定义页面显示的列（表头和内容）
        :param obj:
        :param is_header:
        :return:
        """
        if is_header:
            return "编辑"
        return mark_safe('<a href="%s">编辑</a>' % self.get_reverse_change_url(pk=obj.pk))

    def display_del(self, obj=None, is_header=None, *args, **kwargs):
        if is_header:
            return "删除"
        return mark_safe('<a href="%s">删除</a>' % self.get_reverse_delete_url(pk=obj.pk))

    def display_edit_del(self, obj=None, is_header=None, *args, **kwargs):
        if is_header:
            return '操作'

        tpl = '<a href="%s">编辑</a> <a href="%s">删除</a>' % (
            self.get_reverse_change_url(pk=obj.pk), self.get_reverse_delete_url(pk=obj.pk))
        return mark_safe(tpl)

    def get_list_display(self, request, *args, **kwargs):
        """
        获取页面上应该显示的列，预留的自定义扩展，例如：以后根据用户的不同显示不同的列
        :return:
        """
        value = []
        if self.list_display:
            value.extend(self.list_display)
            value.append(type(self).display_edit_del)
        return value

    def get_has_add_btn(self, request, *args, **kwargs):
        """
        添加按钮的展示
        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        if self.has_add_btn:
            return "<a class='btn btn-success' href='%s'>添加</a>" % self.get_reverse_add_url(*args, **kwargs)
        return None

    def get_model_form_class(self, is_add, request, pk, *args, **kwargs):
        """
        获取动态的model_form
        定制添加和编辑页面的model_form的定制
        :param is_add:
        :return:
        """
        if self.model_form_class:
            return self.model_form_class

        class DynamicModelForm(StarkModelForm):
            class Meta:
                model = self.model_class
                fields = "__all__"

        return DynamicModelForm

    def get_order_list(self):
        return self.order_list or ['-id', ]

    def get_search_list(self):
        return self.search_list

    def get_select_list(self):
        return self.select_list

    def select_multi_delete(self, request, *args, **kwargs):
        """
        批量删除（如果想要定制执行成功后的返回值，那么就为action函数设置返回值即可。）
        :return:
        """
        pk_list = request.POST.getlist('pk')
        self.model_class.objects.filter(id__in=pk_list).delete()

    select_multi_delete.text = "批量删除"

    def get_search_group(self):
        return self.search_group

    def get_search_group_condition(self, request):
        """
        获取组合搜索的条件
        :param request:
        :return:
        """
        condition = {}
        # ?depart=1&gender=2&page=123&q=999
        for option in self.get_search_group():
            if option.is_multi:
                values_list = request.GET.getlist(option.field)  # tags=[1,2]
                if not values_list:
                    continue
                condition['%s__in' % option.field] = values_list
            else:
                value = request.GET.get(option.field)  # tags=[1,2]
                if not value:
                    continue
                condition[option.field] = value
        return condition

    def __init__(self, site, model_class, prev):
        self.site = site
        self.model_class = model_class
        self.prev = prev
        self.request = None

    def get_queryset(self, request, *args, **kwargs):
        """
        获取用户当前使用的model_class, 如果用户使用的model需要使用条件筛选，调用此方法即可。
        使用方法参考 public_customer.py
        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        return self.model_class.objects

    def changelist_view(self, request, *args, **kwargs):
        """
        列表页面
        :param request:
        :return:
        """
        # ########## 1. 处理批量选择操作框 ##########
        select_list = self.get_select_list()
        select_dict = {func.__name__: func.text for func in select_list}  # {'multi_delete':'批量删除','multi_init':'批量初始化'}

        if request.method == 'POST':
            select_func_name = request.POST.get('select')
            if select_func_name and select_func_name in select_dict:  # 用户选择的操作内容必须在select_dict里面
                select_response = getattr(self, select_func_name)(request, *args, **kwargs)
                if select_response:
                    return select_response

        # ########## 2. 获取模糊搜索条件 ##########
        search_list = self.get_search_list()
        search_value = request.GET.get('q', '')
        conn = Q()
        conn.connector = 'OR'  # 自定义查询语法OR
        if search_value:
            for item in search_list:
                conn.children.append((item, search_value))

        # ########## 3. 获取排序 ##########
        order_list = self.get_order_list()
        # 获取组合的条件
        search_group_condition = self.get_search_group_condition(request)
        prev_queryset = self.get_queryset(request, *args, **kwargs)
        queryset = prev_queryset.filter(conn).filter(**search_group_condition).order_by(*order_list)

        # ########## 4. 处理分页 ##########
        all_count = queryset.count()

        query_params = request.GET.copy()
        query_params._mutable = True

        pager = Pagination(
            current_page=request.GET.get('page'),
            all_count=all_count,
            base_url=request.path_info,
            query_params=query_params,
            per_page=self.per_page_count,
        )

        data_list = queryset[pager.start:pager.end]

        # ########## 5. 处理表格 ##########
        list_display = self.get_list_display(request, *args, **kwargs)
        # 5.1 处理表格的表头
        header_list = []
        if list_display:
            for key_or_func in list_display:  # list_display = ['name', 'age', 'email', display_edit]
                if isinstance(key_or_func, FunctionType):
                    #  如果是函数的类型,执行此函数。
                    verbose_name = key_or_func(self, obj=None, is_header=True)
                else:
                    verbose_name = self.model_class._meta.get_field(key_or_func).verbose_name
                    #  如果是字段，获取字段的verbose_name
                header_list.append(verbose_name)
        else:
            header_list.append(self.model_class._meta.model_name)

        # 5.2 处理表的内容
        body_list = []
        for row in data_list:
            tr_list = []
            if list_display:
                for key_or_func in list_display:
                    if isinstance(key_or_func, FunctionType):
                        tr_list.append(key_or_func(self, row, False, *args, **kwargs))
                    else:
                        tr_list.append(getattr(row, key_or_func))  # obj.gender
            else:
                tr_list.append(row)
            body_list.append(tr_list)

        # ########## 6. 添加按钮 #########
        add_btn = self.get_has_add_btn(request, *args, **kwargs)

        # ########## 7. 组合搜索 #########
        search_group_list = []
        search_group = self.get_search_group()  # ['gender', 'depart']
        for option_object in search_group:
            row = option_object.get_queryset_or_tuple(self.model_class, request, *args, **kwargs)
            search_group_list.append(row)

        return render(
            request,
            self.changelist_templates or 'stark/changelist.html',
            {
                'data_list': data_list,
                'header_list': header_list,
                'body_list': body_list,
                'pager': pager,
                'add_btn': add_btn,
                'search_list': search_list,
                'search_value': search_value,
                'select_dict': select_dict,
                'search_group_list': search_group_list
            }
        )

    def save(self, request, form, is_update, *args, **kwargs):
        """
        在使用ModelForm保存数据之前预留的钩子方法
        :param request:
        :param form:
        :param is_update:
        :return:
        """
        form.save()

    def add_view(self, request, *args, **kwargs):
        """
        添加页面
        :param request:
        :return:
        """
        model_form_class = self.get_model_form_class(True, request, None, *args, **kwargs)
        if request.method == 'GET':
            form = model_form_class()
            return render(request, self.add_templates or 'stark/change.html', {'form': form})
        form = model_form_class(data=request.POST)
        if form.is_valid():
            response = self.save(request, form, False, *args, **kwargs)
            # 在数据库保存成功后，跳转回列表页面(携带原来的参数)。
            return response or redirect(self.get_reverse_list_url(*args, **kwargs))

        return render(request, self.add_templates or 'stark/change.html', {'form': form})

    def get_change_object(self, request, pk, *args, **kwargs):
        return self.model_class.objects.filter(pk=pk).first()

    def change_view(self, request, pk, *args, **kwargs):
        """
        编辑页面
        :param request:
        :param pk:
        :return:
        """
        current_change_object = self.get_change_object(request, pk, *args, **kwargs)
        if not current_change_object:
            return HttpResponse('要修改的数据不存在，请重新选择！')

        model_form_class = self.get_model_form_class(False, request, pk, *args, **kwargs)
        if request.method == 'GET':
            form = model_form_class(instance=current_change_object)
            return render(request, self.change_templates or 'stark/change.html', {'form': form})

        form = model_form_class(data=request.POST, instance=current_change_object)
        if form.is_valid():
            response = self.save(request, form, True, *args, **kwargs)
            # 在数据库保存成功后，跳转回列表页面(携带原来的参数)。
            return response or redirect(self.get_reverse_list_url(*args, **kwargs))
        return render(request, self.change_templates or 'stark/change.html', {'form': form})

    def delete_object(self, request, pk, *args, **kwargs):
        self.model_class.objects.filter(pk=pk).delete()

    def delete_view(self, request, pk, *args, **kwargs):
        """
        删除页面
        :param request:
        :param pk:
        :return:
        """
        origin_list_url = self.get_reverse_list_url(*args, **kwargs)
        if request.method == 'GET':
            return render(request, self.delete_templates or 'stark/delete.html', {'cancel': origin_list_url})

        response = self.delete_object(request, pk, *args, **kwargs)
        return response or redirect(origin_list_url)

    def get_url_name(self, param):
        app_label, model_name = self.model_class._meta.app_label, self.model_class._meta.model_name
        if self.prev:
            return '%s_%s_%s_%s' % (app_label, model_name, self.prev, param,)
        return '%s_%s_%s' % (app_label, model_name, param,)

    @property
    def get_list_url_name(self):
        """
        获取列表页面URL的name
        :return:
        """
        return self.get_url_name('list')

    @property
    def get_add_url_name(self):
        """
        获取添加页面URL的name
        :return:
        """
        return self.get_url_name('add')

    @property
    def get_change_url_name(self):
        """
        获取修改页面URL的name
        :return:
        """
        return self.get_url_name('change')

    @property
    def get_delete_url_name(self):
        """
        获取删除页面URL的name
        :return:
        """
        return self.get_url_name('delete')

    def get_reverse_commons_url(self, name, *args, **kwargs):
        name = "%s:%s" % (self.site.namespace, name,)  # stark:app01/userinfo/prev/list/
        base_url = reverse(name, args=args, kwargs=kwargs)
        if not self.request.GET:  # 如果没有url后缀条件，则直接反向生成
            param_url = base_url
        else:
            param = self.request.GET.urlencode()  # ?page=1
            new_query_dict = QueryDict(mutable=True)
            new_query_dict['_filter'] = param
            param_url = "%s?%s" % (base_url, new_query_dict.urlencode())
        return param_url

    def get_reverse_add_url(self, *args, **kwargs):
        """
        生成带有原搜索条件的添加URL
        :return:
        """
        return self.get_reverse_commons_url(self.get_add_url_name, *args, **kwargs)

    def get_reverse_change_url(self, *args, **kwargs):
        """
        生成带有原搜索条件的编辑URL
        :param args:
        :param kwargs:
        :return:
        """
        return self.get_reverse_commons_url(self.get_change_url_name, *args, **kwargs)

    def get_reverse_delete_url(self, *args, **kwargs):
        """
        生成带有原搜索条件的删除URL
        :param args:
        :param kwargs:
        :return:
        """
        return self.get_reverse_commons_url(self.get_delete_url_name, *args, **kwargs)

    def get_reverse_list_url(self, *args, **kwargs):
        """
        跳转回列表页面时，生成URL
        :return:
        """
        #  数据库保存成功后，返回changelist.html
        name = "%s:%s" % (self.site.namespace, self.get_list_url_name,)
        base_url = reverse(name, args=args, kwargs=kwargs)
        param = self.request.GET.get('_filter')
        if not param:
            return base_url
        return "%s?%s" % (base_url, param,)

    def wrapper(self, func):
        @functools.wraps(func)
        def inner(request, *args, **kwargs):
            self.request = request
            return func(request, *args, **kwargs)

        return inner

    def get_urls(self):
        """
         URL最终的分发,如果要修改,可以在子类的handler重写此方法.
        :return:
        """
        patterns = [
            url(r'^list/$', self.wrapper(self.changelist_view), name=self.get_list_url_name),
            url(r'^add/$', self.wrapper(self.add_view), name=self.get_add_url_name),
            url(r'^change/(?P<pk>\d+)/$', self.wrapper(self.change_view), name=self.get_change_url_name),
            url(r'^delete/(?P<pk>\d+)/$', self.wrapper(self.delete_view), name=self.get_delete_url_name),
        ]

        patterns.extend(self.extra_url())
        return patterns

    def extra_url(self):
        return []


class StarkSite(object):
    def __init__(self):
        self._registry = []
        self.app_name = 'stark'
        self.namespace = 'stark'

    def registry(self, model_class, handler_class=None, prev=None):
        """

        :param model_class: 是models中的数据库表对应的类。 models.UserInfo
        :param handler_class: 处理请求的视图函数所在的类
        :param prev: 生成URL的前缀
        :return:
        """
        """
        self._registry = [
            {'prev':None, 'model_class':models.Depart,'handler': DepartHandler(models.Depart,prev)对象中有一个model_class=models.Depart   },
            {'prev':'private', 'model_class':models.UserInfo,'handler':  StarkHandler(models.UserInfo,prev)对象中有一个model_class=models.UserInfo   }
            {'prev':None, 'model_class':models.Host,'handler':  HostHandler(models.Host,prev)对象中有一个model_class=models.Host   }
        ]
        """
        if not handler_class:
            handler_class = StarkHandler
        self._registry.append(
            {'model_class': model_class, 'handler_class': handler_class(self, model_class, prev), 'prev': prev})

    def get_urls(self):
        patterns = []
        for item in self._registry:
            model_class = item['model_class']
            handler = item['handler_class']
            prev = item['prev']
            # 获取self._registry中每个APP的名称,model_class的名称
            app_label, model_name = model_class._meta.app_label, model_class._meta.model_name
            if prev:
                patterns.append(url(r'^%s/%s/%s/' % (app_label, model_name, prev,), (handler.get_urls(), None, None)))
            else:
                patterns.append(url(r'%s/%s/' % (app_label, model_name,), (handler.get_urls(), None, None)))

        return patterns

    @property
    def urls(self):
        return self.get_urls(), self.app_name, self.namespace


site = StarkSite()
"""
实例化就会产生
self._registry = []
self.app_name = 'stark'
self.namespace = 'stark'
"""