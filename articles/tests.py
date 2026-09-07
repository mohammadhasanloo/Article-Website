from datetime import timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Article
from .views import PER_PAGE


def make_article(title, slug, body="A body.", days_ago=0, author=None):
    return Article.objects.create(
        title=title,
        slug=slug,
        body=body,
        author=author,
        published=timezone.now() - timedelta(days=days_ago),
    )


class ArticleModelTests(TestCase):

    def test_articles_come_back_newest_first(self):
        make_article("Older", "older", days_ago=5)
        make_article("Newer", "newer", days_ago=1)

        self.assertEqual(
            ["Newer", "Older"], [a.title for a in Article.objects.all()]
        )

    def test_the_url_is_built_from_the_slug(self):
        article = make_article("Title", "the-slug")

        self.assertEqual("/articles/the-slug/", article.get_absolute_url())

    def test_a_duplicate_slug_is_refused(self):
        make_article("First", "shared")

        with self.assertRaises(Exception):
            make_article("Second", "shared")

    def test_a_short_body_is_its_own_snippet(self):
        article = make_article("Short", "short", body="Three words here.")

        self.assertEqual("Three words here.", article.snippet())

    def test_a_long_body_is_cut_at_a_word(self):
        article = make_article("Long", "long", body="alpha " * 100)
        snippet = article.snippet()

        self.assertTrue(snippet.endswith("..."))
        self.assertLess(len(snippet), len(article.body))
        self.assertNotIn("alph...", snippet)

    def test_reading_time_is_at_least_a_minute(self):
        self.assertEqual(1, make_article("Tiny", "tiny", body="One.").reading_time())
        self.assertEqual(
            3, make_article("Big", "big", body="word " * 500).reading_time()
        )


class ArticleListTests(TestCase):

    def setUp(self):
        self.author = User.objects.create_user("writer", first_name="A", last_name="B")
        for index in range(PER_PAGE + 3):
            make_article(f"Article {index}", f"article-{index}",
                         days_ago=index, author=self.author)

    def test_the_index_shows_one_page_at_a_time(self):
        response = self.client.get(reverse("articles:list"))

        self.assertEqual(200, response.status_code)
        self.assertEqual(PER_PAGE, len(response.context["page"]))
        self.assertTrue(response.context["page"].has_next())

    def test_the_second_page_holds_the_rest(self):
        response = self.client.get(reverse("articles:list"), {"page": 2})

        self.assertEqual(3, len(response.context["page"]))
        self.assertFalse(response.context["page"].has_next())

    def test_a_page_past_the_end_falls_back_to_the_last_one(self):
        """get_page is used precisely so a bookmarked page 99 does not raise."""
        response = self.client.get(reverse("articles:list"), {"page": 99})

        self.assertEqual(200, response.status_code)
        self.assertEqual(2, response.context["page"].number)

    def test_a_page_that_is_not_a_number_falls_back_to_the_first(self):
        response = self.client.get(reverse("articles:list"), {"page": "last"})

        self.assertEqual(1, response.context["page"].number)

    def test_search_matches_the_title(self):
        make_article("A distinctive heading", "distinctive")

        response = self.client.get(reverse("articles:list"), {"q": "distinctive"})

        self.assertEqual(1, response.context["total"])

    def test_search_matches_the_body(self):
        make_article("Ordinary", "ordinary", body="mentions kubernetes once")

        response = self.client.get(reverse("articles:list"), {"q": "KUBERNETES"})

        self.assertEqual(1, response.context["total"])

    def test_search_keeps_its_term_in_the_paging_links(self):
        response = self.client.get(reverse("articles:list"), {"q": "Article"})

        self.assertContains(response, "q=Article&amp;page=2")

    def test_an_empty_index_says_so(self):
        Article.objects.all().delete()

        self.assertContains(self.client.get(reverse("articles:list")), "Nothing published yet")


class ArticleDetailTests(TestCase):

    def setUp(self):
        self.middle = make_article("Middle", "middle", days_ago=5)
        self.older = make_article("Older", "older", days_ago=9)
        self.newer = make_article("Newer", "newer", days_ago=1)

    def test_an_article_is_served_by_its_slug(self):
        response = self.client.get(self.middle.get_absolute_url())

        self.assertEqual(200, response.status_code)
        self.assertContains(response, "Middle")

    def test_an_unknown_slug_is_a_404(self):
        self.assertEqual(404, self.client.get("/articles/no-such-thing/").status_code)

    def test_the_neighbours_are_the_articles_either_side_in_time(self):
        response = self.client.get(self.middle.get_absolute_url())

        self.assertEqual(self.newer, response.context["newer"])
        self.assertEqual(self.older, response.context["older"])

    def test_the_ends_of_the_timeline_have_one_neighbour(self):
        newest = self.client.get(self.newer.get_absolute_url())
        oldest = self.client.get(self.older.get_absolute_url())

        self.assertIsNone(newest.context["newer"])
        self.assertIsNone(oldest.context["older"])


class SiteTests(TestCase):

    def test_the_home_page_lists_the_three_newest(self):
        for index in range(5):
            make_article(f"Article {index}", f"article-{index}", days_ago=index)

        response = self.client.get(reverse("home"))

        self.assertEqual(200, response.status_code)
        self.assertEqual(
            ["Article 0", "Article 1", "Article 2"],
            [a.title for a in response.context["latest"]],
        )

    def test_the_about_page_renders(self):
        self.assertEqual(200, self.client.get(reverse("about")).status_code)

    def test_every_page_carries_the_shared_navigation(self):
        """Each template extends the base, so the nav cannot drift between them."""
        article = make_article("Title", "title")

        for url in [reverse("home"), reverse("about"), reverse("articles:list"),
                    article.get_absolute_url()]:
            with self.subTest(url=url):
                self.assertContains(self.client.get(url), 'class="masthead"')


class SeedCommandTests(TestCase):

    def test_seeding_twice_does_not_duplicate(self):
        from django.core.management import call_command

        call_command("seed", verbosity=0)
        first = Article.objects.count()
        call_command("seed", verbosity=0)

        self.assertEqual(first, Article.objects.count())
        self.assertGreater(first, 0)

    def test_reset_clears_before_writing(self):
        from django.core.management import call_command

        make_article("Left over", "left-over")
        call_command("seed", "--reset", verbosity=0)

        self.assertFalse(Article.objects.filter(slug="left-over").exists())
