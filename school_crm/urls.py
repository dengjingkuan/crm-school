"""school_crm URL Configuration

The `urlpatterns` list routes URLs to handler. For more information please see:
    https://docs.djangoproject.com/en/2.0/topics/http/urls/
Examples:
Function handler
    1. Add an import:  from my_app import handler
    2. Add a URL to urlpatterns:  path('', handler.home, name='home')
Class-based handler
    1. Add an import:  from other_app.handler import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from django.conf.urls import url, include
from mystark.service.v1 import site
from web.views import account

urlpatterns = [
    path('admin/', admin.site.urls),
    url(r'stark/', site.urls),
    url(r'^rbac/', include('rbac.urls', namespace='rbac')),
    url(r'login/', account.login, name='login'),
    url(r'logout/', account.logout, name='logout'),
    # url(r'get_ValidCode_img/', account.get_ValidCode_img, name='get_ValidCode_img'),
    url(r'index/', account.index, name='index'),
]
