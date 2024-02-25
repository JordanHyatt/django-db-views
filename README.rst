===============
django-db-views
===============

An app for creating and maintaining DB views based on ORM QuerySets
-------------------------------------------------------------------



Testing:
^^^^^^^^^^^^

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

.. code-block:: 

    python runtests.py

