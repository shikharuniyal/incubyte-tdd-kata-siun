-- Car dealership inventory: PostgreSQL 16+ reference schema.
-- Apply to an empty database. In Django, implement equivalent models/migrations
-- instead of applying this file alongside Django's own migration tables.
-- A listing is the quantity-based API resource; a vehicle is one VIN-bearing car.
-- Each acquisition is a separate period that car is in dealership inventory.

BEGIN;

CREATE TABLE party (
    party_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    party_type text NOT NULL CHECK (party_type IN ('PERSON', 'ORGANIZATION')),
    display_name text NOT NULL CHECK (btrim(display_name) <> ''),
    email text,
    phone text,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE person (
    party_id uuid PRIMARY KEY REFERENCES party(party_id),
    given_name text NOT NULL,
    family_name text NOT NULL
);

CREATE TABLE organization (
    party_id uuid PRIMARY KEY REFERENCES party(party_id),
    registered_name text NOT NULL,
    registration_number text UNIQUE
);

CREATE TABLE customer (
    party_id uuid PRIMARY KEY REFERENCES party(party_id),
    notes text,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE manufacturer (
    manufacturer_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_party_id uuid NOT NULL UNIQUE REFERENCES organization(party_id)
);

CREATE TABLE dealer_organization (
    dealer_org_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_party_id uuid NOT NULL UNIQUE REFERENCES organization(party_id),
    gstin text UNIQUE
);

CREATE TABLE dealer_network (
    network_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    name text NOT NULL UNIQUE
);

CREATE TABLE network_membership (
    membership_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    network_id uuid NOT NULL REFERENCES dealer_network(network_id),
    dealer_org_id uuid NOT NULL REFERENCES dealer_organization(dealer_org_id),
    joined_at timestamptz NOT NULL DEFAULT now(),
    ended_at timestamptz,
    CHECK (ended_at IS NULL OR ended_at > joined_at)
);

CREATE UNIQUE INDEX network_membership_one_active
    ON network_membership(network_id, dealer_org_id)
    WHERE ended_at IS NULL;

CREATE TABLE dealership (
    dealership_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    dealer_org_id uuid NOT NULL REFERENCES dealer_organization(dealer_org_id),
    name text NOT NULL,
    status text NOT NULL DEFAULT 'ACTIVE'
        CHECK (status IN ('ACTIVE', 'INACTIVE')),
    UNIQUE (dealer_org_id, name)
);

CREATE TABLE site (
    site_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    dealership_id uuid NOT NULL REFERENCES dealership(dealership_id),
    owner_party_id uuid NOT NULL REFERENCES party(party_id),
    name text NOT NULL,
    address text NOT NULL,
    site_type text NOT NULL CHECK (site_type IN ('BRANCH', 'WAREHOUSE', 'OTHER')),
    UNIQUE (dealership_id, name)
);

CREATE TABLE site_area (
    area_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    site_id uuid NOT NULL REFERENCES site(site_id),
    name text NOT NULL,
    area_type text NOT NULL
        CHECK (area_type IN ('SHOWROOM', 'LOT', 'WAREHOUSE', 'SERVICE_BAY', 'OTHER')),
    capacity integer CHECK (capacity IS NULL OR capacity >= 0),
    UNIQUE (site_id, name)
);

CREATE TABLE make (
    make_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    manufacturer_id uuid NOT NULL REFERENCES manufacturer(manufacturer_id),
    name text NOT NULL,
    UNIQUE (manufacturer_id, name)
);

CREATE TABLE vehicle_model (
    model_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    make_id uuid NOT NULL REFERENCES make(make_id),
    name text NOT NULL,
    model_year integer NOT NULL CHECK (model_year BETWEEN 1900 AND 2200),
    variant text NOT NULL DEFAULT 'BASE',
    category text NOT NULL,
    fuel_type text,
    transmission text,
    UNIQUE (make_id, name, model_year, variant)
);

CREATE TABLE vehicle (
    vehicle_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    model_id uuid NOT NULL REFERENCES vehicle_model(model_id),
    vin text NOT NULL UNIQUE CHECK (btrim(vin) <> ''),
    colour text,
    first_registration_date date,
    current_odometer integer NOT NULL DEFAULT 0 CHECK (current_odometer >= 0),
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (vehicle_id, model_id)
);

CREATE TABLE vehicle_listing (
    listing_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    dealership_id uuid NOT NULL REFERENCES dealership(dealership_id),
    model_id uuid NOT NULL REFERENCES vehicle_model(model_id),
    condition_class text NOT NULL
        CHECK (condition_class IN ('NEW', 'USED', 'REFURBISHED')),
    advertised_price numeric(14, 2) NOT NULL CHECK (advertised_price >= 0),
    currency_code char(3) NOT NULL DEFAULT 'INR',
    status text NOT NULL DEFAULT 'ACTIVE'
        CHECK (status IN ('ACTIVE', 'ARCHIVED')),
    deleted_at timestamptz,
    created_at timestamptz NOT NULL DEFAULT now(),
    CHECK (deleted_at IS NULL OR status = 'ARCHIVED'),
    UNIQUE (listing_id, model_id, dealership_id)
);

CREATE TABLE app_user (
    user_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    person_party_id uuid NOT NULL UNIQUE REFERENCES person(party_id),
    email text NOT NULL,
    password_hash text NOT NULL,
    is_active boolean NOT NULL DEFAULT true,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE UNIQUE INDEX app_user_email_unique_ci ON app_user (lower(email));

CREATE TABLE user_role_assignment (
    assignment_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id uuid NOT NULL REFERENCES app_user(user_id),
    dealership_id uuid NOT NULL REFERENCES dealership(dealership_id),
    role text NOT NULL CHECK (role IN ('ADMIN', 'MANAGER', 'STAFF')),
    granted_at timestamptz NOT NULL DEFAULT now(),
    revoked_at timestamptz,
    CHECK (revoked_at IS NULL OR revoked_at > granted_at)
);

CREATE UNIQUE INDEX user_role_one_active
    ON user_role_assignment(user_id, dealership_id, role)
    WHERE revoked_at IS NULL;

CREATE TABLE auth_session (
    session_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id uuid NOT NULL REFERENCES app_user(user_id),
    refresh_token_hash text NOT NULL UNIQUE,
    created_at timestamptz NOT NULL DEFAULT now(),
    expires_at timestamptz NOT NULL,
    revoked_at timestamptz,
    CHECK (expires_at > created_at)
);

CREATE TABLE acquisition (
    acquisition_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    vehicle_id uuid NOT NULL,
    model_id uuid NOT NULL,
    listing_id uuid NOT NULL,
    dealership_id uuid NOT NULL,
    source_party_id uuid NOT NULL REFERENCES party(party_id),
    current_area_id uuid REFERENCES site_area(area_id),
    stock_number text NOT NULL,
    acquisition_type text NOT NULL
        CHECK (acquisition_type IN ('NEW_SUPPLY', 'USED_PURCHASE', 'TRADE_IN', 'AUCTION', 'TRANSFER', 'RETURN', 'OTHER')),
    ownership_type text NOT NULL
        CHECK (ownership_type IN ('OWNED', 'CONSIGNED')),
    inventory_status text NOT NULL DEFAULT 'INTAKE'
        CHECK (inventory_status IN ('INTAKE', 'INSPECTION', 'REFURBISHING', 'AVAILABLE', 'RESERVED', 'SOLD', 'RETURNED', 'REMOVED')),
    acquisition_cost numeric(14, 2) NOT NULL CHECK (acquisition_cost >= 0),
    asking_price numeric(14, 2) CHECK (asking_price IS NULL OR asking_price >= 0),
    currency_code char(3) NOT NULL DEFAULT 'INR',
    intake_odometer integer NOT NULL DEFAULT 0 CHECK (intake_odometer >= 0),
    acquired_at timestamptz NOT NULL DEFAULT now(),
    closed_at timestamptz,
    CHECK ((closed_at IS NOT NULL) =
           (inventory_status IN ('SOLD', 'RETURNED', 'REMOVED'))),
    UNIQUE (dealership_id, stock_number),
    UNIQUE (acquisition_id, dealership_id),
    FOREIGN KEY (vehicle_id, model_id)
        REFERENCES vehicle(vehicle_id, model_id),
    FOREIGN KEY (listing_id, model_id, dealership_id)
        REFERENCES vehicle_listing(listing_id, model_id, dealership_id)
);

CREATE UNIQUE INDEX acquisition_one_open_period_per_vehicle
    ON acquisition(vehicle_id) WHERE closed_at IS NULL;

CREATE TABLE ownership_period (
    ownership_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    vehicle_id uuid NOT NULL REFERENCES vehicle(vehicle_id),
    owner_party_id uuid NOT NULL REFERENCES party(party_id),
    started_at timestamptz NOT NULL,
    ended_at timestamptz,
    reason text,
    CHECK (ended_at IS NULL OR ended_at > started_at)
);

CREATE UNIQUE INDEX ownership_one_current_owner
    ON ownership_period(vehicle_id) WHERE ended_at IS NULL;

CREATE TABLE inspection (
    inspection_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    acquisition_id uuid NOT NULL REFERENCES acquisition(acquisition_id),
    inspector_user_id uuid NOT NULL REFERENCES app_user(user_id),
    odometer integer NOT NULL CHECK (odometer >= 0),
    condition_grade text NOT NULL,
    damage_notes text,
    result text NOT NULL CHECK (result IN ('PASS', 'REPAIR_REQUIRED', 'FAIL')),
    estimated_repair_cost numeric(14, 2)
        CHECK (estimated_repair_cost IS NULL OR estimated_repair_cost >= 0),
    inspected_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE refurbishment_order (
    work_order_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    acquisition_id uuid NOT NULL REFERENCES acquisition(acquisition_id),
    inspection_id uuid REFERENCES inspection(inspection_id),
    status text NOT NULL DEFAULT 'OPEN'
        CHECK (status IN ('OPEN', 'IN_PROGRESS', 'COMPLETED', 'CANCELLED')),
    estimated_cost numeric(14, 2)
        CHECK (estimated_cost IS NULL OR estimated_cost >= 0),
    opened_at timestamptz NOT NULL DEFAULT now(),
    completed_at timestamptz,
    CHECK (completed_at IS NULL OR completed_at >= opened_at)
);

CREATE UNIQUE INDEX refurbishment_one_active_order
    ON refurbishment_order(acquisition_id)
    WHERE status IN ('OPEN', 'IN_PROGRESS');

CREATE TABLE refurbishment_cost (
    cost_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    work_order_id uuid NOT NULL REFERENCES refurbishment_order(work_order_id),
    vendor_party_id uuid REFERENCES party(party_id),
    cost_type text NOT NULL CHECK (cost_type IN ('PARTS', 'LABOUR', 'TRANSPORT', 'OTHER')),
    description text NOT NULL,
    amount numeric(14, 2) NOT NULL CHECK (amount >= 0),
    incurred_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE location_event (
    location_event_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    acquisition_id uuid NOT NULL REFERENCES acquisition(acquisition_id),
    from_area_id uuid REFERENCES site_area(area_id),
    to_area_id uuid NOT NULL REFERENCES site_area(area_id),
    moved_by_user_id uuid NOT NULL REFERENCES app_user(user_id),
    moved_at timestamptz NOT NULL DEFAULT now(),
    reason text,
    CHECK (from_area_id IS NULL OR from_area_id <> to_area_id)
);

CREATE TABLE inventory_event (
    inventory_event_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    acquisition_id uuid NOT NULL REFERENCES acquisition(acquisition_id),
    listing_id uuid NOT NULL REFERENCES vehicle_listing(listing_id),
    performed_by_user_id uuid REFERENCES app_user(user_id),
    event_type text NOT NULL
        CHECK (event_type IN ('ACQUIRED', 'AVAILABLE', 'RESERVED', 'RELEASED', 'SOLD', 'RESTOCKED', 'REFURBISHING', 'REMOVED', 'RETURNED')),
    available_quantity_delta integer NOT NULL,
    idempotency_key text NOT NULL UNIQUE,
    occurred_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE price_change (
    price_change_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    listing_id uuid NOT NULL REFERENCES vehicle_listing(listing_id),
    changed_by_user_id uuid NOT NULL REFERENCES app_user(user_id),
    old_price numeric(14, 2) NOT NULL CHECK (old_price >= 0),
    new_price numeric(14, 2) NOT NULL CHECK (new_price >= 0),
    changed_at timestamptz NOT NULL DEFAULT now(),
    CHECK (old_price <> new_price)
);

CREATE TABLE vehicle_document (
    document_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    vehicle_id uuid REFERENCES vehicle(vehicle_id),
    acquisition_id uuid REFERENCES acquisition(acquisition_id),
    document_type text NOT NULL,
    storage_key text NOT NULL,
    uploaded_at timestamptz NOT NULL DEFAULT now(),
    CHECK (vehicle_id IS NOT NULL OR acquisition_id IS NOT NULL)
);

CREATE TABLE reservation (
    reservation_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    acquisition_id uuid NOT NULL REFERENCES acquisition(acquisition_id),
    customer_party_id uuid NOT NULL REFERENCES customer(party_id),
    status text NOT NULL DEFAULT 'ACTIVE'
        CHECK (status IN ('ACTIVE', 'EXPIRED', 'RELEASED', 'CONVERTED')),
    created_at timestamptz NOT NULL DEFAULT now(),
    expires_at timestamptz NOT NULL,
    CHECK (expires_at > created_at)
);

CREATE UNIQUE INDEX reservation_one_active_per_acquisition
    ON reservation(acquisition_id) WHERE status = 'ACTIVE';

CREATE TABLE sale (
    sale_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    dealership_id uuid NOT NULL REFERENCES dealership(dealership_id),
    buyer_customer_party_id uuid NOT NULL REFERENCES customer(party_id),
    created_by_user_id uuid NOT NULL REFERENCES app_user(user_id),
    authorized_by_user_id uuid REFERENCES app_user(user_id),
    status text NOT NULL DEFAULT 'DRAFT'
        CHECK (status IN ('DRAFT', 'COMPLETED', 'CANCELLED', 'REFUNDED')),
    total_amount numeric(14, 2) NOT NULL DEFAULT 0 CHECK (total_amount >= 0),
    currency_code char(3) NOT NULL DEFAULT 'INR',
    created_at timestamptz NOT NULL DEFAULT now(),
    completed_at timestamptz,
    CHECK ((status = 'COMPLETED' AND completed_at IS NOT NULL)
        OR (status <> 'COMPLETED')),
    UNIQUE (sale_id, dealership_id)
);

-- Insert sale items only when finalising a sale. A later return creates a new
-- acquisition period for the same VIN, preserving the original sale history.
CREATE TABLE sale_item (
    sale_item_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    sale_id uuid NOT NULL,
    acquisition_id uuid NOT NULL UNIQUE,
    dealership_id uuid NOT NULL,
    agreed_price numeric(14, 2) NOT NULL CHECK (agreed_price >= 0),
    discount numeric(14, 2) NOT NULL DEFAULT 0 CHECK (discount >= 0),
    tax_amount numeric(14, 2) NOT NULL DEFAULT 0 CHECK (tax_amount >= 0),
    CHECK (discount <= agreed_price),
    FOREIGN KEY (sale_id, dealership_id)
        REFERENCES sale(sale_id, dealership_id),
    FOREIGN KEY (acquisition_id, dealership_id)
        REFERENCES acquisition(acquisition_id, dealership_id)
);

CREATE TABLE payment (
    payment_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    sale_id uuid NOT NULL REFERENCES sale(sale_id),
    amount numeric(14, 2) NOT NULL CHECK (amount > 0),
    method text NOT NULL,
    status text NOT NULL CHECK (status IN ('PENDING', 'SETTLED', 'FAILED', 'REFUNDED')),
    external_reference text UNIQUE,
    paid_at timestamptz
);

CREATE TABLE trade_in (
    trade_in_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    sale_id uuid NOT NULL REFERENCES sale(sale_id),
    acquisition_id uuid NOT NULL UNIQUE REFERENCES acquisition(acquisition_id),
    agreed_value numeric(14, 2) NOT NULL CHECK (agreed_value >= 0)
);

CREATE TABLE audit_event (
    audit_event_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    actor_user_id uuid REFERENCES app_user(user_id),
    entity_type text NOT NULL,
    entity_id uuid NOT NULL,
    action text NOT NULL,
    details jsonb NOT NULL DEFAULT '{}'::jsonb,
    occurred_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX vehicle_model_category_idx ON vehicle_model(category);
CREATE INDEX vehicle_listing_search_idx
    ON vehicle_listing(status, dealership_id, advertised_price)
    WHERE deleted_at IS NULL;
CREATE INDEX acquisition_listing_status_idx
    ON acquisition(listing_id, inventory_status, acquired_at);
CREATE INDEX acquisition_source_idx ON acquisition(source_party_id);
CREATE INDEX inspection_acquisition_idx ON inspection(acquisition_id, inspected_at DESC);
CREATE INDEX refurbishment_cost_order_idx ON refurbishment_cost(work_order_id);
CREATE INDEX location_event_history_idx ON location_event(acquisition_id, moved_at DESC);
CREATE INDEX inventory_event_history_idx ON inventory_event(acquisition_id, occurred_at DESC);
CREATE INDEX ownership_vehicle_history_idx ON ownership_period(vehicle_id, started_at DESC);
CREATE INDEX reservation_customer_idx ON reservation(customer_party_id, created_at DESC);
CREATE INDEX sale_customer_idx ON sale(buyer_customer_party_id, created_at DESC);
CREATE INDEX sale_dealership_idx ON sale(dealership_id, created_at DESC);
CREATE INDEX payment_sale_idx ON payment(sale_id);
CREATE INDEX audit_event_target_idx ON audit_event(entity_type, entity_id, occurred_at DESC);

-- The kata's GET /api/vehicles response can read this view. Quantity is derived
-- from committed, available physical cars, so it cannot drift from unit status.
CREATE VIEW vehicle_inventory AS
SELECT
    l.listing_id AS id,
    l.dealership_id,
    mk.name AS make,
    vm.name AS model,
    vm.category,
    l.condition_class,
    l.advertised_price AS price,
    l.currency_code,
    count(a.acquisition_id)::integer AS quantity,
    l.status
FROM vehicle_listing AS l
JOIN vehicle_model AS vm ON vm.model_id = l.model_id
JOIN make AS mk ON mk.make_id = vm.make_id
LEFT JOIN acquisition AS a
    ON a.listing_id = l.listing_id
   AND a.inventory_status = 'AVAILABLE'
WHERE l.deleted_at IS NULL
GROUP BY l.listing_id, l.dealership_id, mk.name, vm.name, vm.category,
         l.condition_class, l.advertised_price, l.currency_code, l.status;

COMMIT;
