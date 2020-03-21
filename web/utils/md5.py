#!/usr/bin/env python 
# -*- coding: utf-8 -*- 
# Author : kuan
# Software : PyCharm
import hashlib


def md5_has(origin):
    """
    md5加密
    :param origin: 参数
    :return:
    """
    ha = hashlib.md5(b'dengjingkuan')
    ha.update(origin.encode('utf-8'))
    return ha.hexdigest()
