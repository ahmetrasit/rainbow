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


class processBEDFile:

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
        self.release = temp['version']
        self.chrom2len = {curr['chromosome']:curr['chromosome_length']  for curr in DataModel.objects.filter(data_model_bundle=bundle_pk).values('chromosome', 'chromosome_length')}



    def getData(self, file):
        data = {}
        with open(file) as f:
            for line in f.readlines():
                chrom, start, end, strand, name, *value = line.strip().split()
                start = int(start)
                end = int(end)
                if chrom != "*":
                    if chrom in data:
                        if strand in data[chrom]:
                            data[chrom][strand].append((start, end, (name, *value)))
                        else:
                            data[chrom][strand] = [(start, end, (name, *value))]
                    else:
                        data[chrom] = {strand:[(start, end, (name, *value))]}
        return data


    def getTrees(self, data):
        trees = {}
        for chrom in data:
            trees[chrom] = {}
            for strand in data[chrom]:
                trees[chrom][strand] = IntervalTree.from_tuples(data[chrom][strand])

        return trees


    def tree2json(self, tree, add_data=True):
        output = []
        for branch in tree:
            start, end, *data = branch
            if add_data:
                output.append([start, end, data[0]])
            else:
                output.append([start, end])
        return sorted(output)


    def getBlocksFromTree(self, chrom, tree):
        #diameter of a semi-circle with given pixels: pixels*pi/2
        pixels = {'low':800, 'mid':1280, 'high':2880, 'ultra':5120}
        resolutions = {curr:pixels[curr]*3/2 for curr in pixels}
        arc_blocks = {curr:{} for curr in resolutions}

        for curr in arc_blocks:
            ranges_arc = {'+':{}, '-':{}}
            countd = {'+':[], '-':[]}
            count_tree = {'+':None, '-':None}
            chrom_len = self.chrom2len[chrom]
            block_size =  chrom_len//resolutions[curr]
            arc_blocks[curr] = self.getArcChromBlock(tree, chrom_len, block_size)
        return arc_blocks



    def getArcChromBlock(self, tree, chrom_len, block_size):
        m = 0
        arcBlockInterval = {strand:None for strand in ['+', '-']}
        for strand in tree:
            blocks = []
            curr_tree = tree[strand]
            for i in range(0, int(chrom_len//block_size+1)):
                overlap = curr_tree.overlap(i*block_size, (i+1)*block_size)
                if len(overlap) > 0:
                    blocks.append([i, i+1.01])
            block_tree = IntervalTree.from_tuples(blocks)
            block_tree.merge_overlaps()
            arcBlockInterval[strand] = self.tree2json(block_tree, False)
        return arcBlockInterval


    def getRangesFromTree(self, chrom, trees, k=10000, m=0):
        ranges = {'+':[], '-':[]}
        for strand in trees:
            tree = trees[strand]
            for i in range(0, self.chrom2len[chrom]+1, k):
                ranges[strand].append([curr[-1] for curr in self.tree2json(tree.overlap(i-m, i+k+m))])
        return ranges


    def getAllData(self, chrom, tree):

        interval2genes = self.getRangesFromTree(chrom, tree)
        interval2blocks = self.getBlocksFromTree(chrom, tree)

        return interval2genes, interval2blocks


    def getGene2Info(self, chrom, data):
        gene2info = {}
        rainbow2gene = {}
        rainbow_tree = {}

        ranges = {'+':[], '-':[]}
        r_id = 0
        for strand in data:
            tree_tuple = []
            for datum in data[strand]:
                r_id += 1
                start, end, (element, *values) = datum
                tree_tuple.append([start, end, r_id])
                rainbow2gene[r_id] = element
                curr = {
                        'r_id':r_id,
                        'annot':{'chrom':chrom,'strand':strand,'start': start,'end': end,'values' : values },
                        'interval':{ '-':[ [start, end] ] }
                        }
                try:
                    gene2info[element].append(curr)
                except:
                    gene2info[element] = [curr]
            rainbow_tree[strand] = IntervalTree.from_tuples(tree_tuple)

        return gene2info, rainbow2gene, rainbow_tree


    def buildData(self):
        success = False
        given_task = 'buildData({},{})'.format(self.release, self.genome)

        Task.objects.create(
            request = given_task,
            created_by = self.username
        )
        data =  self.getData(self.file)
        print('file', self.file)
        success_1, bundle_pk_1, failed_files_1, chrom_list, source = self.buildDataTrack(data, given_task)

        SavedView.objects.create(
                    short_name = self.short_name,
                    description = '{}, built for {}-{}'.format(self.description, self.release, self.getGenomeShortName(self.genome)) ,
                    version = self.release,
                    organism = self.genome,
                    type = 'data',
                    data_bundle_source = json.dumps(['{};{}'.format(bundle_pk_1, chrom_list[0])]),
                    created_by = self.username
        )
        print('>> view is saved')

        return success_1 , [bundle_pk_1], set(failed_files_1)




    def buildDataTrack(self, data, given_task):
        pks = []
        failed_files = []
        success = False

        trees = self.getTrees(data)
        for chrom in trees:
            print(chrom)
            gene2info, rainbow2gene, rainbow_tree = self.getGene2Info(chrom, data[chrom])
            interval2genes, interval2blocks = self.getAllData(chrom, rainbow_tree)
            pk = self.saveChromosomeData(self.file, chrom, self.chrom2len[chrom], interval2genes, interval2blocks, gene2info, rainbow2gene)
            pks.append(pk)
            Task.objects.filter(request = given_task, created_by = self.username).update(status='completed')
        if len(pks)>0:
            bundle_pk = self.saveDataModelBundle('BED', pks, self.chrom2len.keys())
            for pk in pks:
                DataModel.objects.filter(pk=pk).update(data_model_bundle=bundle_pk)
            success = True
        else:
            bundle_pk = -1

        if len(failed_files) > 0:
            views.notifyUser(self.username, '{} from Ensembl {} is now ready for visualization with exceptions:{}'.format(self.genome, self.release, failed_files))
        else:
            views.notifyUser(self.username, '{} from Ensembl {} is now ready for visualization.'.format(self.genome, self.release))

        return success, bundle_pk, failed_files, list(self.chrom2len.keys()), 'BED'




    def saveChromosomeData(self, file, chromosome, chromosome_length, interval2genes, interval2blocks, gene2info, rainbow2gene):
        saved = DataModel.objects.create(
                    file = file,
                    chromosome = chromosome,
                    chromosome_length = chromosome_length,
                    interval2genes = json.dumps(interval2genes),
                    interval2blocks = json.dumps(interval2blocks),
                    gene2info = json.dumps(gene2info),
                    rainbow2gene = json.dumps(rainbow2gene)

        )
        return saved.pk






    def saveDataModelBundle(self, source, data_models, chromosome_list):
        saved = DataModelBundle.objects.create(
                    short_name = self.short_name,
                    description = '{}, built for {}-{}'.format(self.description, self.release, self.getGenomeShortName(self.genome)) ,
                    data_models = json.dumps(data_models),
                    chromosome_list = json.dumps(list(chromosome_list)),
                    biotype = self.short_name,
                    source = source,
                    type = 'data',
                    version = self.release,
                    organism = self.genome,
                    created_by = self.username
        )
        return saved.pk



    def getGenomeShortName(self, genome):
        fields = genome.split("_")
        return fields[0].upper()[0] + '. ' + fields[1]
