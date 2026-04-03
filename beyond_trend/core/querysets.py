from django.db import models
from django.utils import timezone


class ArchiveMixin:
    """
    Mixin for archive instance of model
    """

    def archive(self):
        kwargs = {
            'is_archived': True,
            'updated_at': timezone.now()
        }
        self.update(**kwargs)

    def restore(self):
        kwargs = {
            'is_archived': False,
            'updated_at': timezone.now()
        }
        self.update(**kwargs)

    def unarchived(self):
        return self.filter(is_archived=False)


class PublishMixin:
    """
    Mixin for Publish instance of model
    """

    def publish(self):
        kwargs = {
            'is_published': True,
            'updated_at': timezone.now()
        }
        self.update(**kwargs)

    def hide(self):
        kwargs = {
            'is_published': False,
            'updated_at': timezone.now()
        }
        self.update(**kwargs)

    def published(self):
        return self.filter(is_published=True)


class BaseModelQuerySet(models.QuerySet, ArchiveMixin, PublishMixin):
    """
    Base Queryset used in this project
    """
    pass


class BasePublishModelQuerySet(models.QuerySet, ArchiveMixin, PublishMixin):
    """
    Base Queryset used in this project
    """
    pass
