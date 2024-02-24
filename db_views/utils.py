from django.db.utils import ProgrammingError
from django.db import connections

def create_view_from_qs(
    qs, 
    view_name, 
    materialized=True, 
    ufields=None, 
    db_owner='postgres',
    db_read_only_users=None,
    using = 'default'
):
    """ Utility function to create a DB view using the passed qs and view_name """
    connection = connections[using]
    db_read_only_users = db_read_only_users or []
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
    grant_permissions(
        view_name=view_name, db_owner=db_owner, 
        db_read_only_users=db_read_only_users, using=using
    )

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

def refresh_mat_view(view_name, using='default', concurrently=True):
    connection = connections[using]
    concur = 'CONCURRENTLY' if concurrently else ''
    qstr = f'REFRESH MATERIALIZED VIEW {concur} {view_name};'
    with connection.cursor() as cur:
        cur.execute(qstr)


def grant_permissions(view_name, db_owner, db_read_only_users, using='default'):
    connection = connections[using]
    sql_sql_permissions = f'''
        ALTER TABLE {view_name} OWNER TO {db_owner};
        GRANT ALL ON TABLE {view_name} TO {db_owner};
    '''
    for user in db_read_only_users:
        create_db_read_only_user(username=user, using=using)
        sql_sql_permissions += f''' GRANT SELECT ON TABLE {view_name} TO {user};'''
    with connection.cursor() as cursor:
        cursor.execute(sql_sql_permissions)


def revoke_select_privlege(view_name, username, using='default'):
    connection = connections[using]
    qstr = (
        f''' REVOKE ALL ON {view_name} FROM {username} '''
    )   
    with connection.cursor() as cur:
        cur.execute(qstr)

def create_db_read_only_user(username, using='default'):
    connection = connections[using]
    qstr = (
        f'''CREATE ROLE {username} WITH
            NOLOGIN
            NOSUPERUSER
            INHERIT
            NOCREATEDB
            NOCREATEROLE
            NOREPLICATION;
        '''
    )
    with connection.cursor() as cur:
        try:
            cur.execute(qstr)
        except ProgrammingError as pe:
            if 'already exists' not in str(pe):
                raise pe
