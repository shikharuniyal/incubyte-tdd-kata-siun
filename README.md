# Incubyte Motors: Car Dealership Inventory System

A full-stack inventory system for a car dealership, built test-first for the Incubyte TDD kata.

- **Backend:** Django + Django REST Framework, a token-secured REST API on **PostgreSQL**.
- **Frontend:** a **React + Tailwind CSS** single-page app where customers browse, search and buy cars, and dealership staff add, edit, restock and delete them.

Every physical car is tracked by its VIN, but the API exposes the quantity-based "vehicle" resource the kata asks for. **Quantity is never stored.** It is derived from the cars actually available, so it can't drift, and concurrent purchases can't oversell the last car.

![Admin view of the showroom](docs/screenshots/03-dashboard-admin.png)

| | |
|---|---|
| Backend tests | **140 passing**, 99% statement coverage, against real PostgreSQL ([report](docs/TEST_REPORT.md)) |
| Frontend tests | **63 passing**, 93% line coverage ([report](docs/TEST_REPORT.md)) |
| AI chat log | [`PROMPTS.md`](PROMPTS.md) |
| Live demo | Not deployed. Run it locally in about five minutes (below). |

---

## Contents

1. [What it does](#what-it-does)
2. [Tech stack](#tech-stack)
3. [Run it locally](#run-it-locally)
4. [Running the tests](#running-the-tests)
5. [API reference](#api-reference)
6. [Design](#design)
7. [Screenshots](#screenshots)
8. [Project structure](#project-structure)
9. [My AI Usage](#my-ai-usage)

---

## What it does

**Every signed-in user can:**
- register and sign in (JWT access token plus a rotating refresh token);
- browse the showroom, with each model's live stock ("5 in stock", "Only 1 left", "Sold out");
- search by make, model, category and price range;
- **purchase** a car. The button is disabled when the quantity is zero, and each purchase records a real sale.

**Dealership staff** (any role at a dealership) can also add vehicles and edit their details.

**Dealership admins** can also **restock** a vehicle (optionally recording each car's VIN) and **delete** it.

All kata endpoints are implemented: `POST /api/auth/register`, `POST /api/auth/login`, and `POST/GET /api/vehicles`, `GET /api/vehicles/search`, `PUT/DELETE /api/vehicles/:id`, `POST /api/vehicles/:id/purchase` and `POST /api/vehicles/:id/restock`, all protected. Each vehicle has a unique id, make, model, category, price and quantity in stock.

---

## Tech stack

| Layer | Choice | Why |
|---|---|---|
| API | Python 3.12+, **Django 6.1**, **Django REST Framework 3.18** | Mature ORM, transactions and row locking; serializers for validation |
| Database | **PostgreSQL 16+** (developed on 18.6) | Real constraints, partial unique indexes, `SELECT … FOR UPDATE SKIP LOCKED`, views |
| Auth | **PyJWT** access tokens (HS256, 30 min) + random refresh tokens stored as SHA-256 hashes | Stateless requests; refresh tokens can be rotated and revoked |
| Frontend | **React 19**, **TypeScript**, **Tailwind CSS 4**, React Router, Vite | The kata's required SPA stack |
| Backend tests | pytest, pytest-django, pytest-cov | |
| Frontend tests | Vitest, Testing Library, v8 coverage | |

---

## Run it locally

### Prerequisites

- **Python 3.12+**, **Node.js 20+**, **PostgreSQL 16+**
- A PostgreSQL user that may create databases (the test runner creates a temporary `test_dealership` database).

### 1. Get the code

```bash
git clone https://github.com/shikharuniyal/incubyte-tdd-kata-siun.git
cd incubyte-tdd-kata-siun
```

### 2. Start PostgreSQL and create the database

Use whichever is easiest for you.

**A. An existing PostgreSQL install**
```bash
createdb -U postgres dealership
```

**B. Docker**
```bash
docker run -d --name dealership-db -p 5432:5432 \
  -e POSTGRES_USER=app -e POSTGRES_PASSWORD=app -e POSTGRES_DB=dealership postgres:18
```

**C. A database cluster kept inside the project folder** (how I develop: PostgreSQL binaries anywhere, data in `./pgdata`, which is git-ignored)
```bash
initdb -D pgdata -U app --auth=trust -E UTF8 --no-locale
pg_ctl -D pgdata -l pgdata/server.log start
createdb -U app -h localhost dealership
```

### 3. Backend

```bash
python -m venv venv
# Windows: venv\Scripts\activate      macOS/Linux: source venv/bin/activate
pip install -r backend/requirements.txt

cd backend
cp .env.example .env        # then set DATABASE_URL for your database, e.g.
                            # postgresql://app:app@localhost:5432/dealership   (Docker option)
python manage.py migrate    # builds the schema from database/schema.sql
python manage.py seed_demo  # demo dealership, accounts and 10 vehicles (safe to re-run)
python manage.py runserver  # API on http://localhost:8000
```

`seed_demo` creates two accounts. You can also use the "Use … demo" buttons on the login page.

| Role | Email | Password |
|---|---|---|
| Admin | `admin@dealership.local` | `Admin@12345` |
| Customer | `customer@dealership.local` | `Customer@12345` |

Change them with `--admin-password` and `--customer-password`, or the `DEMO_ADMIN_PASSWORD` and `DEMO_CUSTOMER_PASSWORD` environment variables.

### 4. Frontend

In a second terminal:
```bash
cd frontend
npm install
npm run dev                 # http://localhost:5173
```
The Vite dev server proxies `/api` to `http://localhost:8000`. If your API runs elsewhere, start it with `VITE_API_PROXY=http://127.0.0.1:8001 npm run dev`. For a production build pointing at a remote API, set `VITE_API_URL` and run `npm run build`.

> **Windows note:** Vite does not support a `#` in the project path (for example `E:\#Code\...`). If your clone lives under such a folder, map it to a drive letter first (`subst W: "E:\#Code\incubyte-tdd-kata-siun"`, then work from `W:\frontend`), or clone it somewhere else.

### Configuration (`backend/.env`)

| Variable | Default | Meaning |
|---|---|---|
| `DATABASE_URL` | `postgresql://app@localhost:5432/dealership` | Database connection |
| `DJANGO_SECRET_KEY` | dev-only value | Django secret; set a long random value outside development |
| `JWT_SIGNING_KEY` | `DJANGO_SECRET_KEY` | Key used to sign access tokens |
| `JWT_ACCESS_MINUTES` / `JWT_REFRESH_DAYS` | `30` / `7` | Token lifetimes |
| `DJANGO_DEBUG` | `true` | Debug mode |

---

## Running the tests

```bash
# Backend: from backend/, with PostgreSQL running and the virtualenv active
pytest                                  # 140 tests
pytest --cov --cov-report=term          # with coverage (99%)

# Frontend: from frontend/
npm test                                # 63 tests
npm run coverage                        # with coverage (93% lines)
```

The full output of both suites, with per-file coverage, is in **[docs/TEST_REPORT.md](docs/TEST_REPORT.md)**.

Backend tests use a real PostgreSQL database built by the same migration as production, so constraints and the inventory view are exercised for real. One test races two buyers for the last car on separate database connections and asserts that exactly one succeeds.

---

## API reference

All request and response bodies are JSON. Protected endpoints need `Authorization: Bearer <access token>`.

| Method | Path | Who | Purpose |
|---|---|---|---|
| POST | `/api/auth/register` | anyone | Create an account. Returns `{access, refresh, user}` |
| POST | `/api/auth/login` | anyone | Sign in. Returns `{access, refresh, user}` |
| POST | `/api/auth/refresh` | holder of a refresh token | Swap a refresh token (single use) for a new pair |
| POST | `/api/auth/logout` | holder of a refresh token | Revoke the refresh token |
| GET | `/api/auth/me` | signed in | Current user and their dealership roles |
| GET | `/api/vehicles` | signed in | All vehicles, with live quantity |
| GET | `/api/vehicles/search?make=&model=&category=&min_price=&max_price=` | signed in | Case-insensitive partial text match; inclusive price range |
| POST | `/api/vehicles` | staff of a dealership | Add a vehicle (and `quantity` cars of it) |
| GET | `/api/vehicles/:id` | signed in | One vehicle |
| PUT | `/api/vehicles/:id` | staff of its dealership | Update details (partial). Quantity is not editable here |
| DELETE | `/api/vehicles/:id` | **admin** of its dealership | Archive the listing and take unsold cars out of stock |
| POST | `/api/vehicles/:id/purchase` | signed in | Buy one car. Quantity −1 |
| POST | `/api/vehicles/:id/restock` | **admin** of its dealership | Receive cars. Quantity +N |

**A vehicle**
```json
{
  "id": "3f0c…", "make": "Toyota", "model": "Corolla Altis", "category": "Sedan",
  "price": 1850000.0, "quantity": 5, "condition": "NEW", "currency_code": "INR",
  "model_year": 2024, "variant": "BASE",
  "dealership_id": "2127…", "dealership_name": "Incubyte Motors - Main Branch"
}
```

**Add:** `POST /api/vehicles`
```json
{ "make": "Toyota", "model": "Corolla", "category": "Sedan", "price": 1850000,
  "quantity": 3, "model_year": 2024, "variant": "BASE", "condition": "NEW" }
```
`quantity`, `model_year`, `variant`, `condition` and `currency_code` are optional. A staff member at several dealerships must also send `dealership_id`.

**Purchase:** `POST /api/vehicles/:id/purchase` returns `{ "vehicle": {…}, "sale_id": "…" }`, or **409** `{"detail": "Toyota Corolla is out of stock."}`.

**Restock:** `POST /api/vehicles/:id/restock`
```json
{ "quantity": 2 }                                  // cars get temporary IDs until VINs are recorded
{ "vins": ["MA3FB32S0R0123456", "MA3FB32S0R0654321"], "unit_cost": 1500000 }
```

**Safe retries:** purchase and restock accept an optional `Idempotency-Key` header. Repeating a request with the same key (per user) returns the first result instead of buying or restocking twice. The frontend sends a fresh key for each click.

**Errors** use DRF's shape: `{"detail": "…"}`, or field errors such as `{"email": ["An account with this email already exists."]}`. The status codes are:
- `400` invalid input
- `401` missing or invalid token
- `403` not allowed
- `404` not found
- `409` conflict (out of stock, VIN already in stock, or a concurrent change)

---

## Design

### Domain model

I designed the domain before writing code. I sketched it by hand, refined it with an AI assistant into a written spec, and turned it into a PostgreSQL schema.

| Hand-drawn UML class sketch | Hand-drawn ER sketch |
|---|---|
| ![UML](docs/diagrams/UML.jpeg) | ![ER](docs/diagrams/ER.png) |

- The full design (class, state and sequence diagrams, plus three ER views): [`docs/design/diagrams.md`](docs/design/diagrams.md).
- The schema the application runs on: **[`database/schema.sql`](database/schema.sql)** (33 tables and the `vehicle_inventory` view).

The key idea is how the kata's quantity-based "vehicle" relates to physical cars:

```
Manufacturer ─ Make ─ VehicleModel ─┬─ VehicleListing   ← the API's "vehicle": dealership + model + price
                                    │        │
                                    └─ Vehicle (one physical car, unique VIN)
                                             │
                                    Acquisition  ← one period a car is in a dealership's stock
                                    (AVAILABLE → SOLD / REMOVED …)

quantity = number of AVAILABLE acquisitions of a listing   (the vehicle_inventory view)
```

- A **listing** is what a dealership sells (a model at a price). `id`, `make`, `model`, `category` and `price` come from it.
- A **vehicle** is one physical car with a VIN. A car that is sold and later bought back keeps its record, and gets a new **acquisition**.
- **Quantity is derived, not stored.** Adding stock creates cars; buying marks one car `SOLD`. The count cannot disagree with the cars that exist.
- Every stock change also writes an **inventory event** (an append-only ledger with an idempotency key), an **ownership period** (dealer → buyer), and an **audit event**, all in the same transaction.

### Concurrency

A purchase runs as one database transaction:
1. It locks the listing row (`SELECT … FOR NO KEY UPDATE`).
2. It picks the oldest available car (`FOR UPDATE SKIP LOCKED`).
3. It creates the sale and sale item, marks the car `SOLD`, moves ownership to the buyer, and logs the event, then commits.

Two buyers racing for the last car are serialised: one gets it, and the other gets `409 out of stock`. This is proven by a test that uses two real connections. Unique constraints in the schema (one open acquisition per car, one sale item per acquisition, unique idempotency keys) are the last line of defence. If they ever fire, the API returns `409`, not a `500`.

### Backend structure (SOLID, layered)

| Layer | Modules | Responsibility |
|---|---|---|
| HTTP | `accounts/views.py`, `vehicles/views.py`, serializers | Parse and validate input, call one use case, shape the response |
| Use cases | `vehicles/catalog.py` (add/update/delete), `vehicles/stock.py` (purchase/restock), `accounts/services.py`, `accounts/tokens.py` | Business rules and transactions. They know nothing about HTTP |
| Policies | `vehicles/policies.py`, `accounts/roles.py` | Who may do what, scoped per dealership |
| Read model | `vehicles/queries.py` | List and search over the `vehicle_inventory` view |
| Persistence | `dealership/models/*` | Unmanaged Django models mapped onto `database/schema.sql` |
| Errors | `dealership/errors.py`, `config/exception_handler.py` | Domain errors are mapped to HTTP status codes in one place |

Migration `0001` executes `database/schema.sql` itself, so the SQL file stays the single source of truth for constraints, partial indexes, composite foreign keys and the view.

### Decisions worth knowing

- **Adding and editing vehicles requires a dealership staff role.** The kata marks these endpoints as protected and makes only delete and restock admin-only. A listing must belong to a dealership, so a plain customer account can't create one (`403`).
- **`PUT` is a partial update.** Price changes are recorded in `price_change`. Make or model can only change before any car has been stocked; after that the cars physically are that model (`409`, so add a new vehicle instead).
- **`DELETE` is a soft delete.** The listing is archived and unsold cars are marked `REMOVED`, so sales history and audit records survive.
- **Restocking without VINs** gives each car a temporary identifier (`PENDING-…`, which can never collide with a real VIN), so the kata's simple `{ "quantity": n }` works.
- **Tokens:** the access JWT is short-lived. Refresh tokens are random, single-use (rotated on every refresh), revocable on logout, and only their SHA-256 hash is stored. The SPA keeps tokens in `localStorage` for simplicity; an httpOnly-cookie setup would be the next hardening step.
- **The schema covers more than the kata uses** (reservations, inspections, refurbishment, transfers, payments, trade-ins). Those tables exist and are constrained, ready for future features.

---

## Screenshots

| | |
|---|---|
| **Sign in** (with demo shortcuts) ![](docs/screenshots/01-login.png) | **Register** ![](docs/screenshots/02-register.png) |
| **Search and filter** (SUVs up to ₹20 L) ![](docs/screenshots/08-search-filters.png) | **Purchase:** the Thar sells its last car, shows *Sold out* and its button is disabled ![](docs/screenshots/09-purchase-success.png) |
| **Admin: add a vehicle** ![](docs/screenshots/04-add-vehicle.png) | **Admin: restock** ![](docs/screenshots/05-restock.png) |
| **Edit a vehicle** ![](docs/screenshots/06-edit-vehicle.png) | **Admin: delete, with confirmation** ![](docs/screenshots/07-delete-confirm.png) |
| **Mobile layout** ![](docs/screenshots/10-mobile.png) | **Full admin dashboard** ![](docs/screenshots/03-dashboard-admin.png) |

---

## Project structure

```
├── backend/                 Django project
│   ├── config/              settings, URLs, exception handler
│   ├── dealership/          models for database/schema.sql, schema migration, errors, audit
│   ├── accounts/            registration, login, JWT + refresh sessions, roles
│   ├── vehicles/            catalogue, stock (purchase/restock), policies, queries, seed_demo
│   └── tests/               pytest suite (API, concurrency, schema, audit, seed)
├── frontend/                React + TypeScript + Tailwind SPA (Vite)
│   └── src/                 api/, auth/, components/, pages/, lib/  (tests sit next to code)
├── database/schema.sql      PostgreSQL schema (single source of truth)
├── docs/
│   ├── diagrams/            hand-drawn UML and ER diagrams
│   ├── design/diagrams.md   full UML/ER/state/sequence design spec
│   ├── screenshots/
│   ├── problem-statement.md the kata brief
│   └── TEST_REPORT.md
├── PROMPTS.md               raw AI chat log (GPT design conversation)
└── README.md
```

---

## My AI Usage

### My own work
The idea, the requirements analysis, the domain modelling, the hand-drawn UML and ER diagrams (`docs/diagrams/`), the methodology and the overall plan are mine.

### Tools I used
- **OpenAI Codex (GPT):** I used it as a design sparring partner. It reviewed my hand-drawn diagrams for a dealership that sells both new and used cars, compared Snowflake with PostgreSQL for my concurrency needs, converted my diagrams into Mermaid, and drafted `database/schema.sql` from my refined design. The full, unedited conversation is in [`PROMPTS.md`](PROMPTS.md).


### Reflection
Working with AI let me spend my effort on the decisions that matter. Those included:
- what a "vehicle" means (a listing, not a single car);
- why quantity must be derived from the cars in stock;
- how to keep the last car from being sold twice;
- who may restock or delete.

The AI's suggestions still needed checking. I accepted some design changes, such as separating a model from a physical car and stock periods, and made the remaining judgement calls myself.

---

