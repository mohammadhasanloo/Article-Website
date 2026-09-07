from django.contrib import admin

from .models import Article


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ("title", "author", "published", "reading_time")
    list_filter = ("published", "author")
    search_fields = ("title", "body")
    date_hierarchy = "published"
    # Typing the slug by hand is how two articles end up sharing one.
    prepopulated_fields = {"slug": ("title",)}
