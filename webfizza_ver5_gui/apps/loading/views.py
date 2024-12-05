#views.py
# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from django.shortcuts import render
from django.http import JsonResponse
import json
import os
import hashlib

last_known_hash = None  # 이전에 읽은 파일의 해시 값을 저장하기 위한 변수

def index(request):
    return render(request, 'loading/loading.html')

def calculate_file_hash(file_path):
    """파일 내용을 읽어 해시를 계산하는 함수"""
    with open(file_path, "rb") as f:
        file_content = f.read()
        return hashlib.md5(file_content).hexdigest()
def check_status(request):
    status_file_path = "/tmp/fuzz_status.json"
    hash_file_path = "/tmp/fuzz_status_hash.txt"

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

                # 상태가 변경되었을 때만 리디렉션 수행
                if previous_hash != current_hash:
                    # 해시 값을 파일에 저장
                    with open(hash_file_path, "w") as hash_file:
                        hash_file.write(current_hash)
                    if status_data.get("status") == "running":
                        return JsonResponse({"status": "completed"})

            except json.JSONDecodeError:
                pass

    return JsonResponse({"status": "in_progress"})
