from django.test import TestCase
from django.contrib.contenttypes.models import ContentType
from django.db import connections

from tests.models import FakeModel, FakeModelFactory
from db_views.models import DbView


def get_standard_dbv():
    return DbView.objects.update_or_create(
        view_name='fake_view', 
        defaults=dict(
            content_type = ContentType.objects.get_for_model(FakeModel),
            get_qs_method_name = 'get_view_qs', materialized=True,
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

    def test_db_connection(self):
        dbv = get_standard_dbv()
        excpected = connections['default']
        self.assertEqual(dbv.db_connection, excpected)
        # switch to other
        dbv.db_alias = 'other'
        excpected = connections['other']
        self.assertEqual(dbv.db_connection, excpected)

    def test_get_attr_changed(self):
        get_standard_dbv()
        dbv = DbView.objects.first()
        attrs = [('view_name', 'new_view_name'), ('materialized',False)]
        for attr_name, new_val in attrs:
            self.assertFalse(dbv.get_attr_changed(attr_name))
            setattr(dbv, attr_name, new_val)
            self.assertTrue(dbv.get_attr_changed(attr_name))

    def test_model_class(self):
        dbv = get_standard_dbv()
        self.assertIs(dbv.model_class, FakeModel)