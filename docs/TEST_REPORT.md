# Test Report

Generated on 2026-10-25 from a full local run of both suites.

| Suite | Tool | Tests | Result | Coverage |
|---|---|---|---|---|
| Backend (Django REST API on PostgreSQL) | pytest + pytest-django + pytest-cov | 140 | all passed (3.81 s) | 99% of statements |
| Frontend (React SPA) | Vitest + Testing Library + v8 coverage | 63 | all passed | 93.39% lines, 89.89% statements, 80.2% branches |

Backend tests run against a real PostgreSQL test database built by the same migration
that applies `database/schema.sql`, so constraints, partial unique indexes and the
`vehicle_inventory` view are exercised for real. `test_two_buyers_racing_for_the_last_car_cannot_both_get_it`
runs two purchases on separate database connections at the same moment and asserts
that exactly one succeeds.

## How to reproduce

```bash
# Backend (from backend/, PostgreSQL running, virtualenv active)
pytest -v --cov --cov-report=term

# Frontend (from frontend/)
npm test            # or: npx vitest run --coverage
```

## Backend: `pytest -v --cov`

```text
============================= test session starts =============================
platform win32 -- Python 3.14.0, pytest-9.1.1, pluggy-1.7.0 -- E:\#EditorCodes\incubyte\venv\Scripts\python.exe
cachedir: .pytest_cache
django: version: 6.1.2, settings: config.settings (from ini)
rootdir: E:\#EditorCodes\incubyte\backend
configfile: pytest.ini
testpaths: tests
plugins: cov-7.1.0, django-4.14.0
collecting ... collected 140 items
tests/test_audit_trail.py::test_registration_is_audited PASSED           [  0%]
tests/test_audit_trail.py::test_adding_a_vehicle_is_audited PASSED       [  1%]
tests/test_audit_trail.py::test_updating_a_vehicle_is_audited_with_the_changed_fields PASSED [  2%]
tests/test_audit_trail.py::test_deleting_a_vehicle_is_audited PASSED     [  2%]
tests/test_audit_trail.py::test_restocking_is_audited PASSED             [  3%]
tests/test_audit_trail.py::test_a_purchase_is_audited_with_its_sale PASSED [  4%]
tests/test_audit_trail.py::test_a_failed_purchase_leaves_no_audit_event PASSED [  5%]
tests/test_auth_api.py::TestRegister::test_creates_an_account_and_returns_tokens PASSED [  5%]
tests/test_auth_api.py::TestRegister::test_records_the_person_as_a_customer_party PASSED [  6%]
tests/test_auth_api.py::TestRegister::test_stores_a_password_hash_not_the_password PASSED [  7%]
tests/test_auth_api.py::TestRegister::test_normalises_the_email_to_lower_case PASSED [  7%]
tests/test_auth_api.py::TestRegister::test_rejects_a_duplicate_email_case_insensitively PASSED [  8%]
tests/test_auth_api.py::TestRegister::test_rejects_a_weak_password PASSED [  9%]
tests/test_auth_api.py::TestRegister::test_requires_every_field[first_name] PASSED [ 10%]
tests/test_auth_api.py::TestRegister::test_requires_every_field[last_name] PASSED [ 10%]
tests/test_auth_api.py::TestRegister::test_requires_every_field[email] PASSED [ 11%]
tests/test_auth_api.py::TestRegister::test_requires_every_field[password] PASSED [ 12%]
tests/test_auth_api.py::TestRegister::test_rejects_an_invalid_email PASSED [ 12%]
tests/test_auth_api.py::TestLogin::test_returns_tokens_for_valid_credentials PASSED [ 13%]
tests/test_auth_api.py::TestLogin::test_email_is_case_insensitive PASSED [ 14%]
tests/test_auth_api.py::TestLogin::test_rejects_a_wrong_password PASSED  [ 15%]
tests/test_auth_api.py::TestLogin::test_rejects_an_unknown_email_with_the_same_message PASSED [ 15%]
tests/test_auth_api.py::TestLogin::test_rejects_a_deactivated_account PASSED [ 16%]
tests/test_auth_api.py::TestAccessToken::test_me_returns_the_authenticated_user PASSED [ 17%]
tests/test_auth_api.py::TestAccessToken::test_protected_endpoints_require_a_token PASSED [ 17%]
tests/test_auth_api.py::TestAccessToken::test_rejects_a_tampered_token PASSED [ 18%]
tests/test_auth_api.py::TestAccessToken::test_rejects_a_malformed_authorization_header PASSED [ 19%]
tests/test_auth_api.py::TestAccessToken::test_rejects_an_expired_token PASSED [ 20%]
tests/test_auth_api.py::TestAccessToken::test_a_refresh_token_cannot_be_used_as_an_access_token PASSED [ 20%]
tests/test_auth_api.py::TestAccessToken::test_rejects_the_token_of_a_deactivated_user PASSED [ 21%]
tests/test_auth_api.py::TestRefreshAndLogout::test_refresh_issues_a_new_token_pair PASSED [ 22%]
tests/test_auth_api.py::TestRefreshAndLogout::test_a_refresh_token_can_only_be_used_once PASSED [ 22%]
tests/test_auth_api.py::TestRefreshAndLogout::test_rejects_an_unknown_refresh_token PASSED [ 23%]
tests/test_auth_api.py::TestRefreshAndLogout::test_logout_revokes_the_refresh_token PASSED [ 24%]
tests/test_inventory_api.py::TestPurchase::test_decreases_the_quantity_by_one PASSED [ 25%]
tests/test_inventory_api.py::TestPurchase::test_records_a_completed_sale_to_the_buyer_at_the_listed_price PASSED [ 25%]
tests/test_inventory_api.py::TestPurchase::test_marks_one_car_sold_and_logs_the_stock_change PASSED [ 26%]
tests/test_inventory_api.py::TestPurchase::test_transfers_ownership_of_that_car_to_the_buyer PASSED [ 27%]
tests/test_inventory_api.py::TestPurchase::test_selling_the_last_car_leaves_quantity_zero PASSED [ 27%]
tests/test_inventory_api.py::TestPurchase::test_cannot_buy_when_out_of_stock PASSED [ 28%]
tests/test_inventory_api.py::TestPurchase::test_a_retried_request_with_the_same_idempotency_key_buys_once PASSED [ 29%]
tests/test_inventory_api.py::TestPurchase::test_idempotency_keys_are_scoped_to_the_user PASSED [ 30%]
tests/test_inventory_api.py::TestPurchase::test_staff_can_also_buy PASSED [ 30%]
tests/test_inventory_api.py::TestPurchase::test_unknown_vehicle_is_404 PASSED [ 31%]
tests/test_inventory_api.py::TestPurchase::test_deleted_vehicle_is_404 PASSED [ 32%]
tests/test_inventory_api.py::TestPurchase::test_requires_authentication PASSED [ 32%]
tests/test_inventory_api.py::TestRestock::test_admin_restock_increases_the_quantity PASSED [ 33%]
tests/test_inventory_api.py::TestRestock::test_logs_a_restock_event_per_car PASSED [ 34%]
tests/test_inventory_api.py::TestRestock::test_cars_without_a_known_vin_get_a_placeholder PASSED [ 35%]
tests/test_inventory_api.py::TestRestock::test_records_the_given_vins PASSED [ 35%]
tests/test_inventory_api.py::TestRestock::test_records_the_unit_cost PASSED [ 36%]
tests/test_inventory_api.py::TestRestock::test_buying_back_a_sold_car_reuses_its_vehicle_record PASSED [ 37%]
tests/test_inventory_api.py::TestRestock::test_a_car_already_in_stock_cannot_be_received_again PASSED [ 37%]
tests/test_inventory_api.py::TestRestock::test_a_vin_of_a_different_model_is_rejected PASSED [ 38%]
tests/test_inventory_api.py::TestRestock::test_rejects_invalid_requests[payload0] PASSED [ 39%]
tests/test_inventory_api.py::TestRestock::test_rejects_invalid_requests[payload1] PASSED [ 40%]
tests/test_inventory_api.py::TestRestock::test_rejects_invalid_requests[payload2] PASSED [ 40%]
tests/test_inventory_api.py::TestRestock::test_rejects_invalid_requests[payload3] PASSED [ 41%]
tests/test_inventory_api.py::TestRestock::test_rejects_invalid_requests[payload4] PASSED [ 42%]
tests/test_inventory_api.py::TestRestock::test_rejects_invalid_requests[payload5] PASSED [ 42%]
tests/test_inventory_api.py::TestRestock::test_rejects_invalid_requests[payload6] PASSED [ 43%]
tests/test_inventory_api.py::TestRestock::test_rejects_invalid_requests[payload7] PASSED [ 44%]
tests/test_inventory_api.py::TestRestock::test_a_retried_request_with_the_same_idempotency_key_restocks_once PASSED [ 45%]
tests/test_inventory_api.py::TestRestock::test_staff_who_are_not_admins_cannot_restock PASSED [ 45%]
tests/test_inventory_api.py::TestRestock::test_customers_cannot_restock PASSED [ 46%]
tests/test_inventory_api.py::TestRestock::test_admins_of_another_dealership_cannot_restock PASSED [ 47%]
tests/test_inventory_api.py::TestRestock::test_unknown_vehicle_is_404 PASSED [ 47%]
tests/test_inventory_api.py::TestRestock::test_requires_authentication PASSED [ 48%]
tests/test_schema.py::test_migrations_create_every_reference_table PASSED [ 49%]
tests/test_schema.py::test_migrations_create_the_vehicle_inventory_view PASSED [ 50%]
tests/test_seed_demo.py::test_creates_an_admin_who_can_log_in PASSED     [ 50%]
tests/test_seed_demo.py::test_creates_a_customer_without_staff_roles PASSED [ 51%]
tests/test_seed_demo.py::test_stocks_a_showroom_including_a_sold_out_vehicle PASSED [ 52%]
tests/test_seed_demo.py::test_running_twice_does_not_duplicate_anything PASSED [ 52%]
tests/test_vehicle_search_api.py::TestSearch::test_by_make_is_case_insensitive PASSED [ 53%]
tests/test_vehicle_search_api.py::TestSearch::test_by_partial_make PASSED [ 54%]
tests/test_vehicle_search_api.py::TestSearch::test_by_model PASSED       [ 55%]
tests/test_vehicle_search_api.py::TestSearch::test_by_category PASSED    [ 55%]
tests/test_vehicle_search_api.py::TestSearch::test_by_price_range_inclusive PASSED [ 56%]
tests/test_vehicle_search_api.py::TestSearch::test_by_minimum_price_only PASSED [ 57%]
tests/test_vehicle_search_api.py::TestSearch::test_by_maximum_price_only PASSED [ 57%]
tests/test_vehicle_search_api.py::TestSearch::test_combines_filters PASSED [ 58%]
tests/test_vehicle_search_api.py::TestSearch::test_without_filters_returns_everything PASSED [ 59%]
tests/test_vehicle_search_api.py::TestSearch::test_returns_quantity_like_the_list PASSED [ 60%]
tests/test_vehicle_search_api.py::TestSearch::test_no_match_returns_an_empty_list PASSED [ 60%]
tests/test_vehicle_search_api.py::TestSearchValidation::test_rejects_a_non_numeric_price PASSED [ 61%]
tests/test_vehicle_search_api.py::TestSearchValidation::test_rejects_a_minimum_above_the_maximum PASSED [ 62%]
tests/test_vehicle_search_api.py::TestSearchValidation::test_requires_authentication PASSED [ 62%]
tests/test_vehicle_update_delete_api.py::TestGetVehicle::test_returns_one_vehicle PASSED [ 63%]
tests/test_vehicle_update_delete_api.py::TestGetVehicle::test_unknown_id_is_404 PASSED [ 64%]
tests/test_vehicle_update_delete_api.py::TestUpdateVehicle::test_staff_can_change_the_price PASSED [ 65%]
tests/test_vehicle_update_delete_api.py::TestUpdateVehicle::test_a_price_change_is_recorded PASSED [ 65%]
tests/test_vehicle_update_delete_api.py::TestUpdateVehicle::test_an_unchanged_price_records_nothing PASSED [ 66%]
tests/test_vehicle_update_delete_api.py::TestUpdateVehicle::test_can_change_category_and_condition PASSED [ 67%]
tests/test_vehicle_update_delete_api.py::TestUpdateVehicle::test_can_rename_make_and_model_before_any_car_is_stocked PASSED [ 67%]
tests/test_vehicle_update_delete_api.py::TestUpdateVehicle::test_cannot_change_the_model_of_cars_already_in_stock PASSED [ 68%]
tests/test_vehicle_update_delete_api.py::TestUpdateVehicle::test_a_case_only_rename_is_not_a_model_change PASSED [ 69%]
tests/test_vehicle_update_delete_api.py::TestUpdateVehicle::test_quantity_cannot_be_edited_directly PASSED [ 70%]
tests/test_vehicle_update_delete_api.py::TestUpdateVehicle::test_rejects_an_invalid_price PASSED [ 70%]
tests/test_vehicle_update_delete_api.py::TestUpdateVehicle::test_customers_cannot_update PASSED [ 71%]
tests/test_vehicle_update_delete_api.py::TestUpdateVehicle::test_staff_of_another_dealership_cannot_update PASSED [ 72%]
tests/test_vehicle_update_delete_api.py::TestUpdateVehicle::test_unknown_vehicle_is_404 PASSED [ 72%]
tests/test_vehicle_update_delete_api.py::TestUpdateVehicle::test_requires_authentication PASSED [ 73%]
tests/test_vehicle_update_delete_api.py::TestDeleteVehicle::test_admin_can_delete_a_vehicle PASSED [ 74%]
tests/test_vehicle_update_delete_api.py::TestDeleteVehicle::test_delete_archives_the_listing_instead_of_erasing_history PASSED [ 75%]
tests/test_vehicle_update_delete_api.py::TestDeleteVehicle::test_unsold_cars_are_taken_out_of_stock PASSED [ 75%]
tests/test_vehicle_update_delete_api.py::TestDeleteVehicle::test_staff_who_are_not_admins_cannot_delete PASSED [ 76%]
tests/test_vehicle_update_delete_api.py::TestDeleteVehicle::test_customers_cannot_delete PASSED [ 77%]
tests/test_vehicle_update_delete_api.py::TestDeleteVehicle::test_admins_of_another_dealership_cannot_delete PASSED [ 77%]
tests/test_vehicle_update_delete_api.py::TestDeleteVehicle::test_deleting_twice_is_404 PASSED [ 78%]
tests/test_vehicle_update_delete_api.py::TestDeleteVehicle::test_requires_authentication PASSED [ 79%]
tests/test_vehicles_api.py::TestCreateVehicle::test_staff_can_add_a_vehicle PASSED [ 80%]
tests/test_vehicles_api.py::TestCreateVehicle::test_each_unit_in_stock_is_a_physical_car_with_its_own_vin PASSED [ 80%]
tests/test_vehicles_api.py::TestCreateVehicle::test_records_stock_events_and_dealer_ownership PASSED [ 81%]
tests/test_vehicles_api.py::TestCreateVehicle::test_reuses_an_existing_make_case_insensitively PASSED [ 82%]
tests/test_vehicles_api.py::TestCreateVehicle::test_quantity_defaults_to_zero PASSED [ 82%]
tests/test_vehicles_api.py::TestCreateVehicle::test_accepts_optional_year_variant_and_condition PASSED [ 83%]
tests/test_vehicles_api.py::TestCreateVehicle::test_customers_cannot_add_vehicles PASSED [ 84%]
tests/test_vehicles_api.py::TestCreateVehicle::test_requires_authentication PASSED [ 85%]
tests/test_vehicles_api.py::TestCreateVehicle::test_requires_core_fields[make] PASSED [ 85%]
tests/test_vehicles_api.py::TestCreateVehicle::test_requires_core_fields[model] PASSED [ 86%]
tests/test_vehicles_api.py::TestCreateVehicle::test_requires_core_fields[category] PASSED [ 87%]
tests/test_vehicles_api.py::TestCreateVehicle::test_requires_core_fields[price] PASSED [ 87%]
tests/test_vehicles_api.py::TestCreateVehicle::test_rejects_invalid_values[price--1] PASSED [ 88%]
tests/test_vehicles_api.py::TestCreateVehicle::test_rejects_invalid_values[quantity--1] PASSED [ 89%]
tests/test_vehicles_api.py::TestCreateVehicle::test_rejects_invalid_values[make-   ] PASSED [ 90%]
tests/test_vehicles_api.py::TestCreateVehicle::test_rejects_invalid_values[condition-BROKEN] PASSED [ 90%]
tests/test_vehicles_api.py::TestCreateVehicle::test_staff_of_several_dealerships_must_choose_one PASSED [ 91%]
tests/test_vehicles_api.py::TestCreateVehicle::test_cannot_add_to_a_dealership_without_a_role_there PASSED [ 92%]
tests/test_vehicles_api.py::TestListVehicles::test_lists_every_vehicle_with_its_quantity PASSED [ 92%]
tests/test_vehicles_api.py::TestListVehicles::test_quantity_counts_only_cars_still_available PASSED [ 93%]
tests/test_vehicles_api.py::TestListVehicles::test_hides_deleted_vehicles PASSED [ 94%]
tests/test_vehicles_api.py::TestListVehicles::test_requires_authentication PASSED [ 95%]
tests/test_vehicles_api.py::TestListVehicles::test_a_user_from_another_dealership_sees_the_same_catalogue PASSED [ 95%]
tests/test_inventory_api.py::test_two_buyers_racing_for_the_last_car_cannot_both_get_it PASSED [ 96%]
tests/test_exception_handler.py::test_domain_errors_become_a_detail_message_with_their_status PASSED [ 97%]
tests/test_exception_handler.py::test_field_errors_are_reported_against_the_field PASSED [ 97%]
tests/test_exception_handler.py::test_permission_and_conflict_statuses PASSED [ 98%]
tests/test_exception_handler.py::test_a_database_integrity_error_is_a_409_conflict_not_a_500 PASSED [ 99%]
tests/test_exception_handler.py::test_unknown_errors_are_left_to_django PASSED [100%]
=============================== tests coverage ================================
_______________ coverage: platform win32, python 3.14.0-final-0 _______________
Name                                        Stmts   Miss  Cover   Missing
-------------------------------------------------------------------------
accounts\apps.py                                3      0   100%
accounts\authentication.py                     19      0   100%
accounts\roles.py                              10      0   100%
accounts\serializers.py                        31      0   100%
accounts\services.py                           38      3    92%   36, 52-53
accounts\tokens.py                             54      3    94%   59, 90-91
accounts\urls.py                                3      0   100%
accounts\views.py                              49      2    96%   39-40
config\exception_handler.py                    13      0   100%
config\settings.py                             30      0   100%
config\urls.py                                  2      0   100%
dealership\apps.py                              3      0   100%
dealership\audit.py                            10      0   100%
dealership\errors.py                           16      0   100%
dealership\models\__init__.py                   7      0   100%
dealership\models\access.py                    44      0   100%
dealership\models\audit.py                     15      0   100%
dealership\models\catalog.py                   68      0   100%
dealership\models\parties.py                   93      0   100%
dealership\models\sales.py                     36      0   100%
dealership\models\stock.py                     89      0   100%
vehicles\apps.py                                3      0   100%
vehicles\catalog.py                            80      2    98%   170-171
vehicles\demo_data.py                          41      0   100%
vehicles\history.py                             5      0   100%
vehicles\management\commands\seed_demo.py      13      0   100%
vehicles\policies.py                           20      0   100%
vehicles\queries.py                            26      0   100%
vehicles\serializers.py                        83      0   100%
vehicles\stock.py                             104      0   100%
vehicles\urls.py                                3      0   100%
vehicles\views.py                              51      1    98%   30
-------------------------------------------------------------------------
TOTAL                                        1062     11    99%
6 empty files skipped.
============================= 140 passed in 3.81s =============================
```

