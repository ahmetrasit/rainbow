"""explorer URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.0/topics/http/urls/
"""

from django.conf.urls import include, url
from django.contrib import admin
from manager import views as manager_views
from django.contrib.auth import views as auth_views
from django.urls import path



urlpatterns = [
    path('admin/', admin.site.urls),
    url(r'^$', manager_views.homepage, name='homepage'),
    url(r'^config/main$', manager_views.editMainConfiguration, name='editMainConfiguration'),
    url(r'^add/user$', manager_views.addUser, name='addUser'),
    url(r'^get/latestView/$', manager_views.getLatestView, name='getLatestView'),
    url(r'^get/bundle/([\w:]+)/$', manager_views.getBundleData, name='getBundleData'),
    url(r'^get/arc/([\w:;]+)/$', manager_views.getArcData, name='getArcData'),
    url(r'^get/track/(\d+)/$', manager_views.getTrackData, name='getTrackData'),

    url(r'^get/release/$', manager_views.getEnsemblReleaseList, name='getEnsemblReleaseList'),
    url(r'^get/genome/([\w_-]+)$', manager_views.getEnsemblGenomeList, name='getEnsemblGenomeList'),
    url(r'^build/ensembl/([\w_-]+)/([\w_-]+)$', manager_views.buildEnsemblGenome, name='buildEnsemblGenome'),
    url(r'^get/gene_views/$', manager_views.getSavedGeneViews, name='getSavedGeneViews'),
    url(r'^get/all_views/$', manager_views.getSavedAllViews, name='getSavedAllViews'),



    #url(r'^login/$', auth_views.LoginView, {'template_name': 'homepage.html'}),
    url(r'^login/$', auth_views.LoginView.as_view(template_name='homepage.html'), name='login'),
    url(r'^upload/$', manager_views.upload, name='upload'),
    url(r'^logout/$', auth_views.LogoutView.as_view(), name='logout'),
]
