from django.contrib import admin

from .models import Booking, Table


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

