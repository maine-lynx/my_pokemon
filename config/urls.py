from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("pokedex/", include("pokedex.urls")),
    path("battles/", include("battles.urls")),
    path("", include("trainers.urls")),
    path("items/", include("items.urls")),
]
