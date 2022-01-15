import math
import time
import json
import os
from copy import deepcopy as copy

from django.http import HttpResponseRedirect
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.views import generic
from django.utils import timezone
from django.db.models import Max

import pandas as pd
from asteval import Interpreter
import requests


# I'm using these functions to standardize the objects I send to the template and to populate default values.
def textd(value='', style=''):  # for generating text JSON objects for the template
    return {'value': str(value), 'style': style}


def imaged(url='https://www.freeiconspng.com/uploads/red-circular-image-error-0.png', width='30', height='30',
           onerror='', style='', title=''):  # for generating image JSON objects for the template
    return {'url': url, 'width': width, 'height': height, 'onerror': onerror, 'title': title, 'style': style}


# page-returning methods referenced in urls    
def test(request):
    return render(request, 'personal/test.html')


def index_view(request):
    if request.method == 'POST':
        c = open("c.txt", "w")
        aeval = Interpreter(writer=c)

        try:
            torun = request.POST.get('torun')
            print(torun)
            aeval(torun)
            c.close()
            c = open("c.txt", "r")
            rax = '\n'
            rax = rax.join(c.readlines())
            return render(request, 'personal/index.html', {'error': '', 'return': str(rax)})
            c.close()
        except Exception as e:
            c.close()
            error = e
            return render(request, 'personal/index.html', {'error': str(e), 'return': ''})

        return render(request, 'personal/index.html', {'error': str(e), 'return': str(rax)})

        dest = request.POST['dest']
        return HttpResponseRedirect('/user/' + dest)

    return render(request, 'personal/index.html')


def code(request):
    return render(request, 'personal/code.html', {})


def ide(request):
    if request.method == 'POST':
        c = open("c.txt", "w")
        aeval = Interpreter(writer=c)

        try:
            torun = request.POST.get('torun')
            print(torun)
            aeval(torun)
            c.close()
            c = open("c.txt", "r")
            rax = '\n'
            rax = rax.join(c.readlines())
            c.close()
            return render(request, 'personal/ide.html', {'error': '', 'return': str(rax)})

        except Exception as e:
            c.close()
            error = e
            return render(request, 'personal/ide.html', {'error': str(e), 'return': ''})

    return render(request, 'personal/ide.html')


def run(request):
    f = open("f.txt", "w")
    aeval = Interpreter(writer=f)

    try:
        torun = request.GET.get('torun')
        print(torun)
        aeval(torun)
        f.close()
        f = open("f.txt", "r")
        rax = '\n'
        rax = rax.join(f.readlines())
        response = HttpResponse()
        try:
            er = aeval.error[0].get_error()
        except:
            er = ''
        response.content = json.dumps({'error': er, 'return': str(rax)})
        print(response.content)
        return response
        f.close()
    except Exception as e:
        f.close()
        error = e
        response = HttpResponse()
        response.content = json.dumps({'error': str(e), 'return': ''})
        print(response.content)
        return response
