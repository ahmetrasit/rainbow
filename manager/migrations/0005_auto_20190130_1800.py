# Generated by Django 2.1.5 on 2019-01-30 18:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('manager', '0004_savedview_access'),
    ]

    operations = [
        migrations.CreateModel(
            name='Log',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('request', models.TextField()),
                ('created_by', models.TextField()),
                ('status', models.TextField(default='started')),
                ('created_on', models.DateTimeField(auto_now=True)),
                ('finished_on', models.DateTimeField(blank=True, default=None, null=True)),
            ],
        ),
        migrations.RemoveField(
            model_name='datamodel',
            name='gene2intervals',
        ),
        migrations.AddField(
            model_name='datamodel',
            name='chromosome',
            field=models.TextField(default='-'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='datamodel',
            name='chromosome_length',
            field=models.BigIntegerField(default=0),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='datamodel',
            name='gene2info',
            field=models.TextField(default=1),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='datamodel',
            name='organism',
            field=models.TextField(blank=True, default=None, null=True),
        ),
        migrations.AddField(
            model_name='datamodel',
            name='reference_model',
            field=models.IntegerField(blank=True, default=None, null=True),
        ),
        migrations.AddField(
            model_name='datamodel',
            name='source',
            field=models.TextField(default=1),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='datamodel',
            name='version',
            field=models.TextField(blank=True, default=None, null=True),
        ),
    ]
