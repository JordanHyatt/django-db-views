===============
django-db-views
===============

An app for creating and maintaining DB views based on ORM QuerySets
-------------------------------------------------------------------

django-db-views is a reusable, installable app for use with a Django project. **Please note** that using this package will result in the direct manipulation of your Django project's database. 

Set up:
^^^^^^^^^^^^^^

1. Install django-db-views ::

    pip install django-db-views

2. Add *db_views* to your project setting's INSTALLED_APPS
3. Migrate your database ::

    python manage.py migrate

Model/API:
^^^^^^^^^^^

You'll probably want to know how to use this so we will add some background here.
In the meantime the source code itself is fairly explanative.
Clear, readable code and comments are used throughout.

Contributing:
^^^^^^^^^^^^^^

Developers will need to install packages from *requirements.txt*.
Linux users: You'll need to use psycopg2's binaries as pip doesn't seem able to install psycopg2 from source.
After running **pip install -r requirements.txt**, linux users must also run **pip install psycopg2-binary**

A test suite is provided for vetting commits prior to integration with the project.
The test suite will require several environment variables and a postgres test database in order to function properly.

Set up tests:
""""""""""""""
Create a database on your postgres server called *dbviews* (or if you use another name set it as the *DB_NAME* environment variable.)

::

    sudo -u postgres createdb dbviews
    sudo -u postgres psql
    grant all privileges on database dbviews to postgres;


Likewise, if you are using a postgres user other than *postgres* set the name of this user as *DB_USER*.
The environment variable *DB_HOST* must point to your postgres server, if the default, *localhost* is not appropriate, change it.
*DB_PASSWORD* will be used for postgres credentials and *DB_PORT* for the port (default 5432.)

Running tests:
"""""""""""""""
Run the following command to initiate the test runner and run the test suite:

:: 

    python runtests.py

