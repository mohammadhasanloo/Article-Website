from django.shortcuts import render

from articles.models import Article

LATEST = 3


def home(request):
    return render(request, "home.html", {"latest": Article.objects.all()[:LATEST]})


def about(request):
    return render(request, "about.html")
