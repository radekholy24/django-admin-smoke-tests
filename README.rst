========================
django-admin-smoke-tests
========================

.. image:: https://travis-ci.org/greyside/django-admin-smoke-tests.svg?branch=master
    :target: https://travis-ci.org/greyside/django-admin-smoke-tests
.. image:: https://coveralls.io/repos/greyside/django-admin-smoke-tests/badge.png?branch=master
    :target: https://coveralls.io/r/greyside/django-admin-smoke-tests?branch=master

The goal of `django-admin-smoke-tests` application is to create some testing models (with ``model_bakery``) and run tests admin views of your admin site with minimal configuration needed.

In ideal case you should just need these steps:

1. Install the application with ``pip install django-admin-smoke-tests``
2. run ``python manage.py test django_admin_smoke_tests.tests``

You don't have to add anything ``INSTALLED_APPS`` or ``urls.py``.

Although many models can be created without problem, there might be needed some additional configuration in some cases.

Basic configuration
-------------------

Creating superuser
^^^^^^^^^^^^^^^^^^

The ``get_user_model().objects.create_superuser`` method is used to create superuser.
Please make sure, that this method does create superuser that is capable of entering you admin site.
If your app needs some additional fields to be set or code to be executed, override this method:

.. code:: python

    from django.db import models
    from django.contrib.auth.models import AbstractUser
    
    class UserProfileManager(models.Manager):
        def create_superuser(self, *args, **kwargs):
            return super().create_superuser(
                *args,
                **kwargs,
                terms_opt_in=True,
                first_name="Super",
                last_name="user",
            )
            
            
    class UserProfile(AbstractUser):
        objects = UserProfileManager()
        ...

Printing view results
^^^^^^^^^^^^^^^^^^^^^

In order to see the view rendered results, you can run the tests with ``SMOKE_TESTS_PRINT_RESPONSES=True`` env variable:

.. code:: bash
    
    SMOKE_TESTS_PRINT_RESPONSES=True python manage.py test django_admin_smoke_tests.tests

In the root director should be created HTML files like ``response_Group_auth.GroupAdmin_changelist_view_search.html``.

Customized test run
-------------------

Use the ``AdminSiteSmokeTestMixin`` to create your own testing class:

.. code:: python

    from django.test import TestCase
    from django_admin_smoke_tests.tests import AdminSiteSmokeTestMixin

    class AdminSiteSmokeTest(AdminSiteSmokeTestMixin, TestCase):
        def setUp(self):
            super().setUp()
            # custom setup goes here


Restricting tests
^^^^^^^^^^^^^^^^^

And you can exclude certain (external) apps or model admins with:

.. code:: python

    class AdminSiteSmokeTest(AdminSiteSmokeTestMixin, TestCase):
        exclude_apps = ['constance',]
        exclude_modeladmins = [apps.admin.ModelAdmin]


Or test only certain apps or model admins with:

.. code:: python

    class AdminSiteSmokeTest(AdminSiteSmokeTestMixin, TestCase):
        only_apps = ['constance',]
        only_modeladmins = [ChannelAdmin, "PostAdmin"]


The modeladmin lists can contain: class, class name, class path.

Customizing testing data
------------------------

Django admin smoke tests automatically creates model instances through ``model_bakery``.
If there is an error during instance creation, it will be ignored with only a warning unless the tests are running in strict mode.

Fixtures
^^^^^^^^

You can use fixtures as for any other TestCase:

.. code:: python

    from django.test import TestCase
    from django_admin_smoke_tests.tests import AdminSiteSmokeTestMixin

    class AdminSiteSmokeTest(AdminSiteSmokeTestMixin, TestCase):
        fixtures = ['data']
        

Customization
^^^^^^^^^^^^^

You can customize how ``model_bakery`` creates model instances by setting recipes. E.g. create file ``bakery_recipes.py`` in your test directory with following content:

.. code:: python

    from model_bakery.recipe import Recipe
        Channel = Recipe("Channel", text="Created by recipe")

And set ``recipes_prefix`` to your smoke tests with path to the recipes:

.. code:: python

    class MyAdminSiteSmokeTest(AdminSiteSmokeTestMixin, TestCase):
        recipes_prefix = "test_project.main"

You can also set up your own models by overriding ``prepare_all_models()`` classmethod:

.. code:: python

    class AdminSiteSmokeTest(AdminSiteSmokeTestMixin, TestCase):
        @classmethod      
        def prepare_all_models(cls):
            baker.make("plans.Plan", name="Default plan", default=True)
            super().prepare_all_models()   


Strict mode
^^^^^^^^^^^

Strict mode raises exceptions during model instance creation and if instances are not found when testing some admin views.
To enable strict mode, set ``strict_mode`` property:

.. code:: python

    class AdminSiteSmokeTest(AdminSiteSmokeTestMixin, TestCase):
        strict_mode = True
