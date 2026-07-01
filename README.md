# E-Pharmacy

A web application that enables users to locate and compare nearby pharmacies based on
geographic proximity. Users click on an interactive map to set their position and receive
a paginated list of registered pharmacies sorted by distance, from nearest to furthest.

---

## Project context

Bachelor's thesis submitted in partial fulfilment of the Bachelor of Engineering in
Informatics Engineering, Software and Information Systems department, Faculty of
Informatics Engineering, Tishreen University (Latakia, Syria). Supervised by
Dr. Basel Hasan. Academic year 2023–2024. Team of 3. Final grade: 90/100.

---

## Architecture

The system follows a REST API architecture. The Django backend exposes a GeoJSON
endpoint; the frontend consumes it directly via the Fetch API. Distance computation
is delegated entirely to PostGIS.

```
┌────────────────────────────────┐                   ┌────────────────────────────────────────────┐
│  Frontend                      │   HTTP / JSON     │  Backend                                   │
│  HTML · CSS · JavaScript       │ ───────────────►  │  Django 5.0.6 + DRF 3.15.1                 │
│  Leaflet.js 1.9.4              │                   │  GeoDjango + django-rest-framework-gis     │
│  Bootstrap 5.3.3               │ ◄───────────────  │                                            │
└────────────────────────────────┘  GeoJSON response │  ┌──────────────────────────────────────┐  │
                                                     │  │  PostgreSQL + PostGIS                │  │
                                                     │  │  (PointField · ST_Distance)          │  │
                                                     │  └──────────────────────────────────────┘  │
                                                     └────────────────────────────────────────────┘
```

### Backend

| Component                     | Version / detail                                                                  |
|-------------------------------|-----------------------------------------------------------------------------------|
| Python                        | 3.10+                                                                             |
| Django                        | 5.0.6                                                                             |
| Django REST Framework         | 3.15.1                                                                            |
| GeoDjango                     | Bundled with Django; provides `PointField` and spatial ORM support                |
| django-rest-framework-gis     | `GeoFeatureModelSerializer`, `DistanceToPointOrderingFilter`, `GeoJsonPagination` |
| dj-rest-auth                  | 6.0.0; token-based authentication endpoints                                       |
| django-allauth                | Email address verification and account management                                 |
| django-cors-headers           | 4.3.1                                                                             |
| Database                      | PostgreSQL with PostGIS extension                                                 |

### Frontend

| Component   | Version / detail                                             |
|-------------|--------------------------------------------------------------|
| Leaflet.js  | 1.9.4, loaded from CDN (unpkg); tile provider: OpenStreetMap |
| Bootstrap   | 5.3.3                                                        |
| Font Awesome| 4.7.0                                                        |
| JavaScript  | Vanilla JS; Fetch API; no framework and no build step        |

---

## User roles

The system defines three actors. At the authentication layer only two levels are
distinguished — `is_staff = True` (administrator) and `is_staff = False` (everyone else):

| Actor             | `is_staff` | Description                                                                                                           |
|-------------------|------------|-----------------------------------------------------------------------------------------------------------------------|
| **Administrator** | `True`     | Registers pharmacies and links each one to a pharmacist account; directed to the pharmacy registration page on login  |
| **Pharmacist**    | `False`    | A registered user whose account is linked to a pharmacy by an administrator; carries no additional system permissions |
| **Regular user**  | `False`    | Views pharmacies sorted by distance; directed to the nearest-pharmacies page on login                                 |

The thesis class diagram (Figure 2, page 10) shows a request/approval workflow between
these two roles — `Pharmacist.addPharmacy()` and `Admin.approveRequest()` — in which a
pharmacist would request to register their pharmacy and an administrator would approve
it. This was simplified during implementation: the administrator registers pharmacies
directly and assigns a pharmacist to each one by username, with no separate request or
approval step.

---

## Database schema

