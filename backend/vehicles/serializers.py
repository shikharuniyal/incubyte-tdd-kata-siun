from django.utils import timezone
from rest_framework import serializers

from dealership.models import VehicleListing

PRICE = {"max_digits": 14, "decimal_places": 2, "min_value": 0}
MAX_UNITS_PER_REQUEST = 500


class NonBlankCharField(serializers.CharField):
    """A trimmed string that may not be empty."""

    def __init__(self, **kwargs):
        super().__init__(allow_blank=False, trim_whitespace=True, **kwargs)


class VehicleCreateSerializer(serializers.Serializer):
    make = NonBlankCharField(max_length=100)
    model = NonBlankCharField(max_length=100)
    category = NonBlankCharField(max_length=50)
    price = serializers.DecimalField(**PRICE)
    quantity = serializers.IntegerField(min_value=0, max_value=MAX_UNITS_PER_REQUEST, default=0)
    model_year = serializers.IntegerField(min_value=1900, max_value=2200, required=False)
    variant = NonBlankCharField(max_length=50, default="BASE")
    condition = serializers.ChoiceField(choices=VehicleListing.Condition.choices, default=VehicleListing.Condition.NEW)
    currency_code = serializers.RegexField(r"^[A-Za-z]{3}$", default="INR")
    dealership_id = serializers.UUIDField(required=False)

    def validate_currency_code(self, value: str) -> str:
        return value.upper()

    def validate(self, attrs):
        attrs.setdefault("model_year", timezone.now().year)
        return attrs


class VehicleUpdateSerializer(serializers.Serializer):
    """Partial update: only the fields sent are changed."""

    QUANTITY_MESSAGE = "Quantity follows the cars in stock; use the purchase or restock endpoints."

    make = NonBlankCharField(max_length=100, required=False)
    model = NonBlankCharField(max_length=100, required=False)
    category = NonBlankCharField(max_length=50, required=False)
    model_year = serializers.IntegerField(min_value=1900, max_value=2200, required=False)
    variant = NonBlankCharField(max_length=50, required=False)
    price = serializers.DecimalField(required=False, **PRICE)
    condition = serializers.ChoiceField(choices=VehicleListing.Condition.choices, required=False)

    def validate(self, attrs):
        if "quantity" in self.initial_data:
            raise serializers.ValidationError({"quantity": [self.QUANTITY_MESSAGE]})
        return attrs


class VehicleSearchSerializer(serializers.Serializer):
    make = serializers.CharField(required=False, max_length=100)
    model = serializers.CharField(required=False, max_length=100)
    category = serializers.CharField(required=False, max_length=50)
    min_price = serializers.DecimalField(required=False, **PRICE)
    max_price = serializers.DecimalField(required=False, **PRICE)

    def validate(self, attrs):
        low, high = attrs.get("min_price"), attrs.get("max_price")
        if low is not None and high is not None and low > high:
            raise serializers.ValidationError({"min_price": ["min_price cannot be greater than max_price."]})
        return attrs


class VehicleSerializer(serializers.Serializer):
    """How a vehicle (listing + derived quantity) is shown to API clients."""

    id = serializers.UUIDField()
    make = serializers.CharField()
    model = serializers.CharField(source="model_name")
    category = serializers.CharField()
    price = serializers.DecimalField(max_digits=14, decimal_places=2)
    quantity = serializers.IntegerField()
    condition = serializers.CharField(source="condition_class")
    currency_code = serializers.CharField()
    model_year = serializers.IntegerField()
    variant = serializers.CharField()
    dealership_id = serializers.UUIDField()
    dealership_name = serializers.CharField()
