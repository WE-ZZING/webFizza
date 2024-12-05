# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from django import template
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect
from django.template import loader
from django.urls import reverse
from django.shortcuts import render
import random
import json
import os
import hashlib
from django.http import JsonResponse

app_name = 'home'

def index(request):
    return render(request, "home/index.html")
 
def get_datapoints(request):
    default_query_params = { "xstart": 0, "ystart": 0, "length": 1 }
    query_params = { **default_query_params, **request.GET.dict() };
    y = int(query_params["ystart"]);
    datapoints = []
 
    for i in range(int(query_params["length"])):
        y += round(5 + random.random() * (-1, 1))
        datapoints.append({ "x": (int(query_params["xstart"]) + i), "y": y})
    
    return HttpResponse(json.dumps(datapoints), content_type="application/json")  
  
def check_validation_status(request):
    status_file_path = "/tmp/validation_status.json"
    hash_file_path = "/tmp/validation_status_hash.txt"

    if os.path.exists(status_file_path):
        with open(status_file_path, "r") as status_file:
            try:
                status_data = json.load(status_file)
                # 현재 데이터의 해시 생성
                current_hash = hashlib.md5(json.dumps(status_data, sort_keys=True).encode()).hexdigest()

                # 이전 해시 값을 파일에서 읽어오기
                previous_hash = None
                if os.path.exists(hash_file_path):
                    with open(hash_file_path, "r") as hash_file:
                        previous_hash = hash_file.read().strip()

                # 상태가 변경되었을 때만 리턴 수행
                if previous_hash != current_hash:
                    # 해시 값을 파일에 저장
                    with open(hash_file_path, "w") as hash_file:
                        hash_file.write(current_hash)
                    if status_data.get("status") == "validation_complete":
                        return JsonResponse({"status": "completed"})

            except json.JSONDecodeError:
                pass

    return JsonResponse({"status": "in_progress"})

def check_validation_status(request):
    status_file_path = "/tmp/report.json"
    hash_file_path = "/tmp/report.txt"

    if os.path.exists(status_file_path):
        with open(status_file_path, "r") as status_file:
            try:
                status_data = json.load(status_file)
                # 현재 데이터의 해시 생성
                current_hash = hashlib.md5(json.dumps(status_data, sort_keys=True).encode()).hexdigest()

                # 이전 해시 값을 파일에서 읽어오기
                previous_hash = None
                if os.path.exists(hash_file_path):
                    with open(hash_file_path, "r") as hash_file:
                        previous_hash = hash_file.read().strip()

                # 상태가 변경되었을 때만 리턴 수행
                if previous_hash != current_hash:
                    # 해시 값을 파일에 저장
                    with open(hash_file_path, "w") as hash_file:
                        hash_file.write(current_hash)
                    if status_data.get("status") == "report_complete":
                        return JsonResponse({"status": "completed"})

            except json.JSONDecodeError:
                pass

    return JsonResponse({"status": "in_progress"})


def pages(request):
    context = {}
    # All resource paths end in .html.
    # Pick out the html file name from the url. And load that template.
    try:

        load_template = request.path.split('/')[-1]

        if load_template == 'admin':
            return HttpResponseRedirect(reverse('admin:index'))
        context['segment'] = load_template

        html_template = loader.get_template('home/' + load_template)
        return HttpResponse(html_template.render(context, request))

    except template.TemplateDoesNotExist:

        html_template = loader.get_template('home/page-404.html')
        return HttpResponse(html_template.render(context, request))

    except:
        html_template = loader.get_template('home/page-500.html')
        return HttpResponse(html_template.render(context, request))



