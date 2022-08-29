import warnings

from assert_element import AssertElementMixin
from django.contrib import admin
from django.core.exceptions import FieldError
from django.test import TestCase
from model_bakery import baker

from django_admin_smoke_tests.tests import AdminSiteSmokeTestMixin

from .admin import (
    ChannelAdmin,
    FailPostAdmin,
    ForbiddenPostAdmin,
    ListFilter,
    PostAdmin,
)
from .models import Channel, FailPost, HasPrimarySlug, Post, ProxyChannel


class AdminSiteSmokeTest(AdminSiteSmokeTestMixin, TestCase):
    fixtures = []
    exclude_apps = ["auth"]
    exclude_modeladmins = [FailPostAdmin, "ForbiddenPostAdmin"]


class OnlySmokeTest(AdminSiteSmokeTestMixin, TestCase):
    only_apps = ["test_project"]
    only_modeladmins = ["smoke_tests.admin.ChannelAdmin", PostAdmin]


class FailAdminSiteSmokeTest(AdminSiteSmokeTestMixin, TestCase):
    fixtures = []
    exclude_modeladmins = [ForbiddenPostAdmin, PostAdmin, "test_project.ChannelAdmin"]

    def setUp(self):
        FailPost.objects.create(
            channel=Channel.objects.create(),
            author_id=1,
        )
        super(FailAdminSiteSmokeTest, self).setUp()

    def specified_fields_func(self, model, model_admin):
        if model_admin.__class__ == FailPostAdmin:
            with self.assertRaisesRegex(
                AssertionError,
                "False is not true : Field 'nonexistent_field' not found on "
                "test_project.main.models.FailPost \\(main.FailPostAdmin\\)",
            ):
                super().specified_fields_func(model, model_admin)
        else:
            super().specified_fields_func(model, model_admin)

    def changelist_view_search_func(self, model, model_admin):
        if model_admin.__class__ == FailPostAdmin:
            with self.assertRaisesRegex(
                FieldError,
                "Cannot resolve keyword 'nonexistent_field' into field. Choices are: author.*",
            ):
                super().changelist_view_search_func(model, model_admin)
        else:
            super().changelist_view_search_func(model, model_admin)

    def changelist_view_func(self, model, model_admin):
        if model_admin.__class__ == FailPostAdmin:
            with self.assertRaisesRegex(
                Exception, "This exception should be tested for"
            ):
                super().changelist_view_func(model, model_admin)
        else:
            super().changelist_view_func(model, model_admin)


class ForbiddenAdminSiteSmokeTest(AdminSiteSmokeTestMixin, TestCase):
    strict_mode = True
    fixtures = []
    exclude_modeladmins = [FailPostAdmin, PostAdmin, ChannelAdmin]
    print_responses = True


class UnitTest(TestCase):
    maxDiff = None

    def test_strip(self):
        mixin = AdminSiteSmokeTestMixin()
        self.assertEqual(mixin.strip("search_fields", "scene"), "scene")
        self.assertEqual(mixin.strip("search_fields", "^scene"), "scene")
        self.assertEqual(mixin.strip("search_fields", "@scene"), "scene")
        self.assertEqual(mixin.strip("search_fields", "=scene"), "scene")
        self.assertEqual(mixin.strip("ordering", "scene"), "scene")
        self.assertEqual(mixin.strip("ordering", "-scene"), "scene")
        self.assertEqual(mixin.strip("foo", "-scene"), "-scene")

    def test_get_attr_set(self):
        from django_admin_smoke_tests.tests import (
            AdminSiteSmokeTest as OrigAdminSiteSmokeTest,
        )

        test_class = OrigAdminSiteSmokeTest()
        test_class.setUp()
        sites = admin.site._registry.items()
        self.assertSetEqual(
            test_class.get_attr_set(Channel, dict(sites)[Channel]),
            {
                "__str__",
                "slug",
                "title",
                "text",
                "rendered_text",
                "followers",
                "public",
                "enrollment",
                "forbidden_posts__title",
                "post__title",
                "file",
            },
        )
        self.assertSetEqual(
            test_class.get_attr_set(Post, dict(sites)[Post]),
            {
                "time_diff",
                "author",
                "status",
                "id",
                "created",
                "modified",
                "channel",
                "text",
                "title",
                "slug",
                "published",
                "channel__followers__first_name",
                "author__first_name",
                ("custom_summary", admin.DateFieldListFilter),
                ListFilter,
            },
        )


