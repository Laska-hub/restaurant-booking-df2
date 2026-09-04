from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

User = get_user_model()

# 9 тестов проверяют:
# регистрация;
# уникальность email при регистрации;
# успешный вход;
# неправильный пароль;
# доступ к профилю авторизованного пользователя;
# защита профиля от неавторизованных;
# выход;
# редактирование профиля;
# защита уникальности email при редактировании.


class UserRegistrationTest(TestCase):
    # Проверяем, что новый пользователь может успешно зарегистрироваться.
    def test_user_can_register(self):
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

    # Проверяем, что нельзя зарегистрировать двух пользователей
    # с одинаковым email.
    def test_user_cannot_register_with_existing_email(self):
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

    # Проверяем, что зарегистрированный пользователь
    # может успешно войти в аккаунт.
    def test_user_can_login(self):
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

    # Проверяем, что пользователь не может войти
    # с неправильным паролем.
    def test_user_cannot_login_with_wrong_password(self):
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

    # Проверяем, что авторизованный пользователь
    # может открыть свой профиль.
    def test_authenticated_user_can_open_profile(self):
        user = User.objects.create_user(
            username="profileuser",
            email="profile@example.com",
            password="StrongPass123!",
        )

        self.client.force_login(user)

        url = reverse("users:profile")

        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

    # Проверяем, что неавторизованный пользователь
    # не может открыть профиль.
    def test_anonymous_user_cannot_open_profile(self):
        url = reverse("users:profile")

        response = self.client.get(url)

        self.assertEqual(response.status_code, 302)
        self.assertIn("/users/login/", response.url)

    # Проверяем, что пользователь может выйти из аккаунта.
    def test_user_can_logout(self):
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

    # Проверяем, что авторизованный пользователь
    # может изменить данные своего профиля.
    def test_user_can_update_profile(self):
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

    # Проверяем, что пользователь не может изменить email
    # на email, который уже принадлежит другому пользователю.
    def test_user_cannot_update_profile_with_existing_email(self):
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
