# Generated by Django 2.1.5 on 2019-01-30 19:47

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('manager', '0005_auto_20190130_1800'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='Log',
            new_name='Task',
        ),
    ]
