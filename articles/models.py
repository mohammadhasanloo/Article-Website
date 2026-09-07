from django.contrib.auth.models import User
from django.db import models
from django.urls import reverse
from django.utils import timezone

SNIPPET_LENGTH = 180
WORDS_PER_MINUTE = 200


class Article(models.Model):
    """One post."""

    title = models.CharField(max_length=100)
    # Unique because the slug is the address. Two articles sharing one would
    # make the detail view a coin toss over which is served.
    slug = models.SlugField(unique=True)
    body = models.TextField()
    published = models.DateTimeField(default=timezone.now)
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="articles", null=True, blank=True
    )

    class Meta:
        # Newest first, set here rather than in each view, so a query written
        # somewhere new cannot quietly come back in insertion order.
        ordering = ["-published"]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("articles:detail", kwargs={"slug": self.slug})

    def snippet(self):
        """The opening of the body, for the list view.

        Cut at a word boundary so the preview does not end mid-word, and with
        no trailing ellipsis when the whole body already fits.
        """
        if len(self.body) <= SNIPPET_LENGTH:
            return self.body
        cut = self.body[:SNIPPET_LENGTH]
        return cut[: cut.rfind(" ")] + "..."

    def reading_time(self):
        """Whole minutes, rounded up, never zero."""
        return max(1, -(-len(self.body.split()) // WORDS_PER_MINUTE))
