# Generated by Django 2.1.5 on 2019-01-31 17:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('manager', '0007_auto_20190131_1658'),
    ]

    operations = [
        migrations.AddField(
            model_name='datamodelbundle',
            name='data_models',
            field=models.TextField(default=''),
            preserve_default=False,
        ),
    ]
