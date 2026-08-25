from django.apps import AppConfig


class SkillsBlogConfig(AppConfig):
    name = "skills_blog"

    def ready(self):
        from . import signals  # noqa: F401
        from . import agents  # noqa: F401
