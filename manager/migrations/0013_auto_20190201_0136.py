# Generated by Django 2.1.5 on 2019-02-01 01:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('manager', '0012_datamodelbundle_biotype'),
    ]

    operations = [
        migrations.AddField(
            model_name='savedview',
            name='organism',
            field=models.TextField(default=''),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='savedview',
            name='type',
            field=models.CharField(default='', max_length=32),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='savedview',
            name='version',
            field=models.TextField(default=''),
            preserve_default=False,
        ),
    ]
