from django.test import SimpleTestCase
from django.urls import reverse,resolve
from community.views import community_profile,change_pic,change_profile,leaderboard,search_page,search_user,modify,index

class TestUrls(SimpleTestCase):

    def test_index_url(self):
        self.assertEquals(resolve(reverse('community:index')).func, index)
    def test_leaderboard_url(self):
        self.assertEquals(resolve(reverse('community:leaderboard')).func, leaderboard)
    def test_profile_url(self):
        self.assertEquals(resolve(reverse('community:community_profile',  kwargs={'username':'Martina'})).func, community_profile)
    def test_modify_url(self):
        self.assertEquals(resolve(reverse('community:modify')).func, modify)
    def test_change_profile_url(self):
        self.assertEquals(resolve(reverse('community:change')).func, change_profile)
    def test_change_pic_url(self):
        self.assertEquals(resolve(reverse('community:change_pic')).func, change_pic)
    def test_search_page_url(self):
        self.assertEquals(resolve(reverse('community:search')).func, search_page)
    def test_search_user_url(self):
        self.assertEquals(resolve(reverse('community:search_user')).func, search_user)