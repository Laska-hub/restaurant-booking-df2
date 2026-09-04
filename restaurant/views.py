from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .forms import BookingForm, FeedbackForm
from .models import (
    Booking,
    Feedback,
    RestaurantImage,
    SiteContent,
    Table,
)

# BookingForm получает дату, время, количество гостей и комментарий.
# Форма через Django ORM проверяет, что подходящий столик существует.
# view снова получает свободные столики.
# .order_by("seats").first() выбирает самый маленький подходящий столик
# — например, для 2 гостей сначала
# возьмём столик на 2 места, а не на 8.
# Booking.objects.create() создаёт настоящее бронирование с конкретным table.
# После успешного бронирования пользователь отправляется в личный кабинет.

# @login_required означает, что неавторизованный пользователь
# не сможет создать бронирование. Это как раз демонстрирует критерий Permissions/Auth.


@login_required
def booking_create_view(request):
    if request.method == "POST":
        form = BookingForm(request.POST)

        if form.is_valid():
            booking_date = form.cleaned_data["date"]
            booking_time = form.cleaned_data["time"]
            guests = form.cleaned_data["guests"]

            available_table = (
                Table.objects.filter(
                    is_active=True,
                    seats__gte=guests,
                )
                .exclude(
                    bookings__date=booking_date,
                    bookings__time=booking_time,
                    bookings__status__in=["pending", "confirmed"],
                )
                .order_by("seats")
                .first()
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

            available_table = (
                Table.objects.filter(
                    is_active=True,
                    seats__gte=guests,
                )
                .exclude(
                    bookings__date=booking_date,
                    bookings__time=booking_time,
                    bookings__status__in=["pending", "confirmed"],
                )
                .order_by("seats")
                .first()
            )

            if available_table is None:
                available_table = booking.table

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
    content = SiteContent.objects.first()

    return render(
        request,
        "restaurant/about.html",
        {"content": content},
    )


def menu_view(request):
    images = RestaurantImage.objects.filter(category="menu")

    return render(
        request,
        "restaurant/menu.html",
        {"images": images},
    )
