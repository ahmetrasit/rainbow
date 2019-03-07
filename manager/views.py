from django.shortcuts import render, render_to_response
from django.forms.models import model_to_dict
from django.contrib.auth import authenticate
from django.contrib.auth import login as auth_login
from django.contrib.auth import logout as auth_logout
from django.http import HttpResponseRedirect, HttpResponse
from django.contrib.auth.decorators import login_required
from django.core import serializers
from django.views.decorators.csrf import csrf_exempt, csrf_protect

from django.http import JsonResponse
from .requestHandler import requestHandler as rh
from django.db.models import Q

from .parseWormBaseGeneModel import parseWormBaseGeneModel as pWBgm
from .getEnsemblGFF3 import getEnsemblGFF3 as geg3
from .parseEnsemblGFF3 import parseEnsemblGFF3 as peg3
from .saveEnsemblData import saveEnsemblData as sed
from .processBEDFile import processBEDFile as pbf
from .saveTrackFromExisting import saveTrackFromExisting as stfe

from .models import *

from .forms import *
import datetime
import pandas as pd
import os
import re
import time
import random
import json
import html
import xmltodict
import math
from threading import Thread



def homepage(request):
    render_dict = getConfigDict(request)
    #getAllData(request)
    return render(request, 'homepage.html', render_dict)


def requestNewFolder(username, type):
    #temp:temporary, perm:permanent
    curr_time = int(time.time())
    rand_num = random.randint(111111,999999)
    folderName = 'data/{}/{}/{}_{}/'.format(username, type, curr_time, rand_num)

    return folderName


@login_required
def addUser(request):
    render_dict = getConfigDict(request)
    form = AddUserForm
    render_dict['form']=form()
    if request.method == 'POST':
        formInput = form(request.POST)
        if formInput.is_valid():
            if createSystemUser(formInput.cleaned_data["username"]):
                formInput.save()
                message = 'User successfully added'
            else:
                message = "cannot create system user"
        else:
            message = 'Cannot create user.'
        render_dict['message'] = message
        render_dict['form']=formInput

    users_fields = ['username', 'role', 'credit', 'score']
    render_dict['users'] = CustomUser.objects.exclude(username='admin').values(*users_fields)[::-1]
    render_dict['users_fields'] = users_fields
    return render(request, 'addUser.html', render_dict)



def createSystemUser(username):
    return True

@login_required
def buildEnsemblGenome(request, release, genome):
    #print(release, genome)
    Thread(target=startBuildingEnsemblGenome, args=(request.user, release, genome)).start()
    return JsonResponse([release, genome, 'started'], safe=False)


def startBuildingEnsemblGenome(user, release, genome):
    username = user.username
    save = sed(username, release, genome)
    success, saved_pks, failed_files = save.buildEnsemblGenome()
    print('sbeg', success, saved_pks, failed_files)





def notifyUser(username, message):
    print(username, message)



@login_required
def editMainConfiguration(request):
    try:
        last = model_to_dict(MainConfiguration.objects.last())
        del last['id']
    except:
        last = None
    render_dict = getConfigDict(request)
    form = MainConfigurationForm
    render_dict['form']=form(initial=last)
    if request.method == 'POST':
        formInput = form(request.POST)
        if formInput.is_valid():
            if not last == formInput.cleaned_data:
                formInput.save()
                message = 'Main configuration successfully updated.'
            else:
                message = 'Nothing changed from previous state.'
        else:
            message = 'Input parameters are not valid, please check.'
        render_dict['message'] = message
    try:
        last = model_to_dict(MainConfiguration.objects.last())
    except:
        last=None
    render_dict['form']=form(initial=last)
    render_dict['configs'] = serializers.serialize('python', MainConfiguration.objects.all())[::-1]
    return render(request, 'configMain.html', render_dict)


def processAndSaveData(target, file, short_name, description, username, post_dict):
    processFunctions = {'GeneModel':processWormBaseGeneModel, 'BEDFiles':processBEDFile}
    if target in processFunctions:
        return processFunctions[target](file, short_name, description, username, post_dict)
    return 'Error, function not found'


