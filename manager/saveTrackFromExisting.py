#commented already started at 57
import os
import time
import json
import numpy as np
from functools import reduce
import re
from collections import Counter
from intervaltree import Interval, IntervalTree
import traceback

from .getEnsemblGFF3 import getEnsemblGFF3 as geg3
from .parseEnsemblGFF3 import parseEnsemblGFF3 as peg3
from ftplib import FTP
import ntpath
import gzip, shutil, os

from django.core import serializers
from manager.models import *
from manager import views
import random
import html



class saveTrackFromExisting:

    def __init__(self, username, bundle2gene, curr_bundles, keyword):
        self.username = username
        self.bundle2gene = bundle2gene
        self.curr_bundles = curr_bundles
        self.keyword =  keyword
        self.version = None
        self.genome = None

    def createNewDataModelFromExisting(self):
        chrom2data, chrom2len = self.mergeGene2Info(self.bundle2gene)
        chrom_list = sorted(list(chrom2len.keys()))
        pks = []
        global_gene2info = {}
        for chrom in chrom2data:
            gene2info = chrom2data[chrom]
            global_gene2info = self.add2GlobalGene2Info(chrom, gene2info, global_gene2info)
            interval2genes = {}
            interval2blocks ={}
            rainbow2gen = {}
            if gene2info:
                interval2genes, interval2blocks, rainbow2gene = self.getTrackData(chrom2len[chrom], gene2info)
            pk = self.saveChromosomeData(chrom, chrom2len[chrom], gene2info, interval2genes, interval2blocks, rainbow2gene)
            pks.append(pk)

        bundle_pk = self.saveDataModelBundle('search', pks, chrom_list, self.keyword+' query results', global_gene2info)
        for pk in pks:
            DataModel.objects.filter(pk=pk).update(data_model_bundle=bundle_pk)

        self.curr_bundles.append(bundle_pk)
        print(self.curr_bundles)
        saved_pk = SavedView.objects.create(
                    short_name = '{}-{}-{}'.format(self.keyword+' query results', self.getGenomeShortName(self.genome), self.version) ,
                    description = 'Genes of {}, {} from {}'.format(self.getGenomeShortName(self.genome), self.version, self.keyword+' query results') ,
                    version = self.version,
                    organism = self.genome,
                    type = 'search',
                    data_bundle_source = json.dumps(['{};{}'.format(bundle_pk, chrom_list[0]) for bundle_pk in self.curr_bundles]),
                    created_by = self.username
        )

        return saved_pk


    def addPkToLatestSaved(self, new_pk):
        self.curr_bundles.append(new_pk)
        pass


    def getGene2Info(self, bundle_pk, bundle2gene):
        chrom2data = {}
        chrom2len = {}
        curr_bundle = DataModelBundle.objects.filter(pk=bundle_pk).values('chromosome_list', 'version', 'organism')[0]
        chroms =  json.loads(curr_bundle['chromosome_list'])
        self.version = curr_bundle['version']
        self.genome = curr_bundle['organism']
        for chrom in chroms:
            chrom2data[chrom] = {}
            curr_model = DataModel.objects.filter(data_model_bundle=bundle_pk, chromosome=chrom).values('chromosome_length', 'gene2info')[0]
            curr_gene2info = json.loads(curr_model['gene2info'])
            chrom2len[chrom] = curr_model['chromosome_length']
            if chrom in bundle2gene[bundle_pk]:
                gene2rid = {}
                gene2info = {}
                for gene , r_id in bundle2gene[bundle_pk][chrom]:
                    try:
                        gene2rid[gene].append(r_id)
                    except:
                        gene2rid[gene] = [r_id]


                filtered_genes = [gene for gene in curr_gene2info if gene in gene2rid]
                for gene in filtered_genes:
                    for curr in curr_gene2info[gene]:
                        if curr['r_id'] in gene2rid[gene]:
                            try:
                                gene2info[gene].append(curr)
                            except:
                                gene2info[gene] = [curr]
                chrom2data[chrom] = gene2info

        return chrom2data, chrom2len


    def mergeGene2Info(self, bundle2gene):
        chrom2data = {}
        chrom2len = {}
        for bundle_pk in bundle2gene:
            curr_chrom2data, curr_chrom2len = self.getGene2Info(bundle_pk, bundle2gene)
            chrom2len = {**chrom2len, **curr_chrom2len}
            print(chrom2len.keys())
            print(curr_chrom2len.keys())
            print()
            for chrom in curr_chrom2data:   #merging gene2info from different bundles, if any
                if chrom not in chrom2data:
                    chrom2data[chrom] = {}
                chrom2data[chrom] = {**chrom2data[chrom], **curr_chrom2data[chrom]}
        return chrom2data, chrom2len



    def getTrackData(self, chrom_len, gene2info):
        gene2intervals = {}
        rainbow2gene = {}
        for gene in gene2info:
            gene2intervals[gene] = gene2info[gene]
            for index, curr in enumerate(gene2info[gene]):
                rainbow2gene[curr['r_id']] = gene
                gene2intervals[gene][index] = curr
                for subtype in curr['interval']:
                    gene2intervals[gene][index]['interval'][subtype] = self.tree2json(curr['interval'][subtype], False)

        trees = {'+':{}, '-':{}}

        strand2info = {'+':[], '-':[]}
        for gene in gene2info:
            for index, curr in enumerate(gene2info[gene]):
                for strand in ['+', '-']:
                    if curr['annot']['strand'] == strand:
                        strand2info[strand].append([curr['annot']['start'], curr['annot']['end'], curr['r_id']])

        #strand2info = {strand:[[gene2info[curr]['annot']['start'], gene2info[curr]['annot']['end'], curr] for curr in gene2info if gene2info[curr]['annot']['strand'] == strand] for strand in ['+', '-']}
        for strand in ['+', '-']:
            trees[strand] = IntervalTree.from_tuples(strand2info[strand])

        interval2genes = self.getRangesFromTree(chrom_len, trees)
        interval2blocks = self.getBlocksFromTree(chrom_len, trees)

        return interval2genes, interval2blocks, rainbow2gene

    def tree2json(self, tree, add_data=True):
        output = []
        for branch in tree:
            start, end, *data = branch
            if add_data:
                output.append([start, end, data[0]])
            else:
                output.append([start, end])
        return sorted(output)


    def getRangesFromTree(self, chrom_len, trees, k=10000, m=0):
        ranges = {'+':[], '-':[]}
        for strand in ranges:
            tree = trees[strand]
            for i in range(0, chrom_len+1, k):
                ranges[strand].append([curr[-1] for curr in self.tree2json(tree.overlap(i-m, i+k+m))])
        return ranges


    def getBlocksFromTree(self, chrom_len, tree):
        #diameter of a semi-circle with given pixels: pixels*pi/2
        pixels = {'low':800, 'mid':1280, 'high':2880, 'ultra':5120}
        resolutions = {curr:pixels[curr]*3/2 for curr in pixels}
        arc_blocks = {curr:{} for curr in resolutions}

        for curr in arc_blocks:
            ranges_arc = {'+':{}, '-':{}}
            countd = {'+':[], '-':[]}
            count_tree = {'+':None, '-':None}
            block_size =  chrom_len//resolutions[curr]
            arc_blocks[curr] = self.getArcChromBlock(tree, chrom_len, block_size)
        return arc_blocks


    def getArcChromBlock(self, tree, chrom_len, block_size):
        m = 0
        arcBlockInterval = {strand:None for strand in ['+', '-']}
        for strand in ['+', '-']:
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





    def add2GlobalGene2Info(self, chrom, local_gene2info, global_gene2info):
        for gene in local_gene2info:
            for curr in local_gene2info[gene]:
                r_id = curr['r_id']
                annot = curr['annot']
                info = {
                        'r_id' : r_id,
                        'chrom' : chrom,
                        'strand' : annot['strand'],
                        'start' : annot['start'],
                        'end' : annot['end'],
                        'id' : annot['id'],
                        'name' : annot['name'],
                        'meta' : annot['meta'],
                        'biotype' : annot['biotype'],
                        'description' : annot['description'],
                        'no_of_isoforms' : len(curr['interval'].keys())
                }
                try:
                    global_gene2info[gene].append(info)
                except:
                    global_gene2info[gene] = [info]
        return global_gene2info



    def saveChromosomeData(self, chromosome, chromosome_length, gene2info, interval2genes, interval2blocks, rainbow2gene):
        saved = DataModel.objects.create(
                    chromosome = chromosome,
                    chromosome_length = chromosome_length,
                    gene2info = json.dumps(gene2info),
                    interval2genes = json.dumps(interval2genes),
                    interval2blocks = json.dumps(interval2blocks),
                    rainbow2gene = json.dumps(rainbow2gene)
        )
        return saved.pk



    def saveDataModelBundle(self, source, data_models, chromosome_list, biotype, global_gene2info):
        saved = DataModelBundle.objects.create(
                    short_name = '{}-{}-{}'.format(biotype, self.version, self.getGenomeShortName(self.genome)) ,
                    description = '{} genes of {}, {} from {}'.format(biotype, self.getGenomeShortName(self.genome), self.version, source) ,
                    data_models = json.dumps(data_models),
                    chromosome_list = json.dumps(chromosome_list),
                    biotype = biotype,
                    global_gene2info = json.dumps(global_gene2info),
                    source = source,
                    type = 'search',
                    version = self.version,
                    organism = self.genome,
                    created_by = self.username
        )
        return saved.pk



    def getGenomeShortName(self, genome):
        fields = genome.split("_")
        return fields[0].upper()[0] + '. ' + fields[1]
