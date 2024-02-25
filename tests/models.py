import uuid
from factory.django import DjangoModelFactory
from django.db import models



class FakeModel(models.Model):
    uuid = models.UUIDField(default = uuid.uuid4, editable=False, primary_key=True)
    
    @classmethod
    def get_view_qs(cls):
        return cls.objects.values()


class FakeModelFactory(DjangoModelFactory):
    class Meta:
        model = FakeModel
    

