"""Fill an empty database with articles so the blog has something to show."""

from datetime import timedelta

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.utils import timezone

from articles.models import Article

AUTHOR = {"username": "mohammad", "first_name": "Mohammad", "last_name": "GharehHasanloo"}

ARTICLES = [
    (
        "Why the slug has to be unique",
        "why-the-slug-has-to-be-unique",
        """The slug is the address. It is what appears after /articles/, and it is
what the detail view looks the article up by.

If two articles share a slug, the lookup matches both and the view returns
whichever the database happens to hand back first. Nothing raises, nothing is
logged, and the second article becomes unreachable through a URL that looks
exactly like the one that works.

A unique constraint on the column turns that into an error at the point the
second article is saved, where somebody is looking. The admin also fills the
slug in from the title, because typing it by hand is how the collision gets
created in the first place.""",
    ),
    (
        "Ordering belongs on the model, not in the view",
        "ordering-belongs-on-the-model",
        """A view that ends with order_by('-published') is correct until somebody
writes a second view.

The second one is usually a filter, or a related lookup, or a queryset built
somewhere that never thought about ordering at all, and it comes back in
whatever order the database found convenient. On a small table that is often
insertion order, which looks sorted, so the bug ships and shows up later on a
table large enough for the query planner to make a different choice.

Meta.ordering states it once, on the thing being ordered. Every query starts
from it, and a view that wants something else has to say so explicitly, which
is the right way round.""",
    ),
    (
        "The secret key does not belong in the repository",
        "the-secret-key-does-not-belong-in-the-repository",
        """Django generates SECRET_KEY into settings.py, and settings.py is the file
everybody commits.

The key signs sessions and password reset tokens. Anyone holding it can forge
either. Once it has been pushed it is in the history, in every clone, and in
whatever mirrors the host keeps, so rotating it is the only real fix and
deleting the line is not.

Reading it from the environment costs one line. The fallback in this project is
a development-only value, and Django refuses to serve with DEBUG off unless a
real one is supplied, so a deployment that forgets to set it fails loudly
rather than quietly running on a key that is public.""",
    ),
    (
        "Pagination is not just a page parameter",
        "pagination-is-not-just-a-page-parameter",
        """Paginator turns a queryset into pages, and get_page turns a request
parameter into one of them without raising on the two inputs users actually
send: a page number past the end, and a value that is not a number at all.

The part worth attention is the links. A paginated list with a search box has
two pieces of state, and a next-page link that carries only the page number
drops the search on the way. The template has to put both back into the query
string, which is why the link is built rather than hardcoded.""",
    ),
    (
        "select_related, and the query you did not write",
        "select-related-and-the-query-you-did-not-write",
        """A list of ten articles that each show their author runs eleven queries: one
for the articles, and one per article when the template touches article.author.

Nothing in the template looks like a query. It looks like an attribute. That is
the whole difficulty with the pattern: the cost is invisible at the place it is
paid, and it grows with the length of the list rather than with the complexity
of the code.

select_related('author') joins the two tables in the first query and the
attribute access is free. It is one word, and it is the difference between one
query and eleven.""",
    ),
    (
        "Snippets should cut on a word",
        "snippets-should-cut-on-a-word",
        """body[:180] is a preview until it lands in the middle of a word, and then it
is a preview that looks broken.

Cutting back to the last space costs one call and reads better every time. The
other half is the ellipsis: appending one unconditionally means an article
shorter than the cut ends in three dots that promise text which does not
exist.""",
    ),
    (
        "get_object_or_404 over a manual check",
        "get-object-or-404-over-a-manual-check",
        """A detail view that fetches by slug has to decide what happens when the slug
matches nothing.

Doing it by hand means a try, an except on DoesNotExist, and a raise of Http404
that has to be imported. Four lines, and the failure mode when they are skipped
is a 500 with a stack trace where a 404 belonged.

get_object_or_404 is the same behaviour in one call, and it reads as what it
does. The template for the 404 is worth writing too, because the default one
is a white page with a sentence on it, and a reader who mistyped an address
deserves a link back to the index.""",
    ),
    (
        "Templates that do not extend anything",
        "templates-that-do-not-extend-anything",
        """A project that starts with one page tends to get its second page by copying
the first. Two full HTML documents, two head sections, two navigation bars, and
from then on every change to the navigation is a change in two files.

The version that gets forgotten is always the one nobody is looking at. It
keeps the old link, or loses the stylesheet, and the page it renders is subtly
wrong in a way nobody notices until somebody lands on it.

A base template with blocks costs nothing at the point the second page is
written and saves the divergence entirely.""",
    ),
]


def unwrap(text):
    """Reflow each paragraph onto one line.

    The bodies above are wrapped so they can be read in this file, but a body is
    prose and belongs to the reader's screen width. Left as they are, the
    template's linebreaks filter turns every source newline into a <br> and the
    article renders with the ragged right edge of the source instead of its own.
    """
    return "\n\n".join(" ".join(block.split()) for block in text.strip().split("\n\n"))


class Command(BaseCommand):
    help = "Create a sample author and a handful of articles."

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="delete every existing article first",
        )

    def handle(self, *args, **options):
        if options["reset"]:
            removed, _ = Article.objects.all().delete()
            self.stdout.write(f"removed {removed} existing articles")

        author, created = User.objects.get_or_create(
            username=AUTHOR["username"],
            defaults={k: v for k, v in AUTHOR.items() if k != "username"},
        )
        if created:
            author.set_unusable_password()
            author.save()

        # Spaced a few days apart so the index has a believable timeline and
        # the previous and next links on a detail page have somewhere to go.
        start = timezone.now() - timedelta(days=3 * len(ARTICLES))
        written = 0
        for index, (title, slug, body) in enumerate(ARTICLES):
            _, made = Article.objects.get_or_create(
                slug=slug,
                defaults={
                    "title": title,
                    "body": unwrap(body),
                    "author": author,
                    "published": start + timedelta(days=3 * index),
                },
            )
            written += made

        self.stdout.write(
            self.style.SUCCESS(
                f"{written} article{'' if written == 1 else 's'} created, "
                f"{Article.objects.count()} in total"
            )
        )
