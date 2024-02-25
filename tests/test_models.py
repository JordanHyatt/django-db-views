from django.test import TestCase
from django.contrib.contenttypes.models import ContentType

from tests.models import FakeModel, FakeModelFactory
from db_views.models import DbView

class TestDbView(TestCase):

    def test_qs(self):
        FakeModelFactory.create_batch(10)
        dbv,_ = DbView.objects.update_or_create(
            view_name='fake_view', 
            defaults=dict(
                content_type = ContentType.objects.get_for_model(FakeModel),
                get_qs_method_name = 'get_view_qs',
            )
        )
        self.assertEqual(dbv.qs.first(), FakeModel.objects.values().first())