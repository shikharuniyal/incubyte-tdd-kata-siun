from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from . import catalog, queries
from .serializers import VehicleCreateSerializer, VehicleSerializer


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
