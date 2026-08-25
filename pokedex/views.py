from django.shortcuts import render,HttpResponse


# Create your views here.
def pokedex_index(request):
    return HttpResponse("宝可梦图鉴打开了")

def pokedex_detail(request):
    return HttpResponse("这是宝可梦详情页")