#!/usr/bin/env python 
# -*- coding: utf-8 -*- 
# Author : kuan
# Software : PyCharm
from django import forms


class DateTimePickerInput(forms.TextInput):
    template_name = 'stark/forms/widgets/datetime__picker.html'