from celery import shared_task

from beyond_trend.users.models import User


@shared_task()
def get_users_count():
    """A pointless Celery task to demonstrate usage."""
    return User.objects.count()
