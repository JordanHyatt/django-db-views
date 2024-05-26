import logging
from django.db import models
from django.conf import settings
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType
from django.db import connections
from django.db.utils import OperationalError, ProgrammingError
from django.contrib.postgres.fields import ArrayField
from django.db import transaction

from qs_views.utils import *

logger = logging.getLogger()



def get_db_owner_default():
    from django.conf import settings
    return settings.DATABASES.get('default', {}).get('USER', 'postgres')


class QsView(models.Model):
    ''' Represents a database view created from a django queryset '''

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


    def get_get_qs_method(self):
        m1 = getattr(self.content_type.model_class(), self.get_qs_method_name, None)
        m2 = getattr(self.content_type.model_class()._default_manager, self.get_qs_method_name, None)
        return m1 or m2

    @property
    def qs(self):
        if self.get_qs_method_exists:
            return self.get_get_qs_method().__call__()
        return None

    @property
    def get_qs_method_exists(self):
        """ Property returns True if the get_qs_method exists on the model_class """
        m1 = hasattr(self.content_type.model_class(), self.get_qs_method_name)
        m2 = hasattr(self.content_type.model_class()._default_manager, self.get_qs_method_name)
        return m1 or m2

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
    def view_exists(self):
        return view_exists(
            view_name=self.view_name, materialized=self.materialized, using=self.db_alias
        )

    def refresh_mat_view(self):
        if not self.materialized:
            logger.warning(f'View refresh can only be called on materialized views')
            return
        if not self.view_exists:
            logger.warning(f'View {self.view_name} does not exist and cannot be refreshed')
            return
        logger.info(f'Refreshing View: {self.view_name}')
        refresh_mat_view(view_name=self.view_name, using=self.db_alias)
        self.dtg_last_refresh = timezone.now()
        self.save()

    def create_view(self, save_instance=True):
        if self.qs is None:
            logger.warning(f"Queryset is None cannot create view {self.view_name}")
        create_view_from_qs(
            self.qs, view_name=self.view_name, ufields=self.ufields, 
            using=self.db_alias, materialized=self.materialized, 
            db_owner=self.db_owner, db_read_only_users=self.db_read_only_users
        )
        now = timezone.now()
        self.dtg_last_refresh = now
        self.dtg_view_created = now
        if save_instance:
            self.save()

    def drop_view(self, view_name=None):
        view_name = view_name or self.view_name
        drop_view(view_name=view_name, using=self.db_alias)

    def drop_old_view_if_changed(self):
        if self.view_name_changed or self.materialized_changed:
            orig_view_name = getattr(self, '_loaded_values', {}).get('view_name')
            if orig_view_name:
                self.drop_view(view_name=orig_view_name)

    def revoke_privleges(self):
        if not self.view_exists:
            return
        orig = set(getattr(self, '_loaded_values', {}).get('db_read_only_users', set()))
        revoke_list = orig.difference(self.db_read_only_users)
        revoke_privleges(view_name=self.view_name, revoke_list=revoke_list, using=self.db_alias)

    def grant_privleges(self):
        if not self.view_exists:
            return
        grant_privleges(
            view_name=self.view_name, db_owner=self.db_owner, 
            db_read_only_users=self.db_read_only_users, using=self.db_alias,
        )

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


    def save(self, *args, call_create_view=True, **kwargs):
        self.get_get_qs_method_name()
        self.get_fields()
        super().save(*args, **kwargs)
        transaction.on_commit(self.revoke_privleges)
        transaction.on_commit(self.grant_privleges)
        transaction.on_commit(self.drop_old_view_if_changed)


    def delete(self, *args, **kwargs):
        super().delete(*args, **kwargs)
        self.drop_view()

    def __str__(self):
        return f'{self.view_name} | {self.get_qs_method_name} | {self.content_type.model_class().__name__}'