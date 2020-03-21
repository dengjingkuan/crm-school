#!/usr/bin/env python 
# -*- coding: utf-8 -*- 
# Author : kuan
# Software : PyCharm
from mystark.service.v1 import StarkHandler
from .base import PermissionHandler


class CourseHandler(PermissionHandler, StarkHandler):
    list_display = ['name']
