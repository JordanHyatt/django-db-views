from django.test import TestCase
from django.contrib.contenttypes.models import ContentType

from tests.models import FakeModel, FakeModelFactory
from db_views.models import DbView


def get_standard_dbv():
    return DbView.objects.update_or_create(
        view_name='fake_view', 
        defaults=dict(
            content_type = ContentType.objects.get_for_model(FakeModel),
            get_qs_method_name = 'get_view_qs',
        )
    )[0]

class TestDbView(TestCase):

    def test_qs(self):
        FakeModelFactory.create_batch(10)
        dbv = get_standard_dbv()
        self.assertEqual(dbv.qs.first(), FakeModel.objects.values().first())

    
    def test_from_db(self):
        dbv = get_standard_dbv()
        # New dbv object should not have _loaded_values
        self.assertIsNone(getattr(dbv, '_loaded_values', None))
        # retreive from db should have _loaded_values
        dbv = DbView.objects.first()
        self.assertIsNotNone(getattr(dbv, '_loaded_values', None))

