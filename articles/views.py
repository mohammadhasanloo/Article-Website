from django.shortcuts import render, HttpResponse
from .import models

def articles_list(request):
    articles = models.Article.objects.all().order_by('date')

    args = {'articles':articles}
    return render(request, 'articles/articleslist.html', args)


def article_detail(request, slug):
    return HttpResponse(slug)
