from django.shortcuts import render ,HttpResponse

# Create your views here.
def trainer_profile(request):
    return HttpResponse("这是一个训练家页面")