from django.contrib import admin
from django.urls import include, path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("about/", views.about, name="about"),
    path("articles/", include("articles.urls")),
    path("admin/", admin.site.urls),
]
