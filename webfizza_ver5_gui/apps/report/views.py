from django.shortcuts import render
from django.http import HttpResponse
from django.conf import settings
import os

app_name = 'report'
def index(request):
    return render(request, 'report/report.html')
    
def get_md_file(request):
    file_path = os.path.join(settings.MD_FILES_DIR, "report.md")
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")  # 디버그 메시지
        return HttpResponse("File not found", status=404)

    try:
        with open(file_path, "r", encoding="utf-8") as file:
            content = file.read()
        return HttpResponse(content, content_type="text/plain")
    except Exception as e:
        print(f"Error reading file: {e}")  # 디버그 메시지
        return HttpResponse("Error reading file", status=500)