def processBEDFile(filename, short_name, description, username, post_dict):
    release = post_dict['genome_release']
    print('release', filename, release)
    data = pbf(filename, release, short_name, description, username)
    data.buildData()
    print('data built')




def processWormBaseGeneModel(filename, short_name, description, username, post_dict):
    model = pWBgm(filename)
    gene2info = model.getMetaGenome()
    #gene2intervals, interval2genes, interval2blocks = model.getTrackData(gene2info)
    curr_time = time.time()
    tracks = model.generateTrackData(gene2info)
    curr_time = time.time()
    pks = []
    for curr in tracks:
        pk = saveData(DataModel, filename, 'gene_model', curr['name'] + "-" + short_name, description, curr['gene2intervals'], curr['interval2genes'], curr['interval2blocks'], username)
        pks.append(int(pk))

    SavedView.objects.create(
                short_name = short_name,
                description = description,
                track_sources = json.dumps(pks),
                created_by = username
    )



@login_required
def getLatestView(request):
    username = request.user.username
    track_sources = None
    try:
        latest = SavedView.objects.filter( Q(access='public') | Q(created_by=username) ).last()
        #print(latest.data_bundle_source)
        track_sources = latest.data_bundle_source
        pk = latest.pk
    except:
        track_sources = '[]'

    return JsonResponse([pk, json.loads(track_sources)], safe=False)


@login_required
def getSavedGeneViews(request):
    username = request.user.username
    #print(username)
    saved_views = SavedView.objects.filter( (Q(access='public') | Q(created_by=username)) &  Q(type='gene')).values('pk', 'short_name', 'description', 'version', 'organism', 'data_bundle_source', 'created_by')
    #df = pd.DataFrame(list(saved_views)).sort_values(['organism', 'version', 'short_name'])

    return JsonResponse(list(saved_views), safe=False)


@login_required
def getSavedAllViews(request):
    username = request.user.username
    #print(username)
    saved_views = SavedView.objects.filter( (Q(access='public') | Q(created_by=username)) ).values('pk', 'short_name', 'description', 'version', 'organism', 'data_bundle_source', 'created_by')
    #df = pd.DataFrame(list(saved_views)).sort_values(['organism', 'version', 'short_name'])

    return JsonResponse(list(saved_views), safe=False)




@login_required
def getArcData(request, bundle_chrom):
    bundle, chrom = bundle_chrom.split(";")
    curr = DataModel.objects.filter(data_model_bundle=int(bundle), chromosome=chrom).values('id', 'interval2blocks', 'chromosome', 'data_model_bundle')
    info = DataModelBundle.objects.filter(pk=int(bundle)).values('short_name', 'description', 'version', 'organism', 'chromosome_list', 'biotype')
    #print(list(info)[0])
    return JsonResponse({**list(curr)[0], **list(info)[0]}, safe=False)


@login_required
def getBundleData(request, bundle):
    info = DataModelBundle.objects.filter(pk=int(bundle)).values('global_gene2info')
    return JsonResponse({**list(info)[0]}, safe=False)

@login_required
def getTrackData(request, track_pk):
    curr = DataModel.objects.filter(pk=track_pk).values('gene2info', 'interval2genes', 'rainbow2gene', 'chromosome_length')
    #print(list(curr)[0])
    return JsonResponse({**list(curr)[0]}, safe=False)


@login_required
def getEnsemblReleaseList(request):
    conn = geg3()
    return JsonResponse(conn.getReleaseList(), safe=False)


@login_required
def getEnsemblGenomeList(request, release):
    conn = geg3()
    return JsonResponse(conn.getOrganismList(release), safe=False)


