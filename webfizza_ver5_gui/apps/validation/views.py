from django.shortcuts import render
app_name = 'validation'

def index(request):
    return render(request, 'validation/validation.html')
