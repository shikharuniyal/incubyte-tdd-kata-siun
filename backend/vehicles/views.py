from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from . import catalog, queries
from .serializers import (
    VehicleCreateSerializer,
    VehicleSearchSerializer,
    VehicleSerializer,
    VehicleUpdateSerializer,
)


def vehicle_response(listing_id, status_code=status.HTTP_200_OK) -> Response:
    return Response(VehicleSerializer(queries.get_vehicle(listing_id)).data, status=status_code)


class VehicleCollectionView(APIView):
    """GET /api/vehicles lists vehicles; POST /api/vehicles adds one."""

    def get(self, request):
        return Response(VehicleSerializer(queries.inventory(), many=True).data)

    def post(self, request):
        serializer = VehicleCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        listing = catalog.add_vehicle(
            actor=request.user,
            spec=catalog.VehicleSpec(
                make=data["make"],
                model=data["model"],
                category=data["category"],
                model_year=data["model_year"],
                variant=data["variant"],
            ),
            price=data["price"],
            quantity=data["quantity"],
            condition=data["condition"],
            currency_code=data["currency_code"],
            dealership_id=data.get("dealership_id"),
        )
        return vehicle_response(listing.listing_id, status.HTTP_201_CREATED)


class VehicleDetailView(APIView):
    """GET, PUT (partial update) and DELETE /api/vehicles/:id"""

    def get(self, request, listing_id):
        return vehicle_response(listing_id)

    def put(self, request, listing_id):
        serializer = VehicleUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        catalog.update_vehicle(
            actor=request.user,
            listing_id=listing_id,
            changes=catalog.VehicleChanges(**serializer.validated_data),
        )
        return vehicle_response(listing_id)

    def delete(self, request, listing_id):
        catalog.delete_vehicle(actor=request.user, listing_id=listing_id)
        return Response(status=status.HTTP_204_NO_CONTENT)


class VehicleSearchView(APIView):
    """GET /api/vehicles/search?make=&model=&category=&min_price=&max_price="""

    def get(self, request):
        filters = VehicleSearchSerializer(data=request.query_params)
        filters.is_valid(raise_exception=True)
        return Response(VehicleSerializer(queries.search(**filters.validated_data), many=True).data)
