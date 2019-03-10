import os
import time
import json
import numpy as np
from functools import reduce
import re
from collections import Counter
from intervaltree import Interval, IntervalTree

from .getEnsemblGFF3 import getEnsemblGFF3 as ge
from ftplib import FTP
import ntpath
import gzip, shutil, os

from django.core import serializers
from manager.models import *
from manager import views
import random
import html


class processMetaDataFile:

    def __init__(self, file, release_pk, short_name, description, username):
        self.release_pk = int(release_pk)
        self.file = file
        self.short_name = short_name
        self.description = description
        self.username = username
        temp = SavedView.objects.filter(pk=self.release_pk).values('data_bundle_source')
        bundle_pk = int(json.loads(list(temp)[0]['data_bundle_source'])[0].split(";")[0])
        temp = list(DataModelBundle.objects.filter(pk=bundle_pk).values('version', 'organism'))[0]
        self.genome = temp['organism']
        self.version = temp['version']
        self.chrom2len = {curr['chromosome']:curr['chromosome_length']  for curr in DataModel.objects.filter(data_model_bundle=bundle_pk).values('chromosome', 'chromosome_length')}



    def buildData(self):
        mapping = {}
        with open(self.file) as f:
            lines = f.readlines()
        header = lines[0].strip().split("\t")

        if self.checkHeader(header):
            for line in lines[1:]:
                fields = line.strip().split("\t")
                if len(fields) == 2:
                    mapping[fields[0]] = fields[1]
        if len(mapping) > 0:
            self.saveMapping(header[0], header[1], mapping)
        else:
            print('problem with the meta data file')


    def checkHeader(self, header):
        required = ['biotype', 'id', 'name']
        reserved = ['chrom', 'source', 'subtype', 'strand', 'id', 'name', 'biotype', 'gene_id', 'meta']
        if len(header) == 2:
            if header[0] in required and header[1] not in reserved:
                return True
        return False



    def saveMapping(self, source, target, mapping):
        saved = MetaData.objects.create(
                    file = self.file,
                    source = source,
                    target = target,
                    short_name = self.short_name,
                    description = self.description,
                    mapping = json.dumps(mapping),
                    version = self.version,
                    organism = self.genome,
                    reference_model = self.release_pk,
                    created_by = self.username
        )
        return saved.pk
