# django-qs-views

### *UNDER ACTIVE DEVELOPMENT*

### An app for creating and maintaining DB views based on ORM QuerySets

This application is especially useful for when you want to tie analytics tools such as tableau, etc directly into your backend without having to do all the SQL.  You can create the views required directly from the django ORM.

django-qs-views is a reusable, installable app for use with a Django project. **Please note** that using this package will result in the direct manipulation of your Django project's database. 

## Installation

1. Install django-qs-views

    ```pip install django-qs-views```

2. Add *qs_views* to your project setting's INSTALLED_APPS.  You must also have contenttypes framework installed. (*Note*: The utils can be used without installing the app and migrating)

        INSTALLED_APPS = [
            ...
            'django.contrib.contenttypes',
            'qs_views',
        ]

3. Migrate your database

    ``` python manage.py migrate ```

## Example Usage

Say your project has the following models.
```python 
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
```
You would like to create a DB view from the Person model that joins Org info.  Simply create a
 ```@classmethod``` that generates the queryset.  In the example above the method is called `` get_person_view_qs ``.

To generate the view use the ORM (or create frontend UI to interact with the model) to create a QsView instance and call the ``create_view`` method

```python
content_type = ContentType.objects.get_for_model(Person)
qsv = QsView.objects.create(
    view_name='person_view',  content_type=content_type,
    get_qs_method_name = 'get_person_view_qs',
    materialized=False,  db_read_only_users=['user_readonly1'],
)
qsv.create_view()
```
At this point the default DB will have a view in called "person_view" that matches the result of the queryset returned from ``get_person_view_qs``.  If you delete the QsView instance the view will be dropped from the database.  