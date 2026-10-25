"""GET /api/vehicles/search?make=&model=&category=&min_price=&max_price="""

import pytest

pytestmark = pytest.mark.django_db

SEARCH_URL = "/api/vehicles/search"

CATALOGUE = [
    {"make": "Toyota", "model": "Corolla", "category": "Sedan", "price": 1850000, "quantity": 2},
    {"make": "Toyota", "model": "Fortuner", "category": "SUV", "price": 3500000, "quantity": 1},
    {"make": "Hyundai", "model": "Creta", "category": "SUV", "price": 1500000, "quantity": 0},
    {"make": "Maruti Suzuki", "model": "Swift", "category": "Hatchback", "price": 700000, "quantity": 4},
]


@pytest.fixture
def catalogue(staff_client):
    for vehicle in CATALOGUE:
        assert staff_client.post("/api/vehicles", vehicle, format="json").status_code == 201


def search(client, **params):
    return client.get(SEARCH_URL, params)


def models_in(response) -> set[str]:
    return {vehicle["model"] for vehicle in response.json()}


@pytest.mark.usefixtures("catalogue")
class TestSearch:
    def test_by_make_is_case_insensitive(self, customer_client):
        assert models_in(search(customer_client, make="toyota")) == {"Corolla", "Fortuner"}

    def test_by_partial_make(self, customer_client):
        assert models_in(search(customer_client, make="maruti")) == {"Swift"}

    def test_by_model(self, customer_client):
        assert models_in(search(customer_client, model="cret")) == {"Creta"}

    def test_by_category(self, customer_client):
        assert models_in(search(customer_client, category="suv")) == {"Fortuner", "Creta"}

    def test_by_price_range_inclusive(self, customer_client):
        response = search(customer_client, min_price=1500000, max_price=1850000)

        assert models_in(response) == {"Corolla", "Creta"}

    def test_by_minimum_price_only(self, customer_client):
        assert models_in(search(customer_client, min_price=2000000)) == {"Fortuner"}

    def test_by_maximum_price_only(self, customer_client):
        assert models_in(search(customer_client, max_price=1000000)) == {"Swift"}

    def test_combines_filters(self, customer_client):
        assert models_in(search(customer_client, make="toyota", category="suv")) == {"Fortuner"}

    def test_without_filters_returns_everything(self, customer_client):
        assert len(search(customer_client).json()) == 4

    def test_returns_quantity_like_the_list(self, customer_client):
        [creta] = search(customer_client, model="Creta").json()

        assert creta["quantity"] == 0

    def test_no_match_returns_an_empty_list(self, customer_client):
        response = search(customer_client, make="Ferrari")

        assert response.status_code == 200
        assert response.json() == []


class TestSearchValidation:
    def test_rejects_a_non_numeric_price(self, customer_client):
        response = search(customer_client, min_price="cheap")

        assert response.status_code == 400
        assert "min_price" in response.json()

    def test_rejects_a_minimum_above_the_maximum(self, customer_client):
        response = search(customer_client, min_price=500, max_price=100)

        assert response.status_code == 400

    def test_requires_authentication(self, api_client):
        assert search(api_client, make="toyota").status_code == 401
