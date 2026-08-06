from django.db import models


class Tag(models.Model):
    name = models.CharField(max_length=64, unique=True)
    slug = models.SlugField(max_length=64, unique=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Problem(models.Model):
    class Difficulty(models.TextChoices):
        EASY = "Easy", "Easy"
        MEDIUM = "Medium", "Medium"
        HARD = "Hard", "Hard"

    number = models.PositiveIntegerField("題號", unique=True)
    title = models.CharField("題名", max_length=255)
    title_slug = models.SlugField(max_length=255)
    url = models.URLField("網址")
    difficulty = models.CharField("難度", max_length=8, choices=Difficulty.choices)
    ac_rate = models.DecimalField("通過率(%)", max_digits=5, decimal_places=2)
    tags = models.ManyToManyField(Tag, related_name="problems", blank=True)

    class Meta:
        ordering = ["number"]

    def __str__(self):
        return f"{self.number}. {self.title}"
