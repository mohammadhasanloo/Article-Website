from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, render

from .models import Article

PER_PAGE = 5


def articles_list(request):
    """Every article, newest first, five to a page, filtered by ?q= if given."""
    articles = Article.objects.select_related("author")

    query = request.GET.get("q", "").strip()
    if query:
        articles = articles.filter(Q(title__icontains=query) | Q(body__icontains=query))

    page = Paginator(articles, PER_PAGE).get_page(request.GET.get("page"))
    return render(
        request,
        "articles/list.html",
        {"page": page, "query": query, "total": articles.count()},
    )


def article_detail(request, slug):
    """One article, with links to the ones either side of it in time."""
    article = get_object_or_404(Article.objects.select_related("author"), slug=slug)
    return render(
        request,
        "articles/detail.html",
        {
            "article": article,
            "newer": Article.objects.filter(published__gt=article.published).last(),
            "older": Article.objects.filter(published__lt=article.published).first(),
        },
    )
