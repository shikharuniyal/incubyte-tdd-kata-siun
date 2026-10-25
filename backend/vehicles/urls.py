from django.urls import path

from . import views

# Mounted at "api/vehicles" (see config/urls.py).
urlpatterns = [
    path("", views.VehicleCollectionView.as_view(), name="vehicle-list"),
    path("/search", views.VehicleSearchView.as_view(), name="vehicle-search"),
    path("/<uuid:listing_id>", views.VehicleDetailView.as_view(), name="vehicle-detail"),
    path("/<uuid:listing_id>/purchase", views.PurchaseView.as_view(), name="vehicle-purchase"),
    path("/<uuid:listing_id>/restock", views.RestockView.as_view(), name="vehicle-restock"),
]
