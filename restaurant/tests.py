from datetime import date, time

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TestCase
from django.urls import reverse

from .models import Booking, Table

User = get_user_model()


# Проверяем 12 тестов:
# 1. Корректное количество гостей.
# 2. Нельзя забронировать столик на большее количество гостей,
#    чем предусмотрено мест.
# 3. Нельзя забронировать неактивный столик.
# 4. Нельзя создать два активных бронирования одного столика
#    на одну дату и время.
# 5. Отменённое бронирование не блокирует столик.
# 6. Ограничение UniqueConstraint на уровне базы данных
#    предотвращает дублирование активных бронирований.
# 7. Пользователь не может отменить бронирование другого пользователя.
# 8. Неавторизованный пользователь не может открыть страницу
#    бронирования.
# 9. Авторизованный пользователь может открыть страницу
#    бронирования.
# 10. Авторизованный пользователь может создать бронирование.
# 11. Нельзя создать бронирование, если нет подходящего столика.
# 12. Нельзя создать бронирование на прошедшую дату.


class BookingModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
        )
        self.table = Table.objects.create(
            number=1,
            seats=4,
            is_active=True,
        )
        self.booking_data = {
            "user": self.user,
            "table": self.table,
            "date": date(2026, 9, 10),
            "time": time(19, 0),
            "guests": 2,
        }

    # Проверяем, что бронирование с допустимым количеством гостей
    # успешно проходит валидацию.
    def test_booking_with_valid_guest_count(self):
        booking = Booking(**self.booking_data)

        booking.full_clean()

        self.assertEqual(booking.guests, 2)

    # Проверяем, что нельзя забронировать столик на количество гостей,
    # превышающее количество доступных мест.
    def test_booking_rejects_too_many_guests(self):
        booking_data = self.booking_data.copy()
        booking_data["guests"] = 5

        booking = Booking(**booking_data)

        with self.assertRaises(ValidationError):
            booking.full_clean()

    # Проверяем, что неактивный столик нельзя забронировать.
    def test_booking_rejects_inactive_table(self):
        self.table.is_active = False
        self.table.save()

        booking = Booking(**self.booking_data)

        with self.assertRaises(ValidationError):
            booking.full_clean()

    # Проверяем, что нельзя создать два активных бронирования
    # одного столика на одну дату и время.
    def test_cannot_create_duplicate_active_booking(self):
        Booking.objects.create(**self.booking_data)

        duplicate_booking = Booking(**self.booking_data)

        with self.assertRaises(ValidationError):
            duplicate_booking.full_clean()

    # Проверяем, что отменённое бронирование не блокирует столик
    # и на это же время можно создать новое бронирование.
    def test_cancelled_booking_does_not_block_table(self):
        Booking.objects.create(
            **self.booking_data,
            status="cancelled",
        )

        new_booking = Booking(**self.booking_data)

        new_booking.full_clean()
        new_booking.save()

        self.assertEqual(Booking.objects.count(), 2)

    # Проверяем, что ограничение UniqueConstraint на уровне базы данных
    # предотвращает создание дублирующего активного бронирования.
    def test_database_prevents_duplicate_active_booking(self):
        Booking.objects.create(**self.booking_data)

        duplicate_booking = Booking(**self.booking_data)

        with self.assertRaises(IntegrityError):
            duplicate_booking.save()


class BookingPermissionsTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="user1",
            email="user1@example.com",
            password="testpass123",
        )
        self.other_user = User.objects.create_user(
            username="user2",
            email="user2@example.com",
            password="testpass123",
        )
        self.table = Table.objects.create(
            number=1,
            seats=4,
            is_active=True,
        )
        self.booking = Booking.objects.create(
            user=self.other_user,
            table=self.table,
            date=date(2026, 9, 10),
            time=time(19, 0),
            guests=2,
        )

    # Проверяем, что пользователь не может отменить
    # бронирование другого пользователя.
    def test_user_cannot_cancel_another_users_booking(self):
        self.client.force_login(self.user)

        url = reverse(
            "restaurant:booking_cancel",
            args=[self.booking.id],
        )

        response = self.client.post(url)

        self.booking.refresh_from_db()

        self.assertEqual(response.status_code, 404)
        self.assertEqual(self.booking.status, "pending")

    # Проверяем, что неавторизованный пользователь
    # не может открыть страницу бронирования.
    def test_anonymous_user_cannot_create_booking(self):
        url = reverse("restaurant:booking")

        response = self.client.get(url)

        self.assertEqual(response.status_code, 302)
        self.assertIn("/users/login/", response.url)

    # Проверяем, что авторизованный пользователь
    # может открыть страницу бронирования.
    def test_authenticated_user_can_open_booking_page(self):
        self.client.force_login(self.user)

        url = reverse("restaurant:booking")

        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

    # Проверяем, что авторизованный пользователь
    # может создать бронирование через форму.
    def test_authenticated_user_can_create_booking(self):
        self.client.force_login(self.user)

        url = reverse("restaurant:booking")

        response = self.client.post(
            url,
            {
                "date": "2026-09-15",
                "time": "19:00",
                "guests": 2,
                "comment": "Столик у окна",
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            Booking.objects.filter(
                user=self.user,
                date=date(2026, 9, 15),
                time=time(19, 0),
                guests=2,
                comment="Столик у окна",
            ).exists()
        )

    # Проверяем, что бронирование отклоняется,
    # если нет свободного столика подходящего размера.
    def test_booking_rejected_when_no_suitable_table(self):
        self.client.force_login(self.user)

        url = reverse("restaurant:booking")

        response = self.client.post(
            url,
            {
                "date": "2026-09-15",
                "time": "19:00",
                "guests": 5,
                "comment": "",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            "нет свободного столика подходящего размера",
        )
        self.assertFalse(
            Booking.objects.filter(
                user=self.user,
                date=date(2026, 9, 15),
                time=time(19, 0),
            ).exists()
        )

    # Проверяем, что нельзя создать бронирование
    # на прошедшую дату.
    def test_booking_rejected_for_past_date(self):
        self.client.force_login(self.user)

        url = reverse("restaurant:booking")

        response = self.client.post(
            url,
            {
                "date": "2026-01-01",
                "time": "19:00",
                "guests": 2,
                "comment": "",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            "Нельзя забронировать столик на прошедшую дату.",
        )
        self.assertFalse(
            Booking.objects.filter(
                user=self.user,
                date=date(2026, 1, 1),
            ).exists()
        )