## Frontend: `vitest run --reporter=verbose --coverage`

```text
RUN  v5.0.5 W:/frontend
      Coverage enabled with v8
 ✓ src/api/auth.test.ts > auth api > login stores the token pair and returns the user 2ms
 ✓ src/api/auth.test.ts > auth api > register starts a session too 0ms
 ✓ src/api/auth.test.ts > auth api > logout forgets the tokens even if the server cannot be reached 1ms
 ✓ src/api/auth.test.ts > auth api > logout without a session does not call the server 0ms
 ✓ src/api/auth.test.ts > auth api > currentUser is null without a stored session and asks the API otherwise 0ms
 ✓ src/api/auth.test.ts > auth api > treats unreadable stored tokens as no session 0ms
 ✓ src/lib/permissions.test.ts > canManage (add/edit) > allows staff and admins of the vehicle’s dealership 2ms
 ✓ src/lib/permissions.test.ts > canManage (add/edit) > denies customers, anonymous users and staff of other dealerships 0ms
 ✓ src/lib/permissions.test.ts > canAdminister (restock/delete) > allows only admins of the vehicle’s dealership 0ms
 ✓ src/lib/permissions.test.ts > canAddVehicles > is true for anyone with a staff role 0ms
 ✓ src/api/vehicles.test.ts > vehicles api > lists vehicles 4ms
 ✓ src/api/vehicles.test.ts > vehicles api > searches with the API parameter names 0ms
 ✓ src/api/vehicles.test.ts > vehicles api > creates, updates and deletes 1ms
 ✓ src/api/vehicles.test.ts > vehicles api > sends a fresh idempotency key with every purchase and restock 1ms
 ✓ src/api/client.test.ts > api client > sends JSON with the access token 5ms
 ✓ src/api/client.test.ts > api client > omits the token for public endpoints 0ms
 ✓ src/api/client.test.ts > api client > refreshes an expired access token once and retries the request 1ms
 ✓ src/api/client.test.ts > api client > ends the session when the refresh token is rejected 1ms
 ✓ src/api/client.test.ts > api client > turns an error detail into an ApiError message 0ms
 ✓ src/api/client.test.ts > api client > exposes field validation errors 0ms
 ✓ src/api/client.test.ts > api client > returns undefined for 204 No Content 0ms
 ✓ src/api/client.test.ts > api client > reports network failures in plain language 1ms
 ✓ src/lib/format.test.ts > formatPrice > formats rupees with Indian digit grouping and no needless decimals 12ms
 ✓ src/lib/format.test.ts > formatPrice > keeps paise when the amount has them 0ms
 ✓ src/lib/format.test.ts > stockStatus > is sold out at zero 1ms
 ✓ src/lib/format.test.ts > stockStatus > warns when only one or two are left 0ms
 ✓ src/lib/format.test.ts > stockStatus > shows the count when well stocked 0ms
 ✓ src/lib/search.test.ts > toSearchParams > sends only the filters that are set, trimmed, using the API names 2ms
 ✓ src/lib/search.test.ts > toSearchParams > is empty when nothing is set 0ms
 ✓ src/lib/search.test.ts > hasActiveFilters > is false for empty or whitespace-only filters 0ms
 ✓ src/lib/search.test.ts > hasActiveFilters > is true when any filter is set 0ms
 ✓ src/auth/AuthProvider.test.tsx > AuthProvider and RequireAuth > restores a stored session and shows protected pages 37ms
 ✓ src/auth/AuthProvider.test.tsx > AuthProvider and RequireAuth > sends visitors without a session to the login page 6ms
 ✓ src/auth/AuthProvider.test.tsx > AuthProvider and RequireAuth > treats a failed session check as signed out 6ms
 ✓ src/components/VehicleCard.test.tsx > VehicleCard > shows the vehicle’s make, model, category, price and stock 102ms
 ✓ src/components/VehicleCard.test.tsx > VehicleCard > lets a customer purchase a vehicle that is in stock 69ms
 ✓ src/pages/DashboardPage.test.tsx > DashboardPage > shows every available vehicle with its stock 130ms
 ✓ src/components/VehicleFilters.test.tsx > VehicleFilters > reports what the user types into each filter 319ms
 ✓ src/components/VehicleFilters.test.tsx > VehicleFilters > offers the known categories 63ms
 ✓ src/components/VehicleCard.test.tsx > VehicleCard > disables Purchase when the quantity is zero 63ms
 ✓ src/components/VehicleCard.test.tsx > VehicleCard > disables Purchase while a purchase is in progress 7ms
 ✓ src/components/VehicleCard.test.tsx > VehicleCard > hides management actions from customers 5ms
 ✓ src/components/VehicleCard.test.tsx > VehicleCard > lets staff edit but not restock or delete 6ms
 ✓ src/components/VehicleFilters.test.tsx > VehicleFilters > clears every filter at once 52ms
 ✓ src/components/VehicleFilters.test.tsx > VehicleFilters > does not offer to clear when nothing is filtered 4ms
 ✓ src/auth/AuthProvider.test.tsx > AuthProvider and RequireAuth > signs in and out 182ms
 ✓ src/auth/AuthProvider.test.tsx > AuthProvider and RequireAuth > signs the user out when the API reports the session expired 31ms
 ✓ src/auth/AuthProvider.test.tsx > AuthProvider and RequireAuth > useAuth outside the provider is a programming error 5ms
 ✓ src/pages/DashboardPage.test.tsx > DashboardPage > purchasing updates the quantity and confirms the sale 96ms
 ✓ src/pages/DashboardPage.test.tsx > DashboardPage > explains why a purchase failed 95ms
 ✓ src/components/VehicleCard.test.tsx > VehicleCard > gives admins edit, restock and delete actions 165ms
 ✓ src/pages/LoginPage.test.tsx > LoginPage > signs in with the entered credentials and opens the showroom 720ms
 ✓ src/pages/RegisterPage.test.tsx > RegisterPage > creates the account and opens the showroom 858ms
 ✓ src/pages/DashboardPage.test.tsx > DashboardPage > searches the API when a filter is set 428ms
 ✓ src/pages/LoginPage.test.tsx > LoginPage > shows the server’s message when sign-in fails 425ms
 ✓ src/pages/LoginPage.test.tsx > LoginPage > links to registration 10ms
 ✓ src/pages/LoginPage.test.tsx > LoginPage > sends a signed-in user straight to the showroom 5ms
 ✓ src/pages/DashboardPage.test.tsx > DashboardPage > shows a friendly message when nothing matches 464ms
 ✓ src/pages/DashboardPage.test.tsx > DashboardPage > only shows "Add vehicle" to dealership staff 42ms
 ✓ src/pages/RegisterPage.test.tsx > RegisterPage > shows field errors next to the right field 820ms
 ✓ src/pages/DashboardPage.test.tsx > DashboardPage > lets an admin add a vehicle 777ms
 ✓ src/pages/DashboardPage.test.tsx > DashboardPage > lets an admin delete a vehicle after confirming 113ms
 ✓ src/pages/DashboardPage.test.tsx > DashboardPage > lets an admin restock a vehicle 230ms
 Test Files  12 passed (12)
      Tests  63 passed (63)
   Start at  21:52:13
   Duration  4.87s (environment 57%, tests 21%, setup 16%, import 3%, worker 2%, transform 1%)
 % Coverage report from v8
-------------------|---------|----------|---------|---------|-------------------
File               | % Stmts | % Branch | % Funcs | % Lines | Uncovered Line #s
-------------------|---------|----------|---------|---------|-------------------
All files          |   89.89 |     80.2 |    89.2 |   93.39 |
 src               |       0 |      100 |       0 |       0 |
  App.tsx          |       0 |      100 |       0 |       0 | 10
 src/api           |   93.33 |    87.03 |   89.65 |   96.05 |
  client.ts        |   91.37 |    84.78 |   83.33 |   95.65 | 121,128
  http.ts          |    90.9 |      100 |      75 |    90.9 | 28
 src/auth          |   91.89 |      100 |    92.3 |   91.17 |
  AuthContext.tsx  |      88 |      100 |    90.9 |    87.5 | 38-40
 src/components    |   86.48 |    69.66 |   90.24 |   91.48 |
  Navbar.tsx       |   76.92 |    66.66 |      75 |      90 | 39
  RestockModal.tsx |   75.86 |    57.14 |   71.42 |   84.61 | 43-44,79-90
  VehicleCard.tsx  |     100 |     92.3 |     100 |     100 | 88
  ...FormModal.tsx |   83.87 |     65.9 |      90 |      88 | 75-76,161
 src/components/ui |   86.84 |    87.03 |   83.78 |   96.87 |
  Field.tsx        |     100 |     91.3 |     100 |     100 | 68,88
  Modal.tsx        |      85 |    63.63 |     100 |     100 | 22-47
  Toast.tsx        |   73.68 |      100 |   58.33 |   91.66 | 52
  icons.tsx        |   91.66 |      100 |   91.66 |   91.66 | 112
  toast-context.ts |      80 |       50 |     100 |     100 | 12
 src/lib           |     100 |    89.47 |     100 |     100 |
  permissions.ts   |     100 |    66.66 |     100 |     100 | 26-27
 src/pages         |   89.55 |    76.92 |   90.24 |   91.22 |
  ...boardPage.tsx |   87.34 |    74.46 |   88.88 |   89.23 | ...64,184-186,224
  LoginPage.tsx    |      92 |      100 |   83.33 |   91.66 | 77-78
  RegisterPage.tsx |   92.59 |       70 |     100 |   95.45 | 35
-------------------|---------|----------|---------|---------|-------------------
=============================== Coverage summary ===============================
Statements   : 89.89% ( 436/485 )
Branches     : 80.2% ( 235/293 )
Functions    : 89.2% ( 157/176 )
Lines        : 93.39% ( 382/409 )
================================================================================
```
