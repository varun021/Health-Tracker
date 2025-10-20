from django.test import TestCase
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model

User = get_user_model()


class UsersAPITests(APITestCase):
    def setUp(self):
        # create a user for login/logout tests
        self.user = User.objects.create_user(
            username="johndoe",
            email="john@example.com",
            password="strongpassword123"
        )
        self.register_url = "/api/users/register/"
        self.login_url = "/api/users/login/"
        self.logout_url = "/api/users/logout/"
        self.me_url = "/api/users/me/"
        self.refresh_url = "/api/users/refresh/"

    def test_register_success(self):
        data = {
            "username": "alice",
            "email": "alice@example.com",
            "password": "securepass123"
        }
        resp = self.client.post(self.register_url, data, format="json")
        assert resp.status_code == 201
        assert User.objects.filter(username="alice").exists()

    def test_register_duplicate_email_or_username(self):
        # username duplicate
        resp1 = self.client.post(self.register_url, {
            "username": "johndoe",
            "email": "newemail@example.com",
            "password": "anotherpass123"
        }, format="json")
        assert resp1.status_code == 400

        # email duplicate
        resp2 = self.client.post(self.register_url, {
            "username": "newuser",
            "email": "john@example.com",
            "password": "anotherpass123"
        }, format="json")
        assert resp2.status_code == 400

    def test_login_sets_tokens_in_cookies(self):
        resp = self.client.post(self.login_url, {
            "username": "johndoe",
            "password": "strongpassword123"
        }, format="json")
        assert resp.status_code == 200
        # cookies set by view
        assert "access_token" in resp.cookies
        assert "refresh_token" in resp.cookies

    def test_login_with_email(self):
        resp = self.client.post(self.login_url, {
            "username": "john@example.com",
            "password": "strongpassword123"
        }, format="json")
        assert resp.status_code == 200
        assert "access_token" in resp.cookies

    def test_me_with_valid_access_cookie(self):
        login = self.client.post(self.login_url, {
            "username": "johndoe",
            "password": "strongpassword123"
        }, format="json")
        access = login.cookies.get("access_token").value
        refresh = login.cookies.get("refresh_token").value
        # set cookies on client
        self.client.cookies["access_token"] = access
        self.client.cookies["refresh_token"] = refresh

        resp = self.client.get(self.me_url)
        assert resp.status_code == 200
        assert resp.data.get("username") == "johndoe"
        assert resp.data.get("refreshed") is False

    def test_me_refreshes_access_when_access_invalid_but_refresh_valid(self):
        login = self.client.post(self.login_url, {
            "username": "johndoe",
            "password": "strongpassword123"
        }, format="json")
        refresh = login.cookies.get("refresh_token").value
        # set an invalid access token and the valid refresh token
        self.client.cookies["access_token"] = "invalid-token"
        self.client.cookies["refresh_token"] = refresh

        resp = self.client.get(self.me_url)
        # should refresh using refresh cookie and return 200 with refreshed True
        assert resp.status_code == 200
        assert resp.data.get("refreshed") is True
        # new access token should be set in response cookies
        assert "access_token" in resp.cookies

    def test_logout_requires_auth_and_returns_ok(self):
        # use force_authenticate so permission IsAuthenticated passes
        self.client.force_authenticate(user=self.user)
        resp = self.client.post(self.logout_url, {}, format="json")
        assert resp.status_code == 200
        assert resp.data.get("message") == "Logged out successfully"