@login_required
def createNewTrack(request):
    results = json.loads(request.POST['found'])
    curr_bundles = json.loads(request.POST['curr_bundles'])
    keyword = json.loads(request.POST['keyword'])
    #curr = DataModel.objects.filter(data_model_bundle=int(bundle), chromosome=chrom).values('id', 'interval2blocks', 'chromosome', 'data_model_bundle')

    #print(results)
    bundle2gene = {}
    for gene, bundle_pk, r_id, chrom in results:
        try:
            bundle2gene[bundle_pk][chrom].append([gene, r_id])
        except:
            if bundle_pk not in bundle2gene:
                bundle2gene[bundle_pk] = {}
                bundle2gene[bundle_pk][chrom] = [[gene, r_id]]
            else:
                bundle2gene[bundle_pk][chrom] = [[gene, r_id]]
    new_track = stfe(request.user.username, bundle2gene, curr_bundles, keyword)
    new_pk = new_track.createNewDataModelFromExisting()



        #filter datamodel by bundle_pk and chrom, find the gene, gather all
        #then send for formatting and saving

    return HttpResponse('adsf')


@login_required
def upload(request):
    success = False
    if request.method == 'POST':
        #names = request.POST.keys()
        #for name in names:
        #    print('>', name, request.POST[name])

        target = request.POST['target'].replace('add', '')
        short_name = request.POST['short_name']
        description = request.POST['description']
        #print('request.POST', request.POST.keys())


        upload_folder = 'data/' + request.user.username + '/' + target + '/'+ str(datetime.datetime.now().strftime('%Y-%m-%d_%H%M')) + '/'
        uploaded_files = request.FILES.getlist('filesToUpload')
        filenames = [upload_folder + str(file) for file in uploaded_files]
        for i in range(len(uploaded_files)):
            file = uploaded_files[i]
            filename =  str(file)
            if handle_uploaded_file(file, filename, target, upload_folder, request.user.username):
                processAndSaveData(target, upload_folder + filename, short_name, description, request.user.username, request.POST)

    return HttpResponse()


@csrf_exempt
def handle_uploaded_file(f, filename, target, foldername, username):
    try:
        if not os.path.exists('data'):
            print('create main data folder')
            os.mkdir('data')
        if not os.path.exists('data/'+username):
            print('create user data subfolder', 'data/'+username)
            os.mkdir('data/'+username)
        if not os.path.exists('data/'+username+'/'+target):
            print('create data target subfolder', 'data/'+username+'/'+target)
            os.mkdir('data/'+username+'/'+target)
        if not os.path.exists(foldername):
            print('now, folder', foldername)
            os.mkdir(foldername)
    except Exception as e:
        if '[Errno 17]' not in str(e):
            print('Error:{} for {}'.format(foldername, e))
    try:
        with open(foldername + filename, 'wb+') as destination:
            for chunk in f.chunks():
                destination.write(chunk)
        return True
    except Exception as e:
        print('Error:{} for {}'.format(filename, e))
        return False


def getConfigDict(request):
    render_dict = {'user':request.user, 'no_of_samples':0}
    last = MainConfiguration.objects.last()
    if last:
        system_config = model_to_dict(last)
        for key in ['team_name', 'intro_message']:
            render_dict[key] = system_config[key]
    return render_dict




@login_required
def getAllData(request):
    username = request.user.username
    role = request.user.role
    filelist = []
    folders = []
    if role == 'limited':
        folders = [[username, folder] for folder in os.listdir('data/'+username)]
        for path in folders:
            filelist += [[username, path[1], file] for file in os.listdir('data/'+ '/'.join(path))]
    elif role == 'unlimited':
        for curr_user in os.listdir('data'):
            folders += [[curr_user, folder] for folder in os.listdir('data/'+curr_user)]
        for path in folders:
            filelist += [[path[0], path[1], file] for file in os.listdir('data/'+ '/'.join(path))]
    else:
        pass
    output = {}
    for file in filelist:
        curr_file = 'data/' + '/'.join(file)
        output[curr_file] = parseMicrun(curr_file)
    return JsonResponse(json.dumps(output), safe=False)
