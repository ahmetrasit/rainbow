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



class saveEnsemblData:

    def __init__(self, username, release, genome):
        self.username = username
        self.release = release
        self.genome = genome



    def createTemporaryFolder(self, username, keyword):
        #keyword = 'ensembl_download'
        target_dir = views.requestNewFolder(username, keyword)
        try:
            if not os.path.exists('data'):
                os.mkdir('data')
            if not os.path.exists('data/'+username):
                os.mkdir('data/'+username)
            if not os.path.exists('data/'+username+'/'+keyword):
                os.mkdir('data/'+username+'/'+keyword)
            if not os.path.exists(target_dir):
                os.mkdir(target_dir)
            return target_dir
        except Exception as e:
            print('Error:{} for {}'.format(e, target_dir))
            return None



    def buildEnsemblGenome(self):
        success = False
        given_task = 'buildEnsemblGenome({},{})'.format(self.release, self.genome)
        already_started = set([])#set([curr['request'] for curr in Task.objects.all().exclude(status = 'failed').values('request')])
        if given_task not in already_started:
            Task.objects.create(
                request = given_task,
                created_by = self.username
            )
            #try:
            path = '/pub/' + self.release + '/gff3/' + self.genome
            target_dir = self.createTemporaryFolder(self.username, 'ensembl_download')
            if target_dir:
                get_conn = geg3()
                path, gff3_list = get_conn.getGFFList(self.release, self.genome)
                full_path_list = []
                file_list = []
                print(len(gff3_list), 'files will be downloaded..')
                for file in gff3_list:
                    full_path, filename = get_conn.downloadGFF(file, target_dir)
                    full_path_list.append(full_path)
                    file_list.append(file)
                print('..download finished')

                success_1, bundle_pk_1, failed_files_1, chrom_list, source = self.buildEnsemblSubTrack(full_path_list, 'protein_coding', file_list, given_task)
                success_2, bundle_pk_2, failed_files_2, chrom_list, source = self.buildEnsemblSubTrack(full_path_list, 'other', file_list, given_task)

                SavedView.objects.create(
                            short_name = '{}-{}'.format(self.getGenomeShortName(self.genome), self.release) ,
                            description = 'Genes of {}, {} from {}'.format(self.getGenomeShortName(self.genome), self.release, source) ,
                            version = self.release,
                            organism = self.genome,
                            type = 'gene',
                            data_bundle_source = json.dumps(['{};{}'.format(bundle_pk_1, chrom_list[0]),'{};{}'.format(bundle_pk_2, chrom_list[0])]),
                            created_by = self.username
                )
                print('>> view is saved')

                return success_1 and success_2, [bundle_pk_1, bundle_pk_2], set(failed_files_1+failed_files_2)
            '''
            except Exception as e:
                print('error in some part', e)
                Task.objects.filter(request = given_task, created_by = self.username).update(status='failed')
                views.notifyUser(self.username, "Building {} from Ensembl {} is failed due to an error. Please contact admin for details.".format(self.genome, self.release))
            '''
        else:
            views.notifyUser(self.username, "{} from Ensembl {} is either not available, still processed, or already finished.".format(self.genome, self.release))

        return success, None, None


    def buildEnsemblSubTrack(self, full_path_list, biotype, file_list, given_task):
        parse_conn = peg3()
        success = False
        pks = []
        failed_files = []
        chromosome_list = []
        for index, full_path in enumerate(full_path_list):
            file = file_list[index]
            #try:
            c, gene2info, interval2genes, interval2blocks, rainbow2gene = parse_conn.getAllData(full_path, biotype)
            print(">s", c['chrom'])
            chromosome_list.append(c['chrom'])
            pk = self.saveChromosomeData(file, c['source'], c['chrom'], c['length'], gene2info, interval2genes, interval2blocks, rainbow2gene)
            pks.append(pk)
            Task.objects.filter(request = given_task, created_by = self.username).update(status='completed')
            '''
            except Exception as e:
                failed_files.append(file)
                print(e)
                traceback.print_tb(e.__traceback__)
                Task.objects.filter(request = given_task, created_by = self.username).update(status='not avaliable')
                views.notifyUser(self.username, "{} from {} has no defined chromosomes, sorry, it'll not be available for visualization.".format(file, self.genome))
            '''
        if len(pks)>0:
            bundle_pk = self.saveDataModelBundle(c['source'], pks, chromosome_list, biotype)
            for pk in pks:
                DataModel.objects.filter(pk=pk).update(data_model_bundle=bundle_pk)
            success = True
        else:
            bundle_pk = -1

        if len(failed_files) > 0:
            views.notifyUser(self.username, '{} from Ensembl {} is now ready for visualization with exceptions:{}'.format(self.genome, self.release, failed_files))
        else:
            views.notifyUser(self.username, '{} from Ensembl {} is now ready for visualization.'.format(self.genome, self.release))

        return success, bundle_pk, failed_files, chromosome_list, c['source']




    def saveChromosomeData(self, file, source, chromosome, chromosome_length, gene2info, interval2genes, interval2blocks, rainbow2gene):
        saved = DataModel.objects.create(
                    file = file,
                    chromosome = chromosome,
                    chromosome_length = chromosome_length,
                    gene2info = json.dumps(gene2info),
                    interval2genes = json.dumps(interval2genes),
                    interval2blocks = json.dumps(interval2blocks),
                    rainbow2gene = json.dumps(rainbow2gene)
        )
        return saved.pk



    def saveDataModelBundle(self, source, data_models, chromosome_list, biotype):
        saved = DataModelBundle.objects.create(
                    short_name = '{}-{}-{}'.format(biotype, self.release, self.getGenomeShortName(self.genome)) ,
                    description = '{} genes of {}, {} from {}'.format(biotype, self.getGenomeShortName(self.genome), self.release, source) ,
                    data_models = json.dumps(data_models),
                    chromosome_list = json.dumps(chromosome_list),
                    biotype = biotype,
                    source = source,
                    type = 'gene',
                    version = self.release,
                    organism = self.genome,
                    created_by = self.username
        )
        return saved.pk



    def getGenomeShortName(self, genome):
        fields = genome.split("_")
        return fields[0].upper()[0] + '. ' + fields[1]
