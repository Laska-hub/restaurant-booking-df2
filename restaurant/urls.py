from django.urls import path

from .views import (
    about_view,
    booking_cancel_view,
    booking_create_view,
    booking_edit_view,
    home_view,
    menu_view,
)

app_name = "restaurant"

urlpatterns = [
    path("", home_view, name="home"),
    path("about/", about_view, name="about"),
    path("booking/", booking_create_view, name="booking"),
    path(
        "booking/<int:booking_id>/edit/",
        booking_edit_view,
        name="booking_edit",
    ),
    path(
        "booking/<int:booking_id>/cancel/",
        booking_cancel_view,
        name="booking_cancel",
    ),
    path("menu/", menu_view, name="menu"),
]
