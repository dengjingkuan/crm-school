#!/usr/bin/env python
# -*- coding:utf-8 -*-

import re
from collections import OrderedDict
from django.conf import settings
from django.utils.module_loading import import_string
from django.urls import URLResolver, URLPattern


def check_url_exclude(url):
    """
    排除一些特定的URL
    :param url:
    :return:
    """
    for regex in settings.AUTO_DISCOVER_EXCLUDE:
        if re.match(regex, url):
            return True


def recursion_urls(pre_namespace, pre_url, urlpatterns, url_ordered_dict):
    """

    :param pre_namespace: url的namespace前缀，以后用于拼接name.  "rbac:name"
    :param pre_url: url的前缀，以后用于拼接url.
    :param urlpatterns: 路由关系列表。
    :param url_ordered_dict: 用于保存递归中获取的所有路由。
    :return:
    """
    for item in urlpatterns:
        if isinstance(item, URLPattern):  # isinstance 判断类型 如果是URLPattern类型表示非路由分发，添加到url_ordered_dict中。
            if not item.name:  # 如果获取的url 没有name。排除
                continue

            name = item.name
            if pre_namespace:
                name = "%s:%s" % (pre_namespace, item.name)  # 如果有别名(name),并且有前缀，那么需要拼接前缀。
            url = pre_url + item.pattern.regex.pattern  # url(r'^user/reset/password/(?P<pk>\d+)/$',
            url = url.replace('^', '').replace('$', '')  # '/user/reset/password/(?P<pk>\d+)/',
            if check_url_exclude(url):
                continue
            url_ordered_dict[name] = {'name': name, 'url': url}

        elif isinstance(item, URLResolver):  # 类型URLResolver 表示是路由分发，需要继续递归。
            if pre_namespace:  # 如果有namespance前缀，并且分发的url也有。就拼接
                if item.namespace:
                    namespace = "%s:%s" % (pre_namespace, item.namespace)
                else:  # 如果有namespance前缀，但是分发的url没有namespance，就用父级的。
                    namespace = item.namespace
            else:
                if item.namespace:  # 没有namespance前缀，但是分发的url有namespance，就用子级的。
                    namespace = item.namespace
                else:
                    namespace = None  # pre_url + item.pattern.regex.pattern 之前的前缀+现在的前缀

            recursion_urls(namespace, pre_url + item.pattern.regex.pattern, item.url_patterns, url_ordered_dict)


def get_all_url_dict():
    """
    获取项目中所有的URL（必须有name别名）
    :return:
    """
    url_ordered_dict = OrderedDict()

    md = import_string(settings.ROOT_URLCONF)  # from luff.. import urls
    recursion_urls(None, '/', md.urlpatterns, url_ordered_dict)  # 递归去获取所有的路由

    return url_ordered_dict
