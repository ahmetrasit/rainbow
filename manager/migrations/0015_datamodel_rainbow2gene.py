# Generated by Django 2.1.5 on 2019-02-23 01:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('manager', '0014_auto_20190214_0057'),
    ]

    operations = [
        migrations.AddField(
            model_name='datamodel',
            name='rainbow2gene',
            field=models.TextField(default=''),
            preserve_default=False,
        ),
    ]
