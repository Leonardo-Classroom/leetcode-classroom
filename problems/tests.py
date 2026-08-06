from django.test import TestCase

from .filters import filter_problems
from .models import Problem, Tag


class ProblemFilterTests(TestCase):
    def setUp(self):
        self.array_tag = Tag.objects.create(name="Array", slug="array")
        self.dp_tag = Tag.objects.create(name="Dynamic Programming", slug="dynamic-programming")

        self.p1 = Problem.objects.create(
            number=1, title="Two Sum", title_slug="two-sum",
            url="https://leetcode.com/problems/two-sum/", difficulty="Easy", ac_rate="57.95",
        )
        self.p1.tags.add(self.array_tag)

        self.p2 = Problem.objects.create(
            number=5, title="Longest Palindromic Substring", title_slug="longest-palindromic-substring",
            url="https://leetcode.com/problems/longest-palindromic-substring/",
            difficulty="Medium", ac_rate="38.39",
        )
        self.p2.tags.add(self.dp_tag)

    def test_filter_by_keyword(self):
        from django.http import QueryDict
        qs = filter_problems(QueryDict("q=Two"))
        self.assertEqual(list(qs), [self.p1])

    def test_filter_by_difficulty(self):
        from django.http import QueryDict
        qs = filter_problems(QueryDict("difficulty=Medium"))
        self.assertEqual(list(qs), [self.p2])

    def test_filter_by_tag(self):
        from django.http import QueryDict
        qs = filter_problems(QueryDict(f"tags={self.array_tag.id}"))
        self.assertEqual(list(qs), [self.p1])

    def test_no_filter_returns_all(self):
        from django.http import QueryDict
        qs = filter_problems(QueryDict(""))
        self.assertEqual(qs.count(), 2)
