from datetime import date, time

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TestCase
from django.urls import reverse

from .models import Booking, Table

User = get_user_model()


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

    def test_booking_with_valid_guest_count(self):
        """Проверяет бронирование с допустимым количеством гостей."""
        booking = Booking(**self.booking_data)

        booking.full_clean()

        self.assertEqual(booking.guests, 2)

    def test_booking_rejects_too_many_guests(self):
        """
        Проверяет, что нельзя забронировать столик
        для слишком большого числа гостей.
        """
        booking_data = self.booking_data.copy()
        booking_data["guests"] = 5

        booking = Booking(**booking_data)

        with self.assertRaises(ValidationError):
            booking.full_clean()

    def test_booking_rejects_inactive_table(self):
        """Проверяет, что неактивный столик нельзя забронировать."""
        self.table.is_active = False
        self.table.save()

        booking = Booking(**self.booking_data)

        with self.assertRaises(ValidationError):
            booking.full_clean()

    def test_cannot_create_duplicate_active_booking(self):
        """
        Проверяет, что нельзя создать два активных бронирования
        одного столика на одну дату и время.
        """
        Booking.objects.create(**self.booking_data)

        duplicate_booking = Booking(**self.booking_data)

        with self.assertRaises(ValidationError):
            duplicate_booking.full_clean()

    def test_cancelled_booking_does_not_block_table(self):
        """Проверяет, что отменённое бронирование не блокирует столик."""
        Booking.objects.create(
            **self.booking_data,
            status="cancelled",
        )

        new_booking = Booking(**self.booking_data)

        new_booking.full_clean()
        new_booking.save()

        self.assertEqual(Booking.objects.count(), 2)

    def test_database_prevents_duplicate_active_booking(self):
        """
        Проверяет, что ограничение базы данных предотвращает
        дублирование активных бронирований.
        """
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

    def test_user_cannot_cancel_another_users_booking(self):
        """
        Проверяет, что пользователь не может отменить
        чужое бронирование.
        """
        self.client.force_login(self.user)

        url = reverse(
            "restaurant:booking_cancel",
            args=[self.booking.id],
        )

        response = self.client.post(url)

        self.booking.refresh_from_db()

        self.assertEqual(response.status_code, 404)
        self.assertEqual(self.booking.status, "pending")

    def test_anonymous_user_cannot_create_booking(self):
        """
        Проверяет, что неавторизованный пользователь
        не может открыть страницу бронирования.
        """
        url = reverse("restaurant:booking")

        response = self.client.get(url)

        self.assertEqual(response.status_code, 302)
        self.assertIn("/users/login/", response.url)

    def test_authenticated_user_can_open_booking_page(self):
        """
        Проверяет, что авторизованный пользователь
        может открыть страницу бронирования.
        """
        self.client.force_login(self.user)

        url = reverse("restaurant:booking")

        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

    def test_authenticated_user_can_create_booking(self):
        """
        Проверяет, что авторизованный пользователь
        может создать бронирование через форму.
        """
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

    def test_booking_rejected_when_no_suitable_table(self):
        """
        Проверяет, что бронирование отклоняется при отсутствии
        подходящего свободного столика.
        """
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

    def test_booking_rejected_for_past_date(self):
        """Проверяет, что нельзя создать бронирование на прошедшую дату."""
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
