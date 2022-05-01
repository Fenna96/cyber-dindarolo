import pprint

from django.test import TestCase, Client
from django.urls import reverse
from manager.models import (
    Category,
    Product,
    Product_pricetracker,
    Balance,
    BALANCE_LIMIT,
    CatalogItem,
    User,
    Transaction,
)
from user.models import Profile, DEFAULT_PIC_FILE
from django.core.files.uploadedfile import SimpleUploadedFile


class TestViews(TestCase):
    def setUp(self):
        self.client = Client()
        # Fake user setup
        self.username = "Martina"
        self.password = "marti"
        user = User.objects.create(username=self.username)
        user.email = "marti.levizzani@gmail.com"
        user.set_password(self.password)
        user.save()
        # setting up his balance to 200
        balance = Balance.objects.create(
            user=User.objects.get(username=self.username), balance=200
        )

        Profile.objects.create(
            user=User.objects.get(username=self.username),
            name="Martina",
            surname="Levizzani",
            biography="-",
            mobile=3384014188,
        ).save()

        self.redirect_url = "/?next="
        self.index_url = reverse("community:index")
        self.leaderboard_url = reverse("community:leaderboard")
        self.community_profile_url = reverse(
            "community:community_profile", kwargs={"username": "Martina"}
        )
        self.modify_url = reverse("community:modify")
        self.change_profile_url = reverse("community:change")
        self.change_pic_url = reverse("community:change_pic")
        self.search_url = reverse("community:search")
        self.search_user_url = reverse("community:search_user")

    def test_index_methods(self):
        # Testing redirection
        get_response = self.client.get(self.index_url)
        self.assertEquals(get_response.status_code, 302)

        self.client.login(username=self.username, password=self.password)
        get_response = self.client.get(self.index_url)
        post_response = self.client.post(self.index_url)

        self.assertEquals(get_response.status_code, 200)
        self.assertEquals(post_response.status_code, 302)

        self.client.logout()

    def test_leaderboard_methods(self):
        # Testing redirection
        get_response = self.client.get(self.leaderboard_url)
        self.assertEquals(get_response.status_code, 302)

        self.client.login(username=self.username, password=self.password)
        get_response = self.client.get(self.leaderboard_url)
        post_response = self.client.post(self.leaderboard_url)

        self.assertEquals(get_response.status_code, 200)
        self.assertEquals(post_response.status_code, 302)

        self.client.logout()

    def test_community_profile_methods(self):
        # Testing redirection
        get_response = self.client.get(self.community_profile_url)
        self.assertEquals(get_response.status_code, 302)

        self.client.login(username=self.username, password=self.password)
        get_response = self.client.get(self.community_profile_url)
        post_response = self.client.post(self.community_profile_url)

        self.assertEquals(get_response.status_code, 200)
        self.assertEquals(post_response.status_code, 302)

        self.client.logout()

    def test_community_profile_is_you(self):
        self.client.login(username=self.username, password=self.password)

        get_response = self.client.get(self.community_profile_url)

        self.assertTrue(
            get_response.context["yourself"]
        )  # no profile or balance created
        self.client.logout()

    def test_community_profile_is_not_you(self):
        self.client.login(username=self.username, password=self.password)

        User.objects.create(username="Fenna96").save()
        Balance.objects.create(
            user=User.objects.get(username="Fenna96"), balance=10
        ).save()
        Profile.objects.create(
            user=User.objects.get(username="Fenna96"),
            name="Martina",
            surname="Levizzani",
            biography="-",
            mobile=3384014188,
        ).save()

        get_response = self.client.get(
            reverse("community:community_profile", kwargs={"username": "Fenna96"})
        )

        try:
            get_response.context["yourself"]
            self.assertTrue(0)
        except:
            self.assertTrue(1)
        self.client.logout()

    def test_modify_methods(self):
        # Testing redirection
        get_response = self.client.get(self.modify_url)
        self.assertEquals(get_response.status_code, 302)

        self.client.login(username=self.username, password=self.password)
        get_response = self.client.get(self.modify_url)
        post_response = self.client.post(self.modify_url)

        self.assertEquals(get_response.status_code, 200)
        self.assertEquals(post_response.status_code, 302)

        self.client.logout()

    def test_change_profile_methods(self):
        # Testing redirection
        get_response = self.client.get(self.change_profile_url)
        self.assertEquals(get_response.status_code, 302)

        self.client.login(username=self.username, password=self.password)
        get_response = self.client.get(self.change_profile_url)
        post_response = self.client.post(self.change_profile_url)

        self.assertEquals(get_response.status_code, 302)
        self.assertEquals(post_response.status_code, 302)
        self.assertRedirects(
            get_response,
            self.modify_url,
            status_code=302,
            target_status_code=200,
            fetch_redirect_response=True,
        )

        self.client.logout()

    def test_valid_changed_profile(self):
        self.client.login(username=self.username, password=self.password)

        user = User.objects.get(username=self.username)

        post_response = self.client.post(
            self.change_profile_url,
            {
                "username": self.username,
                "email": user.email,
                "password": user.password,
                "name": "Martina",
                "surname": "Levizzani",
                "biography": "Nuova biography",
                "mobile": 3384014188,
            },
            follow=True,
        )

        new_profile = Profile.objects.get(user=User.objects.get(username=self.username))
        self.assertEquals(new_profile.biography, "Nuova biography")
        self.assertRedirects(
            post_response,
            self.community_profile_url,
            status_code=302,
            target_status_code=200,
            fetch_redirect_response=True,
        )

    def test_email_taken_changed_profile(self):
        self.client.login(username=self.username, password=self.password)

        user = User.objects.get(username=self.username)
        new_user = User.objects.create(username="Fenna96")
        new_user.email = "fenna.mercalli@gmail.com"
        new_user.save()

        post_response = self.client.post(
            self.change_profile_url,
            {
                "username": self.username,
                "email": "fenna.mercalli@gmail.com",
                "password": user.password,
                "name": "Martina",
                "surname": "Levizzani",
                "biography": "Nuova biography",
                "mobile": 3384014188,
            },
            follow=True,
        )

        new_profile = Profile.objects.get(user=User.objects.get(username=self.username))
        self.assertRedirects(
            post_response,
            self.modify_url + "Email%20taken%20by%20another%20user,%20we're%20sorry",
            status_code=302,
            target_status_code=200,
            fetch_redirect_response=True,
        )

    def test_invalid_form_changed_profile(self):
        self.client.login(username=self.username, password=self.password)

        user = User.objects.get(username=self.username)

        post_response = self.client.post(
            self.change_profile_url,
            {
                "email": "fenna.mercalli@gmail.com",
                "password": user.password,
                "name": "Martina",
                "surname": "Levizzani",
                "biography": "Nuova biography",
                "mobile": 3384014188,
            },
        )

        new_profile = Profile.objects.get(user=User.objects.get(username=self.username))
        self.assertEquals(post_response.request["PATH_INFO"], self.change_profile_url)

    def test_change_pic_methods(self):
        # Testing redirection
        get_response = self.client.get(self.change_pic_url)
        self.assertEquals(get_response.status_code, 302)

        self.client.login(username=self.username, password=self.password)
        get_response = self.client.get(self.change_pic_url)
        post_response = self.client.post(self.change_pic_url)

        self.assertEquals(get_response.status_code, 302)
        self.assertEquals(post_response.status_code, 302)
        self.assertRedirects(
            get_response,
            self.modify_url,
            status_code=302,
            target_status_code=200,
            fetch_redirect_response=True,
        )
        self.assertRedirects(
            post_response,
            self.community_profile_url,
            status_code=302,
            target_status_code=200,
            fetch_redirect_response=True,
        )

        self.client.logout()

    def test_valid_changed_pic(self):
        self.client.login(username=self.username, password=self.password)

        user = User.objects.get(username=self.username)
        f = SimpleUploadedFile("file.txt", b"file_content")

        post_response = self.client.post(
            self.change_pic_url, {"profile_image": f}, follow=True
        )

        new_profile = Profile.objects.get(user=User.objects.get(username=self.username))
        self.assertNotEquals(new_profile.profile_image.name, DEFAULT_PIC_FILE)
        self.assertRedirects(
            post_response,
            self.community_profile_url,
            status_code=302,
            target_status_code=200,
            fetch_redirect_response=True,
        )

    def test_default_changed_pic(self):
        self.client.login(username=self.username, password=self.password)

        user = User.objects.get(username=self.username)
        f = SimpleUploadedFile("file.txt", b"file_content")

        post_response = self.client.post(self.change_pic_url, {}, follow=True)

        new_profile = Profile.objects.get(user=User.objects.get(username=self.username))
        self.assertEquals(new_profile.profile_image.name, DEFAULT_PIC_FILE)
        self.assertRedirects(
            post_response,
            self.community_profile_url,
            status_code=302,
            target_status_code=200,
            fetch_redirect_response=True,
        )

    def test_search_methods(self):
        # Testing redirection
        get_response = self.client.get(self.search_url)
        self.assertEquals(get_response.status_code, 302)

        self.client.login(username=self.username, password=self.password)
        get_response = self.client.get(self.search_url)
        post_response = self.client.post(self.search_url)

        self.assertEquals(get_response.status_code, 200)
        self.assertEquals(post_response.status_code, 302)

        self.client.logout()

    def test_search_user_methods(self):
        # Testing redirection
        get_response = self.client.get(self.search_user_url)
        self.assertEquals(get_response.status_code, 302)

        self.client.login(username=self.username, password=self.password)
        get_response = self.client.get(self.search_user_url)
        post_response = self.client.post(self.search_user_url)

        self.assertEquals(get_response.status_code, 302)
        self.assertEquals(post_response.status_code, 302)
        self.assertRedirects(
            get_response,
            self.search_url,
            status_code=302,
            target_status_code=200,
            fetch_redirect_response=True,
        )
        self.client.logout()

    def test_search_user_no_username_given(self):
        self.client.login(username=self.username, password=self.password)
        post_response = self.client.post(self.search_user_url)

        self.assertEquals(post_response.status_code, 302)
        self.assertRedirects(
            post_response,
            self.search_url + "No%20username%20given",
            status_code=302,
            target_status_code=200,
            fetch_redirect_response=True,
        )
        self.client.logout()

    def test_search_user_valid_user_given(self):
        self.client.login(username=self.username, password=self.password)
        post_response = self.client.post(self.search_user_url, {"username": "Martina"})

        self.assertEquals(post_response.status_code, 302)
        self.assertRedirects(
            post_response,
            self.community_profile_url,
            status_code=302,
            target_status_code=200,
            fetch_redirect_response=True,
        )
        self.client.logout()

    def test_search_user_invalid_user_given(self):
        self.client.login(username=self.username, password=self.password)
        post_response = self.client.post(self.search_user_url, {"username": "Martina2"})

        self.assertEquals(post_response.status_code, 302)
        self.assertRedirects(
            post_response,
            self.search_url + "User%20not%20found",
            status_code=302,
            target_status_code=200,
            fetch_redirect_response=True,
        )
        self.client.logout()
