import logging
import os
import requests
from wagtail.signals import page_published, page_unpublished

logger = logging.getLogger(__name__)


def trigger_netlify(**kwargs):
    url = os.getenv("NETLIFY_BUILD_HOOK")
    if not url:
        return
    try:
        requests.post(url, timeout=10)
    except requests.RequestException as exc:
        logger.warning("Netlify hook failed: %s", exc)


page_published.connect(trigger_netlify)
page_unpublished.connect(trigger_netlify)
