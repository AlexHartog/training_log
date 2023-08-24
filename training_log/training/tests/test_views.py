from django.contrib.auth.models import User
from django.test import LiveServerTestCase, TestCase
from django.urls import reverse
from selenium import webdriver
from selenium.webdriver.common.by import By


class TestViews(TestCase):
    def setUp(self):
        self.username = "test_user"
        self.password = "test_pw"
        self.user = User.objects.create_user(
            username=self.username, password=self.password
        )

        self.client.login(username=self.username, password=self.password)

    def test_session_list_view(self):
        url = reverse("session-list", kwargs={"username": self.username})
        resp = self.client.get(url)

        # TODO: Can we do some tests on content?
        self.assertEqual(resp.status_code, 200)

    def test_incorrect_user_list_view(self):
        url = reverse("session-list", kwargs={"username": "incorrect_user"})
        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 404)

    def test_session_detail_view(self):
        url = reverse("session-detail", kwargs={"pk": 2})
        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 404)


class TestSignUp(LiveServerTestCase):
    def setUp(self):
        self.driver = webdriver.Chrome()

    def test_signup_fire(self):
        self.driver.get(self.live_server_url + "/register/")
        self.driver.find_element(By.ID, "id_username").send_keys("testuser")
        self.driver.find_element(By.ID, "id_password1").send_keys("testpass123")
        self.driver.find_element(By.ID, "id_password2").send_keys("testpass123")
        self.driver.find_element(By.ID, "id_password2").submit()

        self.assertIn(
            self.live_server_url + "/register/success/", self.driver.current_url
        )

    def tearDown(self):
        self.driver.quit()
