# Generated by Django 2.2.6 on 2019-10-22 13:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('rbac', '0004_auto_20191022_2148'),
    ]

    operations = [
        migrations.AlterField(
            model_name='menu',
            name='title',
            field=models.CharField(max_length=32, verbose_name='一级菜单'),
        ),
    ]
