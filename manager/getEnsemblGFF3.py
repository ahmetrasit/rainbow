import os
import time
import json
import numpy as np
from functools import reduce
import re
from collections import Counter
from intervaltree import Interval, IntervalTree

from ftplib import FTP
import ntpath
import gzip, shutil, os

from django.core import serializers
from manager.models import *
from manager import views
import random
import html

class getEnsemblGFF3:


    def __init__(self):

        self.genome = None
        self.version = None
        self.chrom2len = None


    def revComp(self, seq):
        nts = 'AGNCT'
        pairs = {nts[i]:nts[4-i] for i in range(5)}
        return ''.join([self.pairs[nt] for nt in seq][::-1])


    def getCurrentRelease(self, lines):
        for line in lines:
            match = re.search(r'current_gff3\s+->\s+(release-\d+)/gff3', line)
            if match:
                return match.group(1)


    def getReleaseList(self):
        ftp = FTP('ftp.ensembl.org')
        ftp.login()

        lines = []
        ftp.dir("/pub", lines.append)
        current = self.getCurrentRelease(lines)

        rel = []
        for line in lines:
            match = re.search(r'\s+((\w+)\s+(\w+)\s+([\w:]+))\s(release-\d+)$',line)
            if match:
                if current and current == match.group(5):
                    rel.append([match.group(5), match.group(5) + ' (latest) - ' + match.group(1)])
                else:
                    rel.append([match.group(5), match.group(5) + ' - ' + match.group(1)])
        return rel[::-1]


    def getOrganismList(self, release):
        ftp = FTP('ftp.ensembl.org')
        ftp.login()
        dirname = '/pub/' + release + '/gff3'
        return dirname, [curr.split("/")[-1] for curr in ftp.nlst(dirname)]


    def getGFFList(self, release, organism):
        ftp = FTP('ftp.ensembl.org')
        ftp.login()
        dirname = '/pub/' + release + '/gff3/' + organism
        files = ftp.nlst(dirname)
        chrom_gff_list = [curr for curr in files if re.search(r'chromosome\.\w+\.gff3.gz', curr)]
        if len(chrom_gff_list) == 0:
            chrom_gff_list = [curr for curr in files if re.search(r'\d\.gff3.gz', curr)]

        return '/pub/' + release + '/gff3/' + organism, chrom_gff_list


    def downloadGFF(self, path, target_dir):
        ftp = FTP('ftp.ensembl.org')
        ftp.login()
        filename = ntpath.basename(path)
        with open(target_dir + filename, 'wb') as f:
            ftp.retrbinary('RETR %s' % path, f.write)

        with gzip.open(target_dir + filename, 'r') as f_in, open(target_dir + filename[:-3], 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)

        os.remove(target_dir + filename)

        return target_dir + filename[:-3], filename[:-3]
