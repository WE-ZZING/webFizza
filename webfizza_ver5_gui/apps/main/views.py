from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
import os

def index(request):
    return render(request, 'main/home.html')

@csrf_exempt
def run_webfizza(request):
    if request.method == 'POST':
        mode = request.POST.get('mode')
        url = request.POST.get('url')
        file = request.FILES.get('file')

        # 데이터를 제대로 받고 있는지 로그 출력
        print(f"Received mode: {mode}, url: {url}, file: {file}")

        if mode == 'parsing' and url:
            data = {'mode': mode, 'url': url}
        elif mode == 'llm' and url and file:
            # 파일 경로를 서버에 저장하고 경로 사용
            file_path = f'/tmp/{file.name}'
            with open(file_path, 'wb+') as destination:
                for chunk in file.chunks():
                    destination.write(chunk)
            data = {'mode': mode, 'url': url, 'file_path': file_path}
        else:
            return JsonResponse({'success': False, 'error': 'Invalid data'}, status=400)

        # 데이터를 JSON 파일로 저장
        json_file_path = "/tmp/webfizza_input.json"
        try:
            with open(json_file_path, 'w') as json_file:
                json.dump(data, json_file)
            print(f"Data saved to {json_file_path}")
        except Exception as e:
            print(f"Failed to write JSON file: {e}")
            return JsonResponse({'success': False, 'error': 'Failed to save data'}, status=500)

        return JsonResponse({'success': True})

    return JsonResponse({'success': False, 'error': 'Invalid request'}, status=400)

