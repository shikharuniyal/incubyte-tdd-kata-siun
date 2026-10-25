from django.urls import path

from . import views

# Mounted at "api/vehicles" (see config/urls.py).
urlpatterns = [
    path("", views.VehicleCollectionView.as_view(), name="vehicle-list"),
]
