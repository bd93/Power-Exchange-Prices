from django.shortcuts import render
from django.http import HttpResponse
import requests
import polling
from xmljson import badgerfish as bf
from xml.etree.ElementTree import fromstring
import json
from project.settings import SECURITY_TOKEN
# Create your views here.

def index(request):
    return HttpResponse(render(request, 'berza/index.html'))
