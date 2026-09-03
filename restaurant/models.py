from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q


class Table(models.Model):
    number = models.PositiveIntegerField(
        unique=True,
        verbose_name="Номер столика",
    )
    seats = models.PositiveIntegerField(
        verbose_name="Количество мест",
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Доступен",
    )

    class Meta:
        ordering = ["number"]
        verbose_name = "Столик"
        verbose_name_plural = "Столики"

    def __str__(self):
        return f"Столик №{self.number}"


class Booking(models.Model):
    STATUS_CHOICES = [
        ("pending", "Ожидает подтверждения"),
        ("confirmed", "Подтверждено"),
        ("cancelled", "Отменено"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="bookings",
        verbose_name="Пользователь",
    )
    table = models.ForeignKey(
        Table,
        on_delete=models.CASCADE,
        related_name="bookings",
        verbose_name="Столик",
    )
    date = models.DateField(verbose_name="Дата")
    time = models.TimeField(verbose_name="Время")
    guests = models.PositiveIntegerField(
        verbose_name="Количество гостей",
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending",
        verbose_name="Статус",
    )
    comment = models.TextField(
        blank=True,
        verbose_name="Комментарий",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date", "-time"]
        verbose_name = "Бронирование"
        verbose_name_plural = "Бронирования"
        constraints = [
            models.UniqueConstraint(
                fields=["table", "date", "time"],
                condition=Q(status__in=["pending", "confirmed"]),
                name="unique_active_table_booking",
            ),
        ]

    def clean(self):
        if self.table_id:
            if not self.table.is_active:
                raise ValidationError("Этот столик сейчас недоступен для бронирования.")

            if self.guests > self.table.seats:
                raise ValidationError(
                    f"Столик рассчитан максимум на " f"{self.table.seats} гостей."
                )

    def __str__(self):
        return (
            f"{self.date} {self.time} — "
            f"столик №{self.table.number} — {self.user.email}"
        )
