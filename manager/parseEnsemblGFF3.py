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


class parseEnsemblGFF3:

    def __init__(self):
        self.genome = None
        self.version = None
        self.chrom2len = None



    def getAllData(self, file, biotype):
        #file = os.getcwd() + '/' + file
        c, genes = self.getParsedGFF(file)
        if c:
            #print('p>', c)
            print('getParsedGFF', c['chrom'])
            gene2info = self.getGene2Info(genes)
            if biotype=='protein_coding':
                gene2info = {gene:gene2info[gene] for gene in gene2info if gene2info[gene][0]['annot']['biotype']=='protein_coding'}
            if biotype=='other':
                gene2info = {gene:gene2info[gene] for gene in gene2info if gene2info[gene][0]['annot']['biotype']!='protein_coding'}
            #print('p> len gene2info', biotype, len(gene2info))
            interval2genes, interval2blocks, rainbow2gene = self.getTrackData(c, gene2info)
            #print('p>', len(interval2genes))
            return c, gene2info, interval2genes, interval2blocks, rainbow2gene
        else:
            return None


    def revComp(self, seq):
        nts = 'AGNCT'
        pairs = {nts[i]:nts[4-i] for i in range(5)}
        return ''.join([self.pairs[nt] for nt in seq][::-1])


    def parseInfo(self, line, info):
        fields = re.split(r'\s+', line.strip()[2:])
        info[fields[0]] = fields[-1]
        return info


    def getGenes(self, file):
        with open(file) as f:
            chrom_info = {}
            gene2info = {}
            genes = [[]]
            types = []

            beginning = False
            second = False
            for line in f.readlines():
                if re.match("#", line) and '###' not in line:
                    chrom_info = self.parseInfo(line, chrom_info)

                else:
                    if re.match('###', line):
                        genes.append([])
                    else:
                        if '.\tbiological_region' not in line:
                            genes[-1].append(line.strip().split("\t"))
        return genes


    def parseGene(self, data, index):
        if len(data)>0:
            annotation = data[0]
            parts = []
            for line in data[1:]:
                chrom, source, subtype, start, end, _, strand, _, meta = line
                if subtype != 'CDS':
                    if 'Parent=gene:' in meta:
                        parts.append([])
                        parts[-1].append([chrom, source, subtype, int(start), int(end)+1, strand, meta])
                    else:
                        parts[-1].append([chrom, source, subtype, int(start), int(end)+1, strand])

            return {'annot':self.parseAnnotation(annotation, index), 'parts':self.parseParts(parts)}
        return {}


    def parseParts(self, parts):
        type2elements = {}
        for part in parts:
            annot = part[0]
            biotype = self.getBiotype(annot[-1])
            if biotype not in type2elements:
                type2elements[biotype] = []

            for row in part[1:]:
                type2elements[biotype].append([row[k] if k!=2 else row[k][:1] for k in [3,4,2]])
        return type2elements


    def parseAnnotation(self, annot, index):
        chrom, source, subtype, start, end, _, strand, _, meta = annot
        if subtype == 'chromosome':
            return {'chrom':chrom,
                    'source':source,
                    'subtype':subtype,
                    'length':int(end)
                   }
        else:
            return {'chrom':chrom,
                    'source':source,
                    'subtype':subtype,
                    'strand':strand,
                    'id':self.getID(meta),
                    'r_id':index,    #rainbow id
                    'name':self.getName(meta),
                    'meta':self.getName(meta),
                    'biotype':self.getBiotype(meta),
                    'gene_id':self.getGeneID(meta),
                    'description':self.getDescription(meta)
                   }


    def getID(self, meta):
        match = re.search(r'ID=gene:(\w+);', meta)
        if match:
            return match.group(1)
        else:
            return '-'


    def getName(self, meta):
        match = re.search(r';Name=([\w.-]+);', meta)
        if match:
            return match.group(1)
        else:
            return '-'


    def getGeneID(self, meta):
        match = re.search(r';gene_id=([\w.]+);', meta)
        if match:
            return match.group(1)
        else:
            return '-'


    def getBiotype(self, meta):
        match = re.search(r';biotype=(\w+);', meta)
        if match:
            return match.group(1)
        else:
            return '-'

    def getDescription(self, meta):
        match = re.search(r';description=([^;]+?)(\s+\[Source[^]]+\])*;', meta)
        if match:
            return match.group(1)
        else:
            return '-'


    def getParsedGFF(self, file):
        genes = self.getGenes(file)
        output = []
        chrom_annot = None
        for index, gene in enumerate(genes):
            parsed = self.parseGene(gene, index)
            if len(parsed)>0:
                if parsed['annot']['subtype'] == 'chromosome':
                    chrom_annot = parsed['annot']
                else:
                    output.append(parsed) if len(parsed)>0 else None
        return chrom_annot, output


    def getGene2Info(self, genes):
        gene2info = {}

        for rainbow_id, gene in enumerate(genes):
            gene_id = gene['annot']['gene_id']
            #curr_info = gene2info[gene_id]
            curr_info = {'r_id':rainbow_id}

            curr_info['annot'] = {key:gene['annot'][key] for key in gene['annot'] if key != 'gene_id'}
            curr_info['interval'] = {}
            for subtype in gene['parts']:
                curr_tree = IntervalTree.from_tuples([curr[:2] for curr in gene['parts'][subtype]])
                curr_tree.merge_overlaps()
                curr_info['interval'][subtype]= curr_tree
                curr_info['annot']['start'] = curr_tree.begin()
                curr_info['annot']['end'] = curr_tree.end()

            try:
                gene2info[gene_id].append(curr_info)
            except:
                gene2info[gene_id] = [curr_info]


        return gene2info


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
            chrom_len = chrom['length']
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


    def getRangesFromTree(self, chrom, trees, k=10000, m=0):
        ranges = {'+':[], '-':[]}
        for strand in ranges:
            tree = trees[strand]
            for i in range(0, chrom['length']+1, k):
                ranges[strand].append([curr[-1] for curr in self.tree2json(tree.overlap(i-m, i+k+m))])
        return ranges


    def getTrackData(self, c, gene2info):
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

        interval2genes = self.getRangesFromTree(c, trees)
        interval2blocks = self.getBlocksFromTree(c, trees)

        return interval2genes, interval2blocks, rainbow2gene