class UnitTestMixin(AssertElementMixin, TestCase):
    def setUp(self):
        self.test_class = AdminSiteSmokeTest()
        self.test_class.setUp()
        self.test_class.client = self.client
        self.sites = admin.site._registry.items()

    def test_has_attr(self):
        self.assertTrue(
            self.test_class.has_attr(
                Channel(), Channel, dict(self.sites)[Channel], "slug"
            )
        )
        self.assertTrue(
            self.test_class.has_attr(Post(), Post, dict(self.sites)[Post], "title")
        )
        self.assertFalse(
            self.test_class.has_attr(
                Post(), Post, dict(self.sites)[Post], "nonexistent_field"
            )
        )
        self.assertFalse(
            self.test_class.has_attr(
                Post, Post, dict(self.sites)[Post], "nonexistent_field"
            )
        )
        self.assertFalse(
            self.test_class.has_attr(
                None, Post, dict(self.sites)[Post], "nonexistent_field"
            )
        )

    def test_specified_fields_func(self):
        self.test_class.specified_fields_func(
            Channel, dict(self.sites)[Channel], baker.make("Channel")
        )
        self.test_class.specified_fields_func(
            Post, dict(self.sites)[Post], baker.make("Post")
        )

    def test_prepare_models(self):
        channels = self.test_class.prepare_models(Channel, ChannelAdmin)
        self.assertTrue(isinstance(channels[0], Channel))

    def test_prepare_models_failure(self):
        class MyAdminSiteSmokeTest(AdminSiteSmokeTest):
            recipes_prefix = "foo"

        test_class = MyAdminSiteSmokeTest()
        with self.assertWarnsRegex(
            Warning,
            "Not able to create test_project.main.models.Channel data.",
        ):
            test_class.prepare_models(Channel, ChannelAdmin)

    def test_prepare_models_recipe(self):
        class MyAdminSiteSmokeTest(AdminSiteSmokeTest):
            recipes_prefix = "test_project.main"

        test_class = MyAdminSiteSmokeTest()
        channels = test_class.prepare_models(Channel, ChannelAdmin)
        self.assertTrue(isinstance(channels[0], Channel))
        self.assertEquals(channels[0].text, "Created by recipe")

    def test_get_absolute_url(self):
        self.test_class.get_absolute_url_func(
            Channel, dict(self.sites)[Channel], baker.make("Channel")
        )
        self.test_class.get_absolute_url_func(
            Post, dict(self.sites)[Post], baker.make("Post")
        )

    def test_change_view_func(self):
        self.test_class.change_view_func(
            Channel, dict(self.sites)[Channel], baker.make("Channel")
        )
        self.test_class.change_view_func(
            Post, dict(self.sites)[Post], baker.make("Post")
        )

    def test_change_view_func_encode_url(self):
        """
        Test with UUID PK that doesn't encode well in URLs.
        The _5B sekvention makes problems if not correctly encoded.
        """
        has_primary_slug = baker.make(
            "HasPrimarySlug", pk="zk5TAeSTSeHY1PNmIaujuk_p7qxxS4ixkNGqC_5Bttfk81_0D6"
        )
        self.test_class.change_view_func(
            HasPrimarySlug,
            dict(self.sites)[HasPrimarySlug],
            has_primary_slug,
        )

    def test_change_post_func(self):
        channel = baker.make("Channel", title="Foo title")
        response = self.test_class.change_post_func(
            Channel, dict(self.sites)[Channel], channel
        )
        self.assertElementContains(
            response,
            "input[id=id_title]",
            '<input type="text" name="title" value="Foo title" class="vTextField" '
            'maxlength="140" required="" id="id_title">',
        )

        post = baker.make("Post", title="Foo post")
        response = self.test_class.change_post_func(Post, dict(self.sites)[Post], post)
        self.assertElementContains(
            response,
            "input[id=id_title]",
            '<input type="text" name="title" value="Foo post" class="vTextField" '
            'maxlength="140" required="" id="id_title">',
        )

    def test_change_post_func_encode_url(self):
        """
        Test with UUID PK that doesn't encode well in URLs.
        The _5B sekvention makes problems if not correctly encoded.
        """
        has_primary_slug = baker.make(
            "HasPrimarySlug", pk="zk5TAeSTSeHY1PNmIaujuk_p7qxxS4ixkNGqC_5Bttfk81_0D6"
        )
        self.test_class.change_post_func(
            HasPrimarySlug,
            dict(self.sites)[HasPrimarySlug],
            has_primary_slug,
        )


class UnitTestMixinNoInstances(TestCase):
    def setUp(self):
        self.sites = admin.site._registry.items()

        class MyAdminSiteSmokeTest(AdminSiteSmokeTest):
            modeladmins = []
            superuser_username = "superuser1"
            only_modeladmins = [ChannelAdmin, "PostAdmin"]

            def prepare_models(self, model, model_admin, quantity=1):
                return

        self.test_class = MyAdminSiteSmokeTest()
        self.test_class.setUp()

    def test_get_absolute_url(self):
        self.test_class.get_absolute_url_func(Channel, dict(self.sites)[Channel])
        self.test_class.get_absolute_url_func(Post, dict(self.sites)[Post])

    def test_specified_fields_func(self):
        with self.assertWarnsRegex(
            Warning,
            "No test_project.main.models.Channel data created to test main.ChannelAdmin.",
        ):
            self.test_class.specified_fields_func(Channel, dict(self.sites)[Channel])
        with self.assertWarnsRegex(
            Warning,
            "No test_project.main.models.Post data created to test main.PostAdmin.",
        ):
            self.test_class.specified_fields_func(Post, dict(self.sites)[Post])

    def test_change_view_func(self):
        with self.assertWarnsRegex(
            Warning,
            "No test_project.main.models.Channel data created to test main.ChannelAdmin.",
        ):
            self.test_class.change_view_func(Channel, dict(self.sites)[Channel])
        with self.assertWarnsRegex(
            Warning,
            "No test_project.main.models.Post data created to test main.PostAdmin.",
        ):
            self.test_class.change_view_func(Post, dict(self.sites)[Post])

    def test_change_post_func(self):
        with self.assertWarnsRegex(
            Warning,
            "No test_project.main.models.Channel data created to test main.ChannelAdmin.",
        ):
            self.test_class.change_post_func(Channel, dict(self.sites)[Channel])
        with warnings.catch_warnings():
            self.test_class.change_post_func(ProxyChannel, dict(self.sites)[Channel])
        with self.assertWarnsRegex(
            Warning,
            "No test_project.main.models.Post data created to test main.PostAdmin.",
        ):
            self.test_class.change_post_func(Post, dict(self.sites)[Post])
