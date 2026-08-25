from enum import unique
from django.db import models
from treebeard.utils import serializers
from wagtail.admin import panels
from wagtail.api import APIField
from wagtail.models import Page
from wagtail.fields import RichTextField
from taggit.models import TaggedItemBase
from wagtail.search import index
from modelcluster.fields import ParentalKey
from wagtail.admin.panels import FieldPanel
from modelcluster.contrib.taggit import ClusterTaggableManager
from datetime import date
from rest_framework.fields import Field
from wagtail.snippets.models import register_snippet
from wagtail_ai.panels import AITitleFieldPanel, AIDescriptionFieldPanel


# Create your models here.
class BlogPage(Page):
    body = RichTextField(blank=True)

    content_panels = Page.content_panels + [FieldPanel("body")]

    template = "blog/blog_page.html"

    def get_context(self, request):
        tag = request.GET.get("tag")
        if tag:
            articles = (
                ArticlePage.objects.filter(tags__name=tag)
                .live()
                .order_by("-first_published_at")
            )
        else:
            articles = self.get_children().live().order_by("-first_published_at")

        context = super().get_context(request)
        context["articles"] = articles
        context["tag"] = tag
        return context


class ImageUrl(Field):
    def to_representation(self, value):
        if not value:
            return None

        rendition = value.get_rendition("width-1600|format-webp")
        return {
            "url": rendition.url,
            "title": value.title,
            "width": value.width,
            "height": value.height,
        }


class OwnerProfile(Field):
    def to_representation(self, value):
        return {
            "username": value.username,
            "first_name": value.first_name,
            "last_name": value.last_name,
            "profile_picture": value.profile_picture.url
            if value.profile_picture
            else None,
        }


class ArticlePage(Page):
    intro = models.CharField(max_length=80)
    body = RichTextField(blank=True)
    date = models.DateField("Post date", default=date.today)
    image = models.ForeignKey(
        "wagtailimages.Image", on_delete=models.SET_NULL, null=True, related_name="+"
    )
    caption = models.CharField(blank=True, max_length=80)
    tags = ClusterTaggableManager(through="ArticleTag", blank=True)
    repo_url = models.URLField(blank=True)

    api_fields = [
        APIField("intro"),
        APIField("body"),
        APIField("date"),
        APIField("image", serializer=ImageUrl()),
        APIField("owner", serializer=OwnerProfile()),
        APIField("caption"),
        APIField("tags"),
        APIField("repo_url"),
    ]

    def get_author(self):
        return self.owner.username

    def get_author_first_name(self):
        return self.owner.first_name

    search_fields = Page.search_fields + [
        index.SearchField("intro"),
        index.SearchField("get_author"),
        index.SearchField("get_author_first_name"),
    ]

    template = "blog/article_page.html"

    content_panels = [
        AITitleFieldPanel("title"),
        AIDescriptionFieldPanel("intro"),
        FieldPanel("image"),
        FieldPanel("caption"),
        FieldPanel("body"),
        FieldPanel("date"),
        FieldPanel("tags"),
        FieldPanel("repo_url"),
    ]


class ArticleTag(TaggedItemBase):
    content_object = ParentalKey(
        ArticlePage,
        on_delete=models.CASCADE,
        related_name="tagged_items",
    )


@register_snippet
class NewsletterSubscriber(models.Model):
    name = models.CharField(max_length=120)
    email = models.EmailField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    panels = [
        FieldPanel("name"),
        FieldPanel("email"),
        FieldPanel("created_at", read_only=True),
    ]

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} <{self.email}>"
