from .models import Table


def get_available_table(booking_date, booking_time, guests, booking=None):
    """
    Находит самый маленький свободный столик подходящего размера.
    При редактировании текущий столик бронирования также считается доступным.
    """
    available_tables = (
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
    )

    if booking:
        current_table = Table.objects.filter(
            id=booking.table_id,
            is_active=True,
            seats__gte=guests,
        )

        available_tables = available_tables | current_table

    return available_tables.order_by("seats").first()
