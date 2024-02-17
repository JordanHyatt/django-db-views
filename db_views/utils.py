from django.db.utils import ProgrammingError
from django.db import connections

def drop_view(view_name, using='default'):
    connection = connections[using]
    drop_qstr1 = f''' DROP VIEW IF EXISTS "{view_name}" '''
    drop_qstr2 = f''' DROP MATERIALIZED VIEW IF EXISTS "{view_name}" '''
    with connection.cursor() as cursor:
        # Drop existing views with the name view_name
        for dstr in [drop_qstr1, drop_qstr2]:
            try:
                cursor.execute(dstr)
            except ProgrammingError:
                pass

def create_view_from_qs_base(qs, view_name, sql_permissions=None, materialized=True, ufields=None, using='default'):
    """Utility function to create a DB view from a django queryset.
    Args:
        qs (django.db.QuerySet): The queryset to be translated into a view
        view_name (str): View name to be created/updated
        sql_permissions (str, optional): SQL to be executed after the view is created, 
            intended for setting permissions but could be any raw SQL. 
            i.e. ALTER TABLE public.{view_name} OWNER TO postgres;
        materialized (bool): If True will create a materialized view. default True
        ufields (list): List of field names to create a unique index on 
    """    
    connection = connections[using]
    qstr, params = qs.query.sql_with_params()
    vstr = 'MATERIALIZED VIEW' if materialized else 'VIEW'
    drop_view(view_name) # Call the drop view util
    qstr = f''' CREATE {vstr} "{view_name}" AS {qstr} '''
    index_qstr = None
    if ufields and materialized:
        index_name = f'unique_{view_name}'
        index_drop = f"DROP INDEX IF EXISTS {index_name}"
        index_qstr = f"CREATE UNIQUE INDEX {index_name} ON {view_name} ({', '.join(ufields)})"
    with connection.cursor() as cursor:
        # main view creation
        cursor.execute(qstr, params) 
        # unique index creation
        if index_qstr:
            cursor.execute(index_drop)
            cursor.execute(index_qstr)

    if sql_permissions:
        with connection.cursor() as cursor:
            cursor.execute(sql_permissions)

def create_view_from_qs(
    qs, 
    view_name, 
    use_default_permissions=True, 
    materialized=True, 
    ufields=None, 
    db_owner='postgres',
    read_only_users=None,
    using = 'default'
):
    """ Utility function to create a DB view using the passed qs and view_name """
    connection = connections[using]
    if read_only_users == None: read_only_users = []
    sql_permisions = f'''
        ALTER TABLE public.{view_name} OWNER TO postgres;
        GRANT ALL ON TABLE public.{view_name} TO postgres;
    '''
    if use_default_permissions:
        sql_permisions += f''' GRANT SELECT ON TABLE public.{view_name} TO accdc_readonly;'''
    for ruser in read_only_users:
        sql_permisions += f''' GRANT SELECT ON TABLE public.{view_name} TO {ruser};'''
    create_view_from_qs_base(qs, view_name=view_name, sql_permissions=sql_permisions, materialized=materialized, ufields=ufields)
