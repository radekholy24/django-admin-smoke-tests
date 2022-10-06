========================
django-admin-smoke-tests
========================

.. image:: https://travis-ci.org/greyside/django-admin-smoke-tests.svg?branch=master
    :target: https://travis-ci.org/greyside/django-admin-smoke-tests
.. image:: https://coveralls.io/repos/greyside/django-admin-smoke-tests/badge.png?branch=master
    :target: https://coveralls.io/r/greyside/django-admin-smoke-tests?branch=master

Run with ``./manage.py test django_admin_smoke_tests.tests``.

You don't have to add anything ``INSTALLED_APPS``

Usage in your tests
-------------------

Import into your own code:

.. code:: python

    from django.test import TestCase
    from django_admin_smoke_tests.tests import AdminSiteSmokeTestMixin

    class AdminSiteSmokeTest(AdminSiteSmokeTestMixin, TestCase):
        def setUp(self):
            super().setUp()
            # custom setup goes here

If you want to use admin smoke tests as part of your tests with data from fixtures,
you can do following:

.. code:: python

    from django.test import TestCase
    from django_admin_smoke_tests.tests import AdminSiteSmokeTestMixin

    class AdminSiteSmokeTest(AdminSiteSmokeTestMixin, TestCase):
        fixtures = ['data']


Creating superuser
^^^^^^^^^^^^^^^^^^

Superuser is created automatically for smoke tests, but in certain cases you may want to override the default behavior:

.. code:: python

    class AdminSiteSmokeTest(AdminSiteSmokeTestMixin, TestCase):
        def create_superuser(self):
            return baker.make(
                "accounts.UserProfile",
                is_superuser=True,
                is_staff=True,
                terms_opt_in=True,
                first_name="Super",
                last_name="user",
            )


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

Model instance creation
-----------------------

Django admin smoke tests automatically creates model instances through ``model_bakery``.
If there is an error during instance creation, it will be ignored with only a warning unless the tests are running in strict mode.

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
