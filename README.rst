===============
django-qs-views
===============

\*UNDER ACTIVE DEVELOPMENT\*
-----------------------------

An app for creating and maintaining DB views based on ORM QuerySets
-------------------------------------------------------------------

This application is especially useful for when you want to tie analytics tools such as tableau, etc directly into your backend without having to do all the SQL.  You can create the views required directly from the django ORM.

django-qs-views is a reusable, installable app for use with a Django project. **Please note** that using this package will result in the direct manipulation of your Django project's database. 

Installation:
^^^^^^^^^^^^^

1. Install django-qs-views ::

    pip install django-qs-views

2. Add *qs_views* to your project setting's INSTALLED_APPS.  You must also have contenttypes framework installed :: 

        INSTALLED_APPS = [
            ...
            'django.contrib.contenttypes',
            'qs_views',
        ]

3. Migrate your database ::

    python manage.py migrate


Example Usage:
^^^^^^^^^^^^^^
Say your project has the following models.

.. code-block :: python 

    class Organization(models.Model):
        name = models.CharField(max_length=250)
        country_code = models.CharField(max_length=5, null=True)

    class Person(models.Model):
        org = models.ForeignKey('Organization', null=True, blank=True, on_delete=models.SET_NULL)
        last_name = models.CharField(max_length=100, null=True)
        first_name = models.CharField(max_length=100, null=True)
        middle_name = models.CharField(max_length=100, null=True, blank=True)
        salary = models.FloatField(null=True)

        @classmethod
        def get_person_view_qs(cls):
            return cls.objects.annotate(
                org_name = F('org__name')
            ).values()

You would like to create a DB view from the Person model that joins Org info.  Simply create a @classmethod that generates the queryset.  In the example above the method is called `` get_person_view_qs ``

To generate the view use the ORM (or create frontend UI to interact with the model) to create a QsView instance and call the ``create_view`` method

.. code-block :: python
    
    content_type = ContentType.objects.get_for_model(Person)
    qsv = QsView.objects.create(
        view_name='person_view',  content_type=content_type,
        get_qs_method_name = 'get_person_view_qs',
        materialized=False,  db_read_only_users=['user_readonly1'],
    )
    qsv.create_view()

At this point the default DB will have a view in called "person_view" that matches the result of the queryset returned from ``get_person_view_qs``.  If you delete the QsView instance the view will be dropped from the database.  


Contributing:
^^^^^^^^^^^^^

Developers will need to install packages from *requirements.txt*.
Linux users: You'll need to use psycopg2's binaries as pip doesn't seem able to install psycopg2 from source.
After running

**pip install -r requirements.txt**, linux users must also run 

**pip install psycopg2-binary**

A test suite is provided for vetting commits prior to integration with the project.
The test suite will require several environment variables and a postgres test database in order to function properly.

Set up tests:
""""""""""""""
Create a database on your postgres server called *qsviews* (or if you use another name set it as the *DB_NAME* environment variable.)

::

    sudo -u postgres createdb qsviews
    sudo -u postgres psql
    grant all privileges on database qsviews to postgres;


Likewise, if you are using a postgres user other than *postgres* set the name of this user as *DB_USER*.
The environment variable *DB_HOST* must point to your postgres server, if the default, *localhost* is not appropriate, change it.
*DB_PASSWORD* will be used for postgres credentials and *DB_PORT* for the port (default 5432.)

Running tests:
"""""""""""""""
Run the following command to initiate the test runner and run the test suite:


To test with the requirements.txt env:: 
    
    python runtests.py

To test with the all supported envs:: 
    
    tox run




