import os
import time
import json
import numpy as np
from functools import reduce
import re
from collections import Counter
from intervaltree import Interval, IntervalTree

from django.core import serializers
from manager.models import *
from manager import views
import random
import html

class parseWormBaseGeneModel:

    def __init__(self, file):
        self.file = file
        self.nts = 'AGNCT'
        self.pairs = {self.nts[i]:self.nts[4-i] for i in range(5)}
        self.chrom2len = {  'I':15072434,
                            'II':15279421,
                            'III':13783801,
                            'IV':17493829,
                            'V':20924180,
                            'X':17718942,
                            'MtDNA':13794}


    def revComp(self, seq):
        return ''.join([self.pairs[nt] for nt in seq][::-1])

    def getTranscriptGeneName(self, name):
        match = re.search(r'(:|=)((\w+[A-Z]\w+\.t?\d+)|([A-Z]\w+\.t?\d+))((\.\d+)|([a-z](\.\d+)*))*(;|$)', name)
        if match:
            return match.group(2)
        return '-'


    def getAlias(self, name):
        match = re.search(r'(Alias=)([\w\-.]+)', name)
        if match:
            return match.group(2)
        return '-'


    def getBiotype(self, name):
        match = re.search(r'(biotype=)([\w\-]+);?', name)
        if match:
            return match.group(2)
        return '-'


    def getWBGene(self, name):
        match = re.search(r'(WBGene\d+);?', name)
        if match:
            return match.group(1)
        return '-'


    def parseWormbaseExon(self, data, gene2ivs={}, gene2info={}):
        avoid = {'intron', 'gene', 'mRNA'}
        gene2ivs = {}
        gene2info = {}
        seen = {}
        for curr in data:
            metadata = curr[-1]
            gene = self.getTranscriptGeneName(metadata)

            if gene not in gene2info:
                gene2info[gene] = {'chrom':curr[0], 'strand':curr[6], 'element':set([curr[2]])}

            else:
                gene2info[gene]['element'].add(curr[2])

            if 'Alias=' in metadata:
                alias = self.getAlias(metadata)
                if 'alias' not in gene2info[gene]:
                    gene2info[gene]['alias'] = set([alias])
                else:
                    gene2info[gene]['alias'].add(alias)
            if 'biotype=' in metadata:
                biotype = self.getBiotype(metadata)
                gene2info[gene]['biotype'] = biotype
            if 'WBGene' in metadata:
                wbgene = self.getWBGene(metadata)
                if 'wbgene' in gene2info[gene]:
                    gene2info[gene]['wbgene'].add(wbgene)
                else:
                    gene2info[gene]['wbgene'] = set([wbgene])


            if gene in gene2ivs:
                if curr[2] not in avoid:
                    gene2ivs[gene].append((int(curr[3])-1, int(curr[4])))
            else:
                if curr[2] not in avoid:
                    gene2ivs[gene] = [(int(curr[3])-1, int(curr[4]))]


        sub_elements = {'CDS', 'exon', 'five_prime_UTR', 'three_prime_UTR', 'nc_primary_transcript', 'pre_miRNA', 'miRNA_primary_transcript'}
        for curr in gene2info:
            if 'biotype' not in gene2info[curr]:
                diff = gene2info[curr]['element'] - sub_elements
                if isinstance(diff, str):
                    gene2info[curr]['biotype'] = diff
                else:
                    gene2info[curr]['biotype'] = ','.join(list(diff))

            if 'alias' not in gene2info[curr]:
                gene2info[curr]['alias'] = curr
            else:
                gene2info[curr]['alias'] = ','.join(list(gene2info[curr]['alias']))

            if 'wbgene' in gene2info[curr]:
                gene2info[curr]['wbgene'] = ','.join(list(gene2info[curr]['wbgene']))

        return gene2ivs, gene2info


    def getWormbaseData(self, file):
        commented = []
        data
        with open(file) as f:
            for row in f.readlines():
                if re.match("#", row):
                    commented.append(row.strip())
                else:
                    data.append(row.strip().split("\t"))
        return commented, data

    def getMergedSequence(self, interval, info, id2seq):
        merged_seq = ''
        for curr in interval:
            start, end, _ = curr
            merged_seq += id2seq[info['chrom']][start:end]
        return merged_seq if info['strand'] == '+' else self.revComp(merged_seq)


    def getChromosomLengths(commented):
        if len(commented) > 0:
            chrom2len = {}
            for line in commented:
                fields = line.split(" ")
                chrom2len[fields[1]] = int(fields[3])
            self.chrom2len = chrom2len
            return chrom2len
        else:
            return self.chrom2len


    def getMetaGenome(self):
        data, commented = self.getWormbaseData(self.file)
        chrom2len = self.getChromosomLengths(commented)
        gene2ivs, gene2info = self.parseWormbaseExon(data)

        gene2intervals = {}
        for gene in gene2ivs:
            curr = IntervalTree.from_tuples(gene2ivs[gene])
            curr.merge_overlaps()
            gene2info[gene]['interval'] = curr
            #gene2intervals[gene] = curr

            gene2info[gene]['start'] = curr.begin()
            gene2info[gene]['end'] = curr.end()

        return gene2info


    def getRangesFromTree(self, trees, k=10000, m=0):
        chroms = list(trees.keys())
        ranges = {chrom:{'+':[], '-':[]} for chrom in chroms}
        for chrom in trees:
            for strand in ['+', '-']:
                tree = trees[chrom][strand]
                for i in range(0, tree.end()+1, k):
                    ranges[chrom][strand].append([curr[-1] for curr in self.tree2json(tree.overlap(i-m, i+k+m))])
        return ranges


    def getBlocksFromTree(self, tree):
        #diameter of a semi-circle with given pixels: pixels*pi/2
        pixels = {'low':800, 'mid':1280, 'high':2880, 'ultra':5120}
        resolutions = {curr:pixels[curr]*3/2 for curr in pixels}
        arc_blocks = {curr:{} for curr in resolutions}
        chroms = list(tree.keys())

        for curr in arc_blocks:
            ranges_arc = {chrom:{'+':{}, '-':{}} for chrom in chroms}
            countd = {chrom:{'+':[], '-':[]} for chrom in chroms}
            count_tree = {chrom:{'+':None, '-':None} for chrom in chroms}
            for chrom in tree:
                chrom_len = chrom2len[chrom]
                block_size =  chrom_len//resolutions[curr]
                arc_blocks[curr][chrom] = self.getArcChromBlock(tree[chrom], chrom_len, block_size)
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


    def tree2json(self, tree, add_data=True):
        output = []
        for branch in tree:
            start, end, data = branch
            if add_data:
                output.append([start, end, data])
            else:
                output.append([start, end])
        return sorted(output)


    def getTrackData(self, gene2info):

        gene2intervals = {}
        interval2genes = {}
        interval2blocks = {}

        fields = ['chrom', 'start', 'end', 'strand', 'alias', 'biotype']
        gene2intervals = {curr:{**{'intervals':self.tree2json(gene2info[curr]['interval'], False)}, **{field:gene2info[curr][field] for field in fields}} for curr in gene2info}

        chroms = set([gene2info[gene]['chrom'] for gene in gene2info])
        chrom2intervals = {chrom:{'+':[], '-':[]} for chrom in chroms}

        for gene in gene2info:
            curr = gene2info[gene]
            chrom2intervals[gene2info[gene]['chrom']][gene2info[gene]['strand']].append([curr['start'], curr['end'], gene])

        chrom2trees = {}
        for chrom in chroms:
            chrom2trees[chrom] = {}
            for strand in ['+', '-']:
                chrom2trees[chrom][strand] = IntervalTree.from_tuples(chrom2intervals[chrom][strand])

        interval2genes = self.getRangesFromTree(chrom2trees)
        interval2blocks = self.getBlocksFromTree(chrom2trees)

        return gene2intervals, interval2genes, interval2blocks


    def generateTrackData(self, gene2info):
        tracks = []
        protein_coding = {gene:gene2info[gene] for gene in gene2info if gene2info[gene]['biotype']=='protein_coding'}
        gene2intervals, interval2genes, interval2blocks = self.getTrackData(protein_coding)
        tracks.append({'name':'protein coding', 'gene2intervals':gene2intervals, 'interval2genes':interval2genes, 'interval2blocks':interval2blocks})

        others = {gene:gene2info[gene] for gene in gene2info if gene2info[gene]['biotype']!='protein_coding'}
        gene2intervals, interval2genes, interval2blocks = self.getTrackData(others)
        tracks.append({'name':'others', 'gene2intervals':gene2intervals, 'interval2genes':interval2genes, 'interval2blocks':interval2blocks})

        return tracks
