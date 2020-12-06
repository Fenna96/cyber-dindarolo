from django.test import TestCase

# Create your tests here.
from django.test import SimpleTestCase
from django.urls import reverse,resolve
from community.views import community_profile,change_pic,change_profile,leaderboard,search_page,search_user,modify,index
