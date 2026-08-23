import logging
import os
import requests
from wagtail.signals import page_published, page_unpublished

from .models import ArticlePage

logger = logging.getLogger(__name__)


def trigger_pages_build(**kwargs):
    url = os.getenv("CLOUDFLARE_BUILD_HOOK")
    logger.warning("[SIGNAL] trigger_pages_build hook=%s", url)
    if not url:
        return
    try:
        r = requests.post(url, timeout=10)
        logger.warning("[SIGNAL] pages build http=%s", r.status_code)
    except requests.RequestException as exc:
        logger.warning("Pages build hook failed: %s", exc)


def notify_buttondown(**kwargs):
    api_key = os.getenv("BUTTONDOWN_API_KEY")
    if not api_key:
        return
    page = kwargs.get("page")
    if page is None or not isinstance(page, ArticlePage):
        return
    title = page.title
    slug = page.slug
    base = os.getenv("WAGTAILADMIN_BASE_URL", "http://localhost:8000")
    post_url = f"{base}/skills/{slug}/"
    body = (
        f"# {title}\n\n"
        f"Se publico un nuevo articulo: **{title}**.\n\n"
        f"Leelo aqui: {post_url}"
    )
    try:
        requests.post(
            "https://api.buttondown.com/v1/emails",
            headers={
                "Authorization": f"Token {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "subject": f"Nuevo articulo: {title}",
                "body": body,
                "status": "scheduled",
            },
            timeout=10,
        )
    except requests.RequestException as exc:
        logger.warning("Buttondown notify failed: %s", exc)


def on_article_published(**kwargs):
    page = kwargs.get("page") or kwargs.get("instance")
    logger.warning(
        "[SIGNAL] on_article_published page=%s is_article=%s",
        getattr(page, "title", None),
        isinstance(page, ArticlePage),
    )
    if page is None or not isinstance(page, ArticlePage):
        return
    trigger_pages_build(**kwargs)
    notify_buttondown(**kwargs)


def on_article_unpublished(**kwargs):
    page = kwargs.get("page") or kwargs.get("instance")
    logger.warning(
        "[SIGNAL] on_article_unpublished page=%s is_article=%s",
        getattr(page, "title", None),
        isinstance(page, ArticlePage),
    )
    if page is None or not isinstance(page, ArticlePage):
        return
    trigger_pages_build(**kwargs)


logger.warning("[SIGNAL] signals module loaded, hook=%s", os.getenv("CLOUDFLARE_BUILD_HOOK"))

page_published.connect(on_article_published)
page_unpublished.connect(on_article_unpublished)
