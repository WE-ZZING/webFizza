from django.shortcuts import render
from django.http import HttpResponse
from django.conf import settings
import os

app_name = 'patch'

def index(request):
    return render(request, 'patch/patch.html')

def get_md_file(request, filename):
    valid_files = ['patch.md', 'privacy.md']  # 허용된 파일 이름 목록
    if filename not in valid_files:
        return HttpResponse("Invalid file name", status=400)
    
    file_path = os.path.join(settings.MD_FILES_DIR, filename)
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")  # 디버그 메시지
        return HttpResponse("File not found", status=404)

    try:
        with open(file_path, "r", encoding="utf-8") as file:
            content = file.read()
        # Content-Type에 charset=utf-8 추가
        return HttpResponse(content, content_type="text/plain; charset=utf-8")
    except Exception as e:
        print(f"Error reading file: {e}")  # 디버그 메시지
        return HttpResponse("Error reading file", status=500)

