import time

from django.test import TestCase
from django.contrib.contenttypes.models import ContentType
from django.db import connections

from tests.models import FakeModel, FakeModelFactory
from db_views.models import DbView


def get_dbv(view_name='fake_view', defaults = None):
    defaults = defaults or {}
    default_defaults=dict(
        content_type = ContentType.objects.get_for_model(FakeModel),
        get_qs_method_name = 'get_view_qs', materialized=True,
    )
    for key, val in default_defaults.items():
        if key not in defaults:
            defaults[key] = val

    return DbView.objects.update_or_create(
        view_name=view_name, defaults=defaults

    )[0]

class TestDbView(TestCase):

    def test_from_db(self):
        dbv = get_dbv()
        # New dbv object should not have _loaded_values
        self.assertIsNone(getattr(dbv, '_loaded_values', None))
        # retreive from db should have _loaded_values
        dbv = DbView.objects.first()
        self.assertIsNotNone(getattr(dbv, '_loaded_values', None))

    def test_qs(self):
        FakeModelFactory.create_batch(10)
        dbv = get_dbv()
        self.assertEqual(dbv.qs.first(), FakeModel.objects.values().first())

    def get_qs_method_exists(self):
        dbv = get_dbv()
        self.assertTrue(dbv.get_qs_method_exists)
        dbv.get_qs_method_name = 'fake_method_name'
        self.assertFalse(dbv.get_qs_method_exists)

    def test_db_connection(self):
        dbv = get_dbv()
        excpected = connections['default']
        self.assertEqual(dbv.db_connection, excpected)
        # switch to other
        dbv.db_alias = 'other'
        excpected = connections['other']
        self.assertEqual(dbv.db_connection, excpected)

    def test_get_attr_changed(self):
        get_dbv()
        dbv = DbView.objects.first()
        attrs = [('view_name', 'new_view_name'), ('materialized',False)]
        for attr_name, new_val in attrs:
            self.assertFalse(dbv.get_attr_changed(attr_name))
            self.assertFalse(getattr(dbv, f'{attr_name}_changed'))
            setattr(dbv, attr_name, new_val)
            self.assertTrue(dbv.get_attr_changed(attr_name))
            self.assertTrue(getattr(dbv, f'{attr_name}_changed'))

    def test_view_exists(self):
        dbv = get_dbv()
        self.assertFalse(dbv.view_exists)
        dbv.create_view()
        self.assertTrue(dbv.view_exists)

    def test_refresh_mat_view(self):
        dbv = get_dbv()
        dbv.refresh_mat_view()
        self.assertIsNone(dbv.dtg_last_refresh)
        dbv = get_dbv(defaults=dict(materialized=True))
        dbv.create_view()
        