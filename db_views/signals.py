from django.db.models.signals import post_save
from django.dispatch import receiver

from db_views.models import DbView

@receiver(post_save, sender=DbView)
def create_view(instance, created, **kwargs):
    return