Table names below follow the lowercase convention shown in the thesis ER diagram
(Figure 6, page 14) — see [Known limitations](#known-limitations) for a note on a
minor case difference between this and `settings.py`.

### `apis_pharmacy`

| Field            | Database type      | Constraints                                                           |
|------------------|--------------------|-----------------------------------------------------------------------|
| `id`             | `BIGINT`           | Primary key                                                           |
| `name`           | `VARCHAR(255)`     | `UNIQUE`                                                              |
| `location`       | `POINT` (PostGIS)  | Geospatial point; used as the geometry field in GeoJSON output        |
| `phone_number`   | `VARCHAR(10)`      | `UNIQUE`; validated against regex `09XXXXXXXX`                        |
| `email`          | `VARCHAR(254)`     | `UNIQUE`; nullable                                                    |
| `pharmacist_id`  | `INT`              | `OneToOneField → auth_user`; each pharmacy has exactly one pharmacist |

A custom manager method, `create_pharmacy()`, performs the following as a sequence of
separate statements: updates the linked user's `first_name`/`last_name`, saves the
`Pharmacy` row, then loops over the submitted business hours calling
`get_or_create()` and linking each result to the pharmacy via the M2M relationship.
This sequence is not wrapped in a database transaction (see
[Known limitations](#known-limitations)).

### `apis_businesshours`

| Field              | Database type   | Constraints                                                              |
|--------------------|-----------------|--------------------------------------------------------------------------|
| `id`               | `BIGINT`        | Primary key                                                              |
| `day_of_the_week`  | `VARCHAR(3)`    | Choices: `Mon` · `Tue` · `Wed` · `Thr` · `Fri` · `Sat` · `Sun`           |
| `opened_at`        | `TIME`          | Nullable (`NULL` indicates all-day open when `closed_at` is also `NULL`) |
| `closed_at`        | `TIME`          | Nullable                                                                 |

> **Note:** Thursday's stored code is `Thr`, not the more conventional `Thu` — this is
> the value defined in `models.py` (`THIRSDAY = "Thr"`, with the choice's display label
> itself spelled `"Thirsday"`). Any client code integrating with this API must send
> `Thr`, exactly as it appears in the source, or the value will not match a valid choice.

A junction table (`apis_businesshours_pharmacies`) links `BusinessHours` to `Pharmacy`
as a many-to-many relationship, allowing one hours entry to be shared across multiple
pharmacies with identical schedules.

**Constraints on `BusinessHours`:**

- `UNIQUE` on (`day_of_the_week`, `opened_at`, `closed_at`) — prevents duplicate entries
- Check constraint: `opened_at < closed_at`, OR both fields are `NULL` — partial nulls are rejected

### Authentication tables (managed by third-party packages)

| Table                        | Purpose                                                            |
|------------------------------|--------------------------------------------------------------------|
| `auth_user`                  | Django built-in user model (`username`, `email`, `is_staff`, etc.) |
| `authtoken_token`            | DRF token store; one token per user                                |
| `account_emailaddress`       | django-allauth; tracks verified/primary email addresses            |
| `account_emailconfirmation`  | django-allauth; stores time-limited verification keys              |

---

## API reference

### Base URL (development)

```
http://127.0.0.1:8000/
```

> The frontend currently hardcodes this address. Deploying to any other environment
> requires updating the URL in the frontend source files.

### Authentication — `/api/auth/`

Confirmed from `urls.py` and `AuthAPIs/views.py`: registration and login use
dj-rest-auth's unmodified default views (`RegisterView`, `LoginView`, `LogoutView`,
`UserDetailsView`, `VerifyEmailView`, `ResendEmailVerificationView`,
`PasswordResetView`, `PasswordResetConfirmView`). The only customisation in
`REST_AUTH` is the token output format
(`TOKEN_SERIALIZER: 'AuthAPIs.serializers.TokenSerializer'`) — no
`REGISTER_SERIALIZER` override is present. Two paths route to project-specific view
functions, `InformEmailConfirmation` and `PasswordRestConfirmation` (name as it
appears in `urls.py`); their implementations are confirmed below.

| Method | Path                                         | View                                              | Description                                                                                                                                                                                                                                                                      |
|--------|-----------------------------------------------|--------------------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `POST` | `/register/`                                  | `RegisterView` (default)                         | Register a new user; sends a verification email                                                                                                                                                                                                                                  |
| `POST` | `/login/`                                     | `LoginView` (default)                            | Authenticate with username and password; returns a token and user object (including `is_staff`)                                                                                                                                                                                  |
| `POST` | `/logout/`                                    | `LogoutView` (default)                           | Invalidate the current token                                                                                                                                                                                                                                                     |
| `GET`  | `/user/`                                      | `UserDetailsView` (default)                      | Return the authenticated user's details                                                                                                                                                                                                                                          |
| `POST` | `/register/verify-email/`                     | `VerifyEmailView` (default)                      | Confirm registration using the emailed key, submitted in the request body                                                                                                                                                                                                        |
| `POST` | `/register/resend-email/`                     | `ResendEmailVerificationView` (default)          | Resend the verification email                                                                                                                                                                                                                                                    |
| `GET`  | `/account-confirm-email/<key>/`               | `InformEmailConfirmation` — project-specific     | Verification-link landing page. Internally issues a server-side `POST` to its own `/api/auth/account-confirm-email/` endpoint (`VerifyEmailView`) with the key, then renders `confirm_template.html`, showing a success or failure message based on that response's status code  |
| `GET`  | `/account-confirm-email/`                     | `VerifyEmailView` (default)                      | Named `account_email_verification_sent`; the "check your inbox" placeholder page required by django-allauth                                                                                                                                                                      |
| `POST` | `/password/reset/`                            | `PasswordResetView` (default)                    | Send a password-reset email containing a time-limited link                                                                                                                                                                                                                       |
| `GET`  | `/password/reset/confirm/<uidb64>/<token>/`   | `PasswordRestConfirmation` — project-specific    | Password-reset link landing page. Renders `password reset form.html`, passing `uidb64` and `token` into the page; the form's own JavaScript performs the actual `POST` to `/api/auth/password/reset/confirm/` on submission                                                      |
| `POST` | `/password/reset/confirm/`                    | `PasswordResetConfirmView` (default)             | Submit the new password using the emailed `uid` and `token`                                                                                                                                                                                                                      |

`InformEmailConfirmation`'s internal call also hardcodes the local development host
(see [Known limitations](#known-limitations)).

Passwords are stored using PBKDF2 with SHA-256 (Django's default `PASSWORD_HASHERS`;
no override present in `settings.py`). Email verification keys and password-reset
tokens both use the django-allauth/Django 3-day default expiry (no override present
in `settings.py`).

**On the login credential** (resolving the earlier open question): `settings.py` sets
`ACCOUNT_EMAIL_REQUIRED = True` and `ACCOUNT_EMAIL_VERIFICATION = "mandatory"`, but
does not set `ACCOUNT_AUTHENTICATION_METHOD` (or its newer equivalent,
`ACCOUNT_LOGIN_METHODS`). With no override, django-allauth falls back to its library
default, which is username-based authentication — this is why `login/` takes a
username rather than an email, matching the class diagram, even though email is
mandatory and verified at registration. Consistently, no `REGISTER_SERIALIZER`
override appears in `REST_AUTH`, so registration uses dj-rest-auth's default
`RegisterSerializer`, which requires `username`, `email`, `password1`, and `password2`
together — `username` could not be dropped from registration without replacing this
serializer.

### Pharmacy data — `/api/pharmacies/`

**`GET /api/pharmacies/?point=<lng>,<lat>&format=json`**

- **Permission**: `IsAuthenticated` — all logged-in users. Note: the project-wide
  `DEFAULT_PERMISSION_CLASSES` in `settings.py` is `AllowAny`; `PharmacyView`
  overrides this explicitly.
- **Required parameter**: `point` — the user's coordinates as `longitude,latitude`
- **Ordering**: Ascending distance from the supplied point. `DistanceToPointOrderingFilter`
  annotates the queryset using PostGIS `ST_Distance` (via Django's `GeometryDistance`
  expression) and orders by that annotation. Computation is performed in the database.
- **Pagination**: `GeoJsonPagination`; `PAGE_SIZE = 1` (one pharmacy per response).
  Each response includes `next` and `previous` URL fields for navigating the ordered list.
- **Response format**: GeoJSON `FeatureCollection`

```json
{
  "type": "FeatureCollection",
  "count": 2,
  "next": "http://127.0.0.1:8000/api/pharmacies/?format=json&page=2&point=35.783%2C35.523",
  "previous": null,
  "features": [
    {
      "type": "Feature",
      "geometry": {
        "type": "Point",
        "coordinates": [35.79274, 35.52410]
      },
      "properties": {
        "name": "Example Pharmacy",
        "pharmacist": { "first_name": "...", "last_name": "..." },
        "phone_number": "0996655443",
        "email": "pharmacy@example.com",
        "business_hours": [
          { "day_of_the_week": "Mon", "opened_at": "09:00", "closed_at": "21:00" },
          { "day_of_the_week": "Sat", "opened_at": "09:00", "closed_at": "21:00" }
        ]
      }
    }
  ]
}
```

**`POST /api/pharmacies/`** — Create a pharmacy.
Permission: `IsAuthenticated` AND `IsAdminUser` (`is_staff = True`). Only `list` and
`create` are routed for this viewset (see [Known limitations](#known-limitations)).

---

## Key components

### `PharmacySerializer`

A subclass of `GeoFeatureModelSerializer` (`django-rest-framework-gis`). The `location`
field is declared as the GeoJSON `geometry` field, so it is serialised as a GeoJSON
`Point` object rather than a raw coordinate pair. Each response is therefore a valid
GeoJSON `Feature`, directly consumable by Leaflet without client-side transformation.

`validate_business_hours()` enforces two rules on write: no more than 7 entries, and
no duplicate `day_of_the_week` values. This duplicates part of what the database's
`unique_together` constraint would otherwise catch, but does so before the write hits
the database, returning a clearer error message.

`create()` delegates entirely to the `Pharmacy.objects.create_pharmacy()` custom
manager method, rather than DRF's default nested-serializer creation logic — needed
because a pharmacy write also involves updating the linked `User`'s name fields and
creating/reusing `BusinessHours` rows.

### `PharmacistSerializer`

A nested `ModelSerializer` for the `User` model, used inside `PharmacySerializer`.
`username` is declared `write_only` — it is required on input (to look up or assign
the linked user) but is not included in API responses; only `first_name` and
`last_name` are returned.

### `BusinessHoursSerializer`

Overrides `to_internal_value()` to convert empty-string `opened_at`/`closed_at`
values to `None` before validation — this is what allows the frontend's "Open 24/7"
toggle (which submits empty strings) to map onto the model's all-day-open
representation (`NULL`/`NULL`). `validate()` then enforces, at the application layer,
the same rule the database's `CheckConstraint` enforces: both fields must be `NULL`,
or `opened_at` must be earlier than `closed_at`; a value on only one of the two fields
is rejected with a field-specific error message.

### `DistanceToPointOrderingFilter`

Provided by `django-rest-framework-gis`; registered in `filter_backends` on
`PharmacyView`. Reads the `point` query parameter, annotates each entry in the
`Pharmacy` queryset with the distance from its `location` field to that point using
PostGIS `ST_Distance`, and sorts the queryset in ascending order of that annotation.
All spatial computation is delegated to the database.

### `GeoJsonPagination`

A subclass of `PageNumberPagination` (`django-rest-framework-gis`). Wraps each page
of results in a GeoJSON `FeatureCollection` envelope so that every paginated response
remains a valid GeoJSON document. `PAGE_SIZE` is set to 1; the frontend advances
through results by following the `next` URL in each response.

---

## System design

The thesis document contains the following UML artefacts (Figures 1–6, pages 9–14):

- **Use Case Diagram** (Figure 1): four actors — Unregistered, Registered, Admin,
  Pharmacist — plus a Simple Mail Server as an external system; covers sign-up,
  email verification, login, password reset, viewing pharmacies, and adding pharmacies
- **Class Diagram** (Figure 2): `Pharmacy`, `BusinessHours`, `User`, `Admin`,
  `Pharmacist`, and the `Schedule` (M2M) relationship; includes the `Location` and
  `Weekday` data types
- **Sequence Diagrams**:
  - Figure 3: Account creation (registration → validation → verification email → token confirmation)
  - Figure 4: Login (credential validation → token issuance → role-based routing)
  - Figure 5: View pharmacies (map click → `GET` with `point` parameter → paginated GeoJSON response)
- **Entity–Relationship Diagram** (Figure 6): full database schema including all
  django-allauth and DRF token tables

These diagrams are in the thesis and are not reproduced here.

---

## Getting started

### Prerequisites

- Python 3.10 or later
- PostgreSQL with the PostGIS extension
- On Windows: an OSGeo4W installation with GDAL (the `settings.py` includes path
  configuration for the OSGeo4W default installation location)
- A Gmail account with an App Password configured (required for the SMTP email backend)

### Database

```sql
CREATE DATABASE epharmacy;
\c epharmacy
CREATE EXTENSION postgis;
```

### Backend

```bash
# 1. Create and activate a virtual environment
python -m venv venv
source venv/bin/activate       # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set credentials in EPharmacy/settings.py
#    DATABASES — NAME, USER, PASSWORD, HOST, PORT
#    EMAIL_HOST_USER, EMAIL_HOST_PASSWORD, DEFAULT_FROM_EMAIL

# 4. Apply migrations
python manage.py migrate

# 5. Create an administrator account
python manage.py createsuperuser

# 6. Start the development server
python manage.py runserver
```

The server runs at `http://127.0.0.1:8000/` by default.

### Frontend

No build step is required. The files in `frontend/` are plain HTML and can be opened
directly in a browser or served by any static file server, provided the Django server
is running at `http://127.0.0.1:8000/`.

> **CORS note**: `CORS_ALLOWED_ORIGINS` in `settings.py` includes `'null'` to permit
> requests from `file://` origins during local development. Remove this entry before
> any non-local deployment.

---

## Repository structure

```
E-Pharmacy/
├── EPharmacy/              # Django project root (settings.py, urls.py, wsgi.py)
├── apis/                   # Main Django application
│   ├── models.py           # Pharmacy, BusinessHours
│   ├── serializers.py      # PharmacySerializer (GeoFeatureModelSerializer)
│   ├── views.py            # PharmacyView (ModelViewSet + DistanceToPointOrderingFilter)
│   └── ...
├── requirements.txt
└── frontend/
    ├── sign up.html
    ├── sign in.html
    ├── pharmacy registration.html
    ├── nearest pharmacies.html
    └── ...
```

---

## Known limitations

Scope decisions and implementation gaps worth knowing before building on this code,
gathered in one place rather than scattered through the sections above.

- **`create_pharmacy()` is not transactional.** The manager method that creates a
  `Pharmacy` and its `BusinessHours` runs as a sequence of separate statements, not
  wrapped in `transaction.atomic()` (and `DATABASES['default']` does not set
  `ATOMIC_REQUESTS`, so there's no request-level wrapping either). A failure partway
  through the `BusinessHours` loop — for example a day entry that fails the
  `CheckConstraint` — would leave the already-created rows committed rather than
  rolled back. Wrapping the method body in `transaction.atomic()` would close this.

- **Hardcoded local host, on both sides.** The frontend's API calls and
  `InformEmailConfirmation`'s internal server-side call both point at
  `http://127.0.0.1:8000/`. Deploying anywhere other than localhost means updating
  both, not just the frontend.

- **`PharmacyView` exposes only `list` and `create`.** It's built as a full
  `ModelViewSet`, but `APIs/urls.py` only routes those two actions to
  `/pharmacies/`. There's no way to retrieve, update, or delete a single pharmacy by
  ID through the API as it stands — out of scope for the thesis, but worth knowing
  if the API is extended later.

- **A small casing mismatch.** `INSTALLED_APPS` registers the app as `'APIs'`
  (mixed case), while the thesis ER diagram shows lowercase table names
  (`apis_pharmacy`). PostgreSQL folds unquoted identifiers to lowercase by default,
  so this is unlikely to have any practical effect, but the actual table names in a
  live database haven't been checked directly.

- **The pharmacist request/approval workflow in the class diagram wasn't built.**
  The original design had pharmacists requesting to register their pharmacy and
  admins approving it (see [User roles](#user-roles)). The implementation simplified
  this to direct registration by the administrator.

---

## Future work

The thesis identifies a mobile application for iOS and Android as the primary intended
next step, noting the potential to use device GPS for automatic location detection and
push notifications to alert users when a nearby pharmacy is open.

---

## References

1. Django documentation — https://docs.djangoproject.com/en/5.0/
2. GeoDjango — https://docs.djangoproject.com/en/5.0/ref/contrib/gis/
3. Django REST Framework — https://www.django-rest-framework.org/
4. django-rest-framework-gis — https://github.com/openwisp/django-rest-framework-gis
5. dj-rest-auth — https://dj-rest-auth.readthedocs.io/en/latest/
6. PostgreSQL — https://www.postgresql.org/
7. PostGIS — https://postgis.net/
8. Leaflet — https://leafletjs.com/
