from django.test import TestCase, SimpleTestCase
from django.contrib.auth import get_user_model

from .util import (generate_unique_username, generate_base_username, generate_candidate_usernames,)
from .models import BookSearchUser


class BookSearchUserTests(TestCase):

    def test_create_user(self):
        User = get_user_model()
        user = User.objects.create_user(
            username='testuser',
            email='testuser@email.com',
            password='testpass123'
        )
        self.assertEqual(user.username, 'testuser')
        self.assertEqual(user.email, 'testuser@email.com')
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)

    def test_create_superuser(self):
        User = get_user_model()
        superuser = User.objects.create_superuser(
            username='superuser',
            email='superuser@email.com',
            password='testpass123'
        )
        self.assertEqual(superuser.username, 'superuser')
        self.assertEqual(superuser.email, 'superuser@email.com')
        self.assertTrue(superuser.is_active)
        self.assertTrue(superuser.is_staff)
        self.assertTrue(superuser.is_superuser)


class TestGenerateUsernameNoDB(SimpleTestCase):

    def test_generate_base_username(self):
        examples = [
            ("a.b-c@example.com", "a.b-c"),
            ("Üsêrnamê@example.com", "username"),
            ("User Name@drogers.us", "user_name"),
            ("@example.com", "user"),
            ('" "@example.com', "user"),
            ('ab@example.com', "user"),
            ("email.with+symbol@example.com", "email.withsymbol"),
            ("user%example.com@example.org", "userexample.com")
        ]
        for email, expected in examples:
            self.assertEqual(generate_base_username(email), expected)

    def test_generate_candidate_usernames(self):
        basename = 'username'
        candidates = generate_candidate_usernames(basename)
        for i in range(len(candidates)):
            self.assert_(candidates[i].startswith(basename))
            self.assertEqual(len(candidates[i]), len(basename) + i)


class TestGenerateUsername(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.existing_username = 'username'
        cls.email = f'{cls.existing_username}@example.com'
        BookSearchUser.objects.create_user(cls.existing_username,
                                           cls.email,
                                            'TestPass123')

    def test_generate_unique_username_with_name_clash(self):
        username = generate_unique_username(self.email)
        self.assertEqual(len(username), len(self.existing_username) + 1)

    def test_generate_unique_username_with_no_clash(self):
        new_name = 'new_username'
        username = generate_unique_username(f'{new_name}@example.com')
        self.assertEqual(new_name, username)

