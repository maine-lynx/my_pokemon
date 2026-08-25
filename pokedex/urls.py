# pokedex/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.pokedex_index, name='pokedex_index'),       # 图鉴列表
    path('<int:pokemon_id>/', views.pokedex_detail, name='pokedex_detail'),  # 详情
]