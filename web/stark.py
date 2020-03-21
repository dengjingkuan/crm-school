#!/usr/bin/env python 
# -*- coding: utf-8 -*- 
# Author : kuan
# Software : PyCharm
from mystark.service.v1 import site
from web import models
from web.handler import school
from web.handler import depart
from web.handler import userinfo
from web.handler import course
from web.handler import classlist
from web.handler import public_customer
from web.handler import private_customer
from web.handler import consult_record
from web.handler import payment_record
from web.handler import checked_payment_record
from web.handler import student
from web.handler import score_record
from web.handler import course_record


site.registry(models.School, school.SchoolHandler)  # 注册stark组件
site.registry(models.Department, depart.DepartHandler)
site.registry(models.UserInfo, userinfo.UserInfoHandler)
site.registry(models.Course, course.CourseHandler)
site.registry(models.ClassList, classlist.ClassListHandler)
site.registry(models.Customer, public_customer.PublicCustomerHandler, 'public')
site.registry(models.Customer, private_customer.PrivateCustomerHandler, 'private')
site.registry(models.ConsultRecord, consult_record.ConsultRecordHandler)
site.registry(models.PaymentRecord, payment_record.PaymentRecordHandler)
site.registry(models.PaymentRecord, checked_payment_record.CheckPaymentRecordHandler, 'checked')
site.registry(models.Student, student.StudentHandler)
site.registry(models.ScoreRecord, score_record.ScoreRecordHandler)
site.registry(models.CourseRecord, course_record.CourseRecordHandler)

