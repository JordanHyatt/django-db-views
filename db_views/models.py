import logging
from django.db import models
from django.conf import settings
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType
from django.db import connections
from django.db.utils import OperationalError, ProgrammingError
from django.contrib.postgres.fields import ArrayField

from db_views.utils import *

logger = logging.getLogger()


def get_db_owner_default():
    from django.conf import settings
    return settings.DATABASES.get('default', {}).get('USER', 'postgres')


class DbView(models.Model):
    ''' Represents a database view created from a django query '''

    view_name = models.CharField(max_length=255, unique=True)
    db_alias = models.CharField(max_length=255, default='default')
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE) # The ContentType of the model that generates the qs
    get_qs_method_name = models.CharField(max_length=255) # Name of the method on the content_type that generates the qs
    fields = models.JSONField(null=True, blank=True)
    ufields = models.JSONField(null=True, blank=True, verbose_name="Unique Fields")
    owners = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True) # Django users that "own" the view
    materialized = models.BooleanField(default=True) 
    desc = models.TextField(null=True, blank=True)
    dtg_last_refresh = models.DateTimeField(null=True, blank=True) # only applies to materialized views
    dtg_view_created = models.DateTimeField(null=True, blank=True)

    # Database Fields 
    db_owner = models.CharField(max_length=50, default=get_db_owner_default) # Database owner of the view. Defaults to DATABASES['default']['USER']
    db_read_only_users = ArrayField(models.CharField(max_length=50, blank=True), default=list)

    class Meta:
        ordering = ('-dtg_last_refresh', '-dtg_view_created')

    @classmethod
    def from_db(cls, db, field_names, values):
        instance = super().from_db(db, field_names, values)
        instance._loaded_values = dict(
            zip(field_names, (value for value in values if value is not models.DEFERRED))
        )
        return instance

    @property
    def db_connection(self):
        return connections[self.db_alias]

    @property
    def view_name_changed(self):
        return self.get_attr_changed(attr_name='view_name')

    @property
    def materialized_changed(self):
        return self.get_attr_changed(attr_name='materialized')

    def get_attr_changed(self, attr_name):
        orig = getattr(self, '_loaded_values', {}).get(attr_name)
        return orig != getattr(self, attr_name)

    @property
    def model_class(self):
        return self.content_type.model_class()

    @property
    def model_name(self):
        return self.model_class.__name__

    @property
    def qs_model_name(self):
        return self.qs.model.__name__

    @property
    def qs(self):
        if self.get_qs_method_exists:
            return getattr(self.model_class, self.get_qs_method_name).__call__()
        return None

    @property
    def filter_logic(self):
        return str(self.qs.query.where).replace('<', '').replace('>', '')

    @property
    def get_qs_method_exists(self):
        """ Property returns True if the get_qs_method exists on the model_class """
        return hasattr(self.model_class, self.get_qs_method_name)

    @property
    def view_exists(self):
        from django.db import connection
        if self.materialized:
            sql = f"select exists(select matviewname from pg_matviews where matviewname='{self.view_name}')"
        else:
            sql = f"select exists(select viewname from pg_views where viewname='{self.view_name}')"
        with self.db_connection.cursor() as cur:
            cur.execute(sql)
            return cur.fetchone()[0]

    def refresh_mat_view(self):
        if not self.materialized:
            logger.warning(f'View refresh can only be called on materialized views')
        if not self.view_exists:
            logger.warning(f'View {self.view_name} does not exist and cannot be refreshed')
        logger.info(f'Refreshing View: {self.view_name}')
        refresh_mat_view(view_name=self.view_name, using=self.db_alias)
        self.dtg_last_refresh = timezone.now()
        self.save()


    def create_view(self):
        if self.qs is None:
            logger.warning(f"Queryset is None cannot create view {self.view_name}")
        create_view_from_qs(
            self.qs, view_name=self.view_name, ufields=self.ufields, using=self.db_alias,
            materialized=self.materialized, db_owner=self.db_owner, 
        )
        self.dtg_last_refresh = timezone.now()
        self.dtg_view_created = timezone.now()
        self.save()

    def drop_view(self, view_name=None):
        view_name = view_name or self.view_name
        drop_qstr1 = f''' DROP VIEW IF EXISTS "{view_name}" '''
        drop_qstr2 = f''' DROP MATERIALIZED VIEW IF EXISTS "{view_name}" '''
        with self.db_connection.cursor() as cursor:
            # Drop existing views with the name view_name
            for dstr in [drop_qstr1, drop_qstr2]:
                try:
                    cursor.execute(dstr)
                except ProgrammingError:
                    pass

    def drop_old_view_if_changed(self):
        if self.view_name_changed or self.materialized_changed:
            orig_view_name = getattr(self, 'orig', {}).get('view_name')
            if orig_view_name:
                self.drop_view(view_name=orig_view_name)

    def get_fields(self):
        qs = self.qs
        m1 = qs is None
        m2 = bool(self.fields)
        if m1 or m2:
            return
        self.fields = list(qs.query.values_select) + list(qs.query.annotations.keys())

    def get_get_qs_method_name(self):
        if self.get_qs_method_name:
            return
        self.get_qs_method_name = f'get_{self.view_name}_qs'

    def run_save_methods(self):
        self._created = not bool(self.pk)
        self.get_get_qs_method_name()
        self.get_fields()
        
    def run_after_pk_methods(self):
        self.drop_old_view_if_changed()
        
    def delete(self, *args, **kwargs):
        super().delete(*args, **kwargs)
        self.drop_view()

    def __str__(self):
        return f'{self.view_name} | {self.get_qs_method_name} | {self.content_type.model_class().__name__}'