from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .forms import BookingForm
from .models import Booking, Table

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

                return redirect("users:profile")

    else:
        form = BookingForm()

    return render(
        request,
        "restaurant/booking_form.html",
        {"form": form},
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
    return render(request, "restaurant/home.html")


def about_view(request):
    return render(request, "restaurant/about.html")
