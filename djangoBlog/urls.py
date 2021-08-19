
from django.contrib import admin
from django.urls import path, include
from . import views
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

urlpatterns = [
    path('admin/', admin.site.urls),
    path('about/', views.About),
    path('', views.Home),
    path('articles/', include('articles.urls')),
]

urlpatterns += staticfiles_urlpatterns()
