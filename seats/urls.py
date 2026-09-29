from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("api/seats/", views.api_seats),
    path("api/select/", views.api_select),
    path("api/pay/", views.api_pay),
]
