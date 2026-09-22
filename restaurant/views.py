from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .forms import BookingForm, FeedbackForm
from .models import (
    Booking,
    Feedback,
    RestaurantImage,
    SiteContent,
)
from .services import get_available_table


@login_required
def booking_create_view(request):
    """
    Создаёт новое бронирование столика.

    Доступна только авторизованным пользователям.
    Форма проверяет данные и наличие подходящего столика,
    после чего создаётся объект Booking и пользователь
    перенаправляется в личный кабинет.
    """
    if request.method == "POST":
        form = BookingForm(request.POST)

        if form.is_valid():
            booking_date = form.cleaned_data["date"]
            booking_time = form.cleaned_data["time"]
            guests = form.cleaned_data["guests"]

            available_table = get_available_table(
                booking_date,
                booking_time,
                guests,
            )

            if available_table:
                Booking.objects.create(
                    user=request.user,
                    table=available_table,
                    date=booking_date,
                    time=booking_time,
                    guests=guests,
                    comment=form.cleaned_data["comment"],
                )

                messages.success(
                    request,
                    f"Бронирование успешно создано! "
                    f"Столик №{available_table.number} "
                    f"забронирован на {booking_date} в {booking_time}.",
                )

                return redirect("users:profile")

    else:
        form = BookingForm()

    return render(
        request,
        "restaurant/booking_form.html",
        {"form": form},
    )


@login_required
def booking_edit_view(request, booking_id):
    """
    Редактирует существующее бронирование пользователя.

    Пользователь может изменить дату, время, количество гостей
    и комментарий. При изменении также выполняется поиск
    подходящего свободного столика.
    """
    booking = get_object_or_404(
        Booking,
        id=booking_id,
        user=request.user,
    )

    if booking.status not in ["pending", "confirmed"]:
        return redirect("users:profile")

    if request.method == "POST":
        form = BookingForm(
            request.POST,
            booking=booking,
        )

        if form.is_valid():
            booking_date = form.cleaned_data["date"]
            booking_time = form.cleaned_data["time"]
            guests = form.cleaned_data["guests"]

            available_table = get_available_table(
                booking_date,
                booking_time,
                guests,
                booking=booking,
            )

            booking.date = booking_date
            booking.time = booking_time
            booking.guests = guests
            booking.comment = form.cleaned_data["comment"]
            booking.table = available_table
            booking.save()

            messages.success(
                request,
                f"Бронирование изменено! "
                f"Столик №{available_table.number} "
                f"забронирован на {booking_date} в {booking_time}.",
            )

            return redirect("users:profile")
    else:
        form = BookingForm(
            initial={
                "date": booking.date,
                "time": booking.time.strftime("%H:%M"),
                "guests": booking.guests,
                "comment": booking.comment,
            },
            booking=booking,
        )

    return render(
        request,
        "restaurant/booking_form.html",
        {
            "form": form,
            "edit_mode": True,
        },
    )


@login_required
def booking_cancel_view(request, booking_id):
    """
    Отменяет бронирование пользователя.

    Отмена выполняется только для активных бронирований
    со статусом pending или confirmed.
    """
    booking = get_object_or_404(
        Booking,
        id=booking_id,
        user=request.user,
    )

    if request.method == "POST" and booking.status in [
        "pending",
        "confirmed",
    ]:
        booking.status = "cancelled"
        booking.save()

    return redirect("users:profile")


def home_view(request):
    """
    Отображает главную страницу ресторана.

    Получает контент сайта из базы данных и обрабатывает
    отправку формы обратной связи.
    """
    content = SiteContent.objects.first()

    if request.method == "POST":
        form = FeedbackForm(request.POST)

        if form.is_valid():
            Feedback.objects.create(
                name=form.cleaned_data["name"],
                email=form.cleaned_data["email"],
                message=form.cleaned_data["message"],
            )

            return redirect("restaurant:home")
    else:
        form = FeedbackForm()

    return render(
        request,
        "restaurant/home.html",
        {
            "form": form,
            "content": content,
        },
    )


def about_view(request):
    """
    Отображает страницу «О ресторане».

    Получает историю, миссию, ценности и информацию
    о команде из базы данных.
    """
    content = SiteContent.objects.first()

    return render(
        request,
        "restaurant/about.html",
        {"content": content},
    )


def menu_view(request):
    """
    Отображает страницу меню ресторана.

    Получает из базы данных изображения, относящиеся
    к категории меню.
    """
    images = RestaurantImage.objects.filter(category="menu")

    return render(
        request,
        "restaurant/menu.html",
        {"images": images},
    )
