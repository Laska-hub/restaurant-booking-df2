from django.urls import path

from .views import (
    about_view,
    booking_cancel_view,
    booking_create_view,
    home_view,
)

app_name = "restaurant"

urlpatterns = [
    path("", home_view, name="home"),
    path("about/", about_view, name="about"),
    path("booking/", booking_create_view, name="booking"),
    path(
        "booking/<int:booking_id>/cancel/",
        booking_cancel_view,
        name="booking_cancel",
    ),
]
