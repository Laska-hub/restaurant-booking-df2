from django.contrib import admin

from .models import (
    Booking,
    Feedback,
    RestaurantImage,
    SiteContent,
    Table,
)


@admin.register(Table)
class TableAdmin(admin.ModelAdmin):
    list_display = ("number", "seats", "is_active")
    list_filter = ("is_active",)
    search_fields = ("number",)
    ordering = ("number",)


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = (
        "date",
        "time",
        "table",
        "user",
        "guests",
        "status",
        "created_at",
    )
    list_filter = ("status", "date")
    search_fields = (
        "user__email",
        "table__number",
        "comment",
    )
    ordering = ("-date", "-time")
    list_select_related = ("user", "table")


@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "email",
        "created_at",
    )
    search_fields = (
        "name",
        "email",
        "message",
    )
    ordering = ("-created_at",)


@admin.register(SiteContent)
class SiteContentAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "restaurant_description",
        "history",
        "mission",
    )


@admin.register(RestaurantImage)
class RestaurantImageAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "category",
        "description",
    )
    list_filter = ("category",)
    search_fields = (
        "title",
        "description",
    )
