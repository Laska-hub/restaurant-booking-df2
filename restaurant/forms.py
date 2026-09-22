from datetime import date, time

from django import forms
from django.core.exceptions import ValidationError

from .services import get_available_table


class BookingForm(forms.Form):
    """
    Форма для создания и редактирования бронирования столика.

    Пользователь указывает дату, время, количество гостей
    и необязательный комментарий.
    """

    date = forms.DateField(
        label="Дата",
        widget=forms.DateInput(
            attrs={
                "type": "date",
                "class": "form-control",
            },
            format="%Y-%m-%d",
        ),
        input_formats=["%Y-%m-%d"],
    )

    time = forms.ChoiceField(
        label="Время",
        choices=[],
        widget=forms.Select(
            attrs={
                "class": "form-select",
            }
        ),
    )

    guests = forms.IntegerField(
        label="Количество гостей",
        min_value=1,
        widget=forms.NumberInput(
            attrs={
                "min": 1,
                "class": "form-control",
            }
        ),
    )

    comment = forms.CharField(
        label="Комментарий",
        required=False,
        widget=forms.Textarea(
            attrs={
                "rows": 3,
                "class": "form-control",
                "placeholder": "Пожелания к бронированию",
            }
        ),
    )

    def __init__(self, *args, booking=None, **kwargs):
        """
        Инициализирует форму и создаёт список доступного времени.

        Параметр booking передаётся при редактировании существующего
        бронирования, чтобы текущий столик учитывался при проверке
        доступности.
        """
        super().__init__(*args, **kwargs)

        self.booking = booking

        self.fields["time"].choices = [
            (
                time(hour=hour, minute=minute).strftime("%H:%M"),
                time(hour=hour, minute=minute).strftime("%H:%M"),
            )
            for hour in range(12, 23)
            for minute in (0, 30)
        ]

    def clean_date(self):
        """
        Проверяет, что дата бронирования не находится в прошлом.
        """
        booking_date = self.cleaned_data["date"]

        if booking_date < date.today():
            raise ValidationError("Нельзя забронировать столик на прошедшую дату.")

        return booking_date

    def clean(self):
        """
        Проверяет наличие свободного столика для выбранных параметров.

        Использует общую функцию get_available_table(), чтобы логика
        поиска свободного столика не дублировалась в форме и views.
        """
        cleaned_data = super().clean()

        booking_date = cleaned_data.get("date")
        booking_time = cleaned_data.get("time")
        guests = cleaned_data.get("guests")

        if not booking_date or not booking_time or not guests:
            return cleaned_data

        booking_time = time.fromisoformat(booking_time)

        available_table = get_available_table(
            booking_date,
            booking_time,
            guests,
            booking=self.booking,
        )

        if not available_table:
            raise ValidationError(
                "На выбранные дату и время нет свободного столика "
                "подходящего размера."
            )

        return cleaned_data


class FeedbackForm(forms.Form):
    """
    Форма обратной связи с посетителем ресторана.
    """

    name = forms.CharField(
        label="Имя",
        max_length=100,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Ваше имя",
            }
        ),
    )

    email = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(
            attrs={
                "class": "form-control",
                "placeholder": "Ваш email",
            }
        ),
    )

    message = forms.CharField(
        label="Сообщение",
        widget=forms.Textarea(
            attrs={
                "rows": 4,
                "class": "form-control",
                "placeholder": "Ваше сообщение",
            }
        ),
    )
