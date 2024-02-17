from django.db.models import Model, CharField


class DbView(models.Model):
    ''' Represents a database view created from a django query '''
    STORE_ORIG = True
    
    view_name = CharField(max_length=255, unique=True)
    content_type = ForeignKey(ContentType, on_delete=CASCADE) # The ContentType of the model that generates the QS
    get_qs_method_name = CharField(max_length=255) # Name of the method on the model that gets the queryset
    fields = ArrayField(CharField(max_length=255,null=True), size=100, null=True, blank=True)
    ufields = ArrayField(CharField(max_length=255,null=True), size=100, null=True, blank=True, verbose_name="Unique Fields")
    owners = ManyToManyField('common.Employee', blank=True)
    materialized = BooleanField(default=True)
    desc = TextField(null=True, blank=True)
    dtg_last_refresh = DateTimeField(null=True, blank=True)
    dtg_view_created = DateTimeField(null=True, blank=True)
    history = HistoricalRecords(related_name='log')

    class Meta:
        ordering = ('-dtg_last_refresh', '-dtg_view_created')

    @property
    def view_name_changed(self):
        old_view_name = getattr(self, 'orig', {}).get('view_name') or self.view_name
        return old_view_name != self.view_name

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
        with connection .cursor() as cur:
            cur.execute(sql)
            return cur.fetchone()[0]

    def refresh_mat_view(self, run_async=True):
        ''' refreshes materialized view asynchronously '''
        app_label, model_name = get_app_label_model_name(self)
        method = run_instance_method_task.delay if run_async else run_instance_method_task
        method(pk=self.pk, app_label=app_label, model_name=model_name, method_name='_refresh_mat_view')

    def _refresh_mat_view(self):
        if not self.materialized:
            logger.warning(f'View refresh can only be called on materialized views')
        if not self.view_exists:
            logger.warning(f'View {self.view_name} does not exist and cannot be refreshed')
        logger.info(f'Refreshing View: {self.view_name}')
        qstr = f'REFRESH MATERIALIZED VIEW CONCURRENTLY {self.view_name};'
        with connection.cursor() as cur:
            try:
                cur.execute(qstr)
            except OperationalError:
                logger.warning(f'---- {self.view_name} does not have an unique index -----')
                return
        self.dtg_last_refresh = timezone.now()
        self.save()

    def create_view(self, run_async=True):
        ''' refreshes materialized view asynchronously '''
        app_label, model_name = get_app_label_model_name(self)
        method = run_instance_method_task.delay if run_async else run_instance_method_task
        method(pk=self.pk, app_label=app_label, model_name=model_name, method_name='_create_view')

    def _create_view(self):
        if self.qs is None:
            logger.warning(f"Queryset is None cannot create view {self.view_name}")
        create_view_from_qs(
            self.qs, view_name=self.view_name, ufields=self.ufields, materialized=self.materialized, 
        )
        self.dtg_last_refresh = timezone.now()
        self.dtg_view_created = timezone.now()
        self.save()

    def drop_view(self, view_name=None):
        view_name = view_name or self.view_name
        drop_qstr1 = f''' DROP VIEW IF EXISTS "{view_name}" '''
        drop_qstr2 = f''' DROP MATERIALIZED VIEW IF EXISTS "{view_name}" '''
        with connection.cursor() as cursor:
            # Drop existing views with the name view_name
            for dstr in [drop_qstr1, drop_qstr2]:
                try:
                    cursor.execute(dstr)
                except ProgrammingError:
                    pass

    def drop_old_view_if_changed(self):
        if not self.view_name_changed:
            return
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