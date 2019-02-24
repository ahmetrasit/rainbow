from django.db import models
from django.contrib.auth.models import AbstractUser


class CustomUser(AbstractUser):
    CHOICES = ((role, role) for role in ('limited', 'unlimited'))

    created_on = models.DateTimeField(auto_now=True)
    role = models.CharField(choices=CHOICES, max_length=128, default=None, blank=True, null=True)
    credit = models.PositiveSmallIntegerField( default=None, blank=True, null=True)
    special = models.CharField(max_length=128, default=None, blank=True, null=True)
    score = models.CharField(max_length=128, default=None, blank=True, null=True)
    key_value = models.TextField(default=None, blank=True, null=True)


class MainConfiguration(models.Model):
    team_name = models.CharField(max_length=64)
    intro_message = models.CharField(max_length=256)
    cpu_ratio = models.DecimalField(max_digits=3, decimal_places=2)
    ram_ratio = models.DecimalField(max_digits=3, decimal_places=2)
    key_value = models.TextField()
    created_on = models.DateTimeField(auto_now=True)


class DataModel(models.Model):
    file = models.TextField(default=None, blank=True, null=True)
    data_model_bundle = models.IntegerField(default=None, blank=True, null=True)
    chromosome = models.TextField()
    chromosome_length = models.BigIntegerField()
    gene2info = models.TextField(default=None, blank=True, null=True)  #metagenome in a tree
    interval2genes = models.TextField()    #quick reference to find genes within an interval
    interval2blocks = models.TextField()   #for building arcs, should have low, middle, and high resolution modes
    rainbow2gene = models.TextField()
    created_on = models.DateTimeField(auto_now=True)


class DataModelBundle(models.Model):
    short_name = models.CharField(max_length=32)
    description = models.TextField()
    data_models = models.TextField()
    chromosome_list = models.TextField()
    biotype = models.TextField()
    source = models.TextField() #user or ensembl?
    type = models.CharField(max_length=32) #gene or data
    version = models.TextField(default=None, blank=True, null=True)
    organism = models.TextField(default=None, blank=True, null=True)
    reference_model = models.IntegerField(default=None, blank=True, null=True)
    created_by = models.TextField()
    created_on = models.DateTimeField(auto_now=True)


class SavedView(models.Model):
    access = models.CharField(max_length=128, default='public')
    short_name = models.CharField(max_length=128)
    description = models.TextField()
    version = models.TextField()
    organism = models.TextField()
    type = models.CharField(max_length=32) #gene or data
    data_bundle_source = models.TextField()
    created_by = models.TextField()
    created_on = models.DateTimeField(auto_now=True)


class Task(models.Model):
    request = models.TextField()
    created_by = models.TextField()
    status = models.TextField(default='started')
    created_on = models.DateTimeField(auto_now=True)
    finished_on = models.DateTimeField(default=None, blank=True, null=True)
