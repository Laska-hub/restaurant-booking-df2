from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

User = get_user_model()


class UserRegistrationTest(TestCase):
    def test_user_can_register(self):
        """Проверяет, что новый пользователь может успешно зарегистрироваться."""
        url = reverse("users:register")

        response = self.client.post(
            url,
            {
                "username": "newuser",
                "email": "newuser@example.com",
                "password1": "StrongPass123!",
                "password2": "StrongPass123!",
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            User.objects.filter(
                username="newuser",
                email="newuser@example.com",
            ).exists()
        )

    def test_user_cannot_register_with_existing_email(self):
        """
        Проверяет, что нельзя зарегистрировать двух пользователей
        с одинаковым email.
        """
        User.objects.create_user(
            username="existinguser",
            email="existing@example.com",
            password="StrongPass123!",
        )

        url = reverse("users:register")

        response = self.client.post(
            url,
            {
                "username": "newuser",
                "email": "existing@example.com",
                "password1": "StrongPass123!",
                "password2": "StrongPass123!",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(User.objects.count(), 1)

    def test_user_can_login(self):
        """
        Проверяет, что зарегистрированный пользователь
        может успешно войти в аккаунт.
        """
        User.objects.create_user(
            username="loginuser",
            email="login@example.com",
            password="StrongPass123!",
        )

        url = reverse("users:login")

        response = self.client.post(
            url,
            {
                "username": "loginuser",
                "password": "StrongPass123!",
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.wsgi_request.user.is_authenticated)

    def test_user_cannot_login_with_wrong_password(self):
        """
        Проверяет, что пользователь не может войти
        с неправильным паролем.
        """
        User.objects.create_user(
            username="loginuser",
            email="login@example.com",
            password="StrongPass123!",
        )

        url = reverse("users:login")

        response = self.client.post(
            url,
            {
                "username": "loginuser",
                "password": "WrongPassword123!",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.wsgi_request.user.is_authenticated)

    def test_authenticated_user_can_open_profile(self):
        """
        Проверяет, что авторизованный пользователь
        может открыть свой профиль.
        """
        user = User.objects.create_user(
            username="profileuser",
            email="profile@example.com",
            password="StrongPass123!",
        )

        self.client.force_login(user)

        url = reverse("users:profile")

        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

    def test_anonymous_user_cannot_open_profile(self):
        """
        Проверяет, что неавторизованный пользователь
        не может открыть профиль.
        """
        url = reverse("users:profile")

        response = self.client.get(url)

        self.assertEqual(response.status_code, 302)
        self.assertIn("/users/login/", response.url)

    def test_user_can_logout(self):
        """Проверяет, что пользователь может выйти из аккаунта."""
        user = User.objects.create_user(
            username="logoutuser",
            email="logout@example.com",
            password="StrongPass123!",
        )

        self.client.force_login(user)

        url = reverse("users:logout")

        response = self.client.post(url)

        self.assertEqual(response.status_code, 302)
        self.assertFalse(response.wsgi_request.user.is_authenticated)

    def test_user_can_update_profile(self):
        """
        Проверяет, что авторизованный пользователь
        может изменить данные своего профиля.
        """
        user = User.objects.create_user(
            username="profileuser",
            email="old@example.com",
            password="StrongPass123!",
        )

        self.client.force_login(user)

        url = reverse("users:profile")

        response = self.client.post(
            url,
            {
                "first_name": "Иван",
                "last_name": "Иванов",
                "email": "new@example.com",
            },
        )

        self.assertEqual(response.status_code, 302)

        user.refresh_from_db()

        self.assertEqual(user.first_name, "Иван")
        self.assertEqual(user.last_name, "Иванов")
        self.assertEqual(user.email, "new@example.com")

    def test_user_cannot_update_profile_with_existing_email(self):
        """
        Проверяет, что пользователь не может изменить email
        на email другого пользователя.
        """
        User.objects.create_user(
            username="existinguser",
            email="existing@example.com",
            password="StrongPass123!",
        )

        user = User.objects.create_user(
            username="profileuser",
            email="profile@example.com",
            password="StrongPass123!",
        )

        self.client.force_login(user)

        url = reverse("users:profile")

        response = self.client.post(
            url,
            {
                "first_name": "Иван",
                "last_name": "Иванов",
                "email": "existing@example.com",
            },
        )

        self.assertEqual(response.status_code, 200)

        user.refresh_from_db()

        self.assertEqual(user.email, "profile@example.com")
        self.assertEqual(user.first_name, "")
        self.assertEqual(user.last_name, "")
