from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views.generic import CreateView

from .forms import ProfileUpdateForm, UserRegistrationForm


class RegisterView(CreateView):
    form_class = UserRegistrationForm
    template_name = "users/register.html"
    success_url = reverse_lazy("users:login")


class LoginView(auth_views.LoginView):
    template_name = "users/login.html"


@login_required
def profile_view(request):
    bookings = request.user.bookings.select_related("table").all()

    if request.method == "POST":
        form = ProfileUpdateForm(
            request.POST,
            instance=request.user,
        )

        if form.is_valid():
            form.save()
            return redirect("users:profile")
    else:
        form = ProfileUpdateForm(instance=request.user)

    return render(
        request,
        "users/profile.html",
        {
            "bookings": bookings,
            "form": form,
        },
    )
