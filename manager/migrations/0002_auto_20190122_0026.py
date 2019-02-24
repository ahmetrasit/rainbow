# Generated by Django 2.1.5 on 2019-01-22 00:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('manager', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='GeneModel',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('file', models.TextField()),
                ('short_name', models.CharField(max_length=128)),
                ('description', models.TextField()),
                ('gene2intervals', models.TextField()),
                ('interval2genes', models.TextField()),
                ('interval2blocks', models.TextField()),
                ('tracks', models.TextField()),
                ('created_by', models.TextField()),
                ('created_on', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.AlterField(
            model_name='customuser',
            name='role',
            field=models.CharField(blank=True, choices=[('limited', 'limited'), ('unlimited', 'unlimited')], default=None, max_length=128, null=True),
        ),
    ]
