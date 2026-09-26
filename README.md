# EVE Healthcare Diagnostic Booking Backend

A small FastAPI + PostgreSQL backend for diagnostic test bookings and simulated payments.

## Features
- User signup/login with JWT authentication
- Diagnostic centres and tests
- Authenticated bookings
- Mock payment processing
- Idempotent payment webhook using unique provider event IDs
- Authorization checks
- Request validation and useful error responses
- Pagination for centres/tests
- Swagger/OpenAPI docs
- Pytest tests

## Stack
FastAPI, SQLAlchemy 2, PostgreSQL, Pydantic, JWT, Passlib/bcrypt, Pytest. SQLite is supported for tests.

## Run locally
1. Copy `.env.example` to `.env` and update values if needed.
2. Start PostgreSQL and create database `eve_healthcare`.
3. Install dependencies:
```bash
pip install -r requirements.txt
```
4. Run:
```bash
uvicorn app.main:app --reload
```
5. Open `/docs` for Swagger UI.

### Docker
```bash
docker compose up --build
```

## API endpoints
- `POST /auth/signup/`
- `POST /auth/login/`
- `GET /centres/`
- `POST /centres/` (authenticated)
- `GET /centres/{centre_id}`
- `POST /tests/` (authenticated)
- `GET /tests/`
- `POST /bookings/` (authenticated)
- `GET /bookings/` (authenticated, own bookings)
- `GET /bookings/{booking_id}` (authenticated, owner only)
- `POST /payments/` (authenticated, booking owner)
- `POST /payments/webhook/`

## Example
Signup:
```json
POST /auth/signup/
{"email":"priya@example.com","password":"Password123"}
```
Login returns a bearer JWT. Add it in Swagger Authorize as `Bearer <token>`.

Create a centre:
```json
{"name":"City Diagnostics","location":"Greater Noida"}
```
Create a test:
```json
{"name":"CBC","price":650,"centre_id":1}
```
Book:
```json
{"test_id":1,"centre_id":1,"appointment_at":"2026-10-05T10:00:00+05:30"}
```
Mock payment:
```json
{"booking_id":1,"force_status":"SUCCESS","provider_payment_id":"mock-pay-1"}
```
Webhook:
```json
{"event_id":"evt-1","payment_id":"mock-pay-1","booking_id":1,"status":"SUCCESS"}
```
Sending the same `event_id` again returns the existing payment and does not create a second payment.

## Schema design
- `users`: credentials and identity
- `diagnostic_centres`: centre details
- `diagnostic_tests`: test and price, linked to centre
- `bookings`: user + test + centre + appointment + amount + status
- `payments`: one payment record per booking and provider event IDs are unique

The booking stores the price at booking time so later test-price changes do not alter historical bookings. A booking can only be created for a test belonging to the selected centre.

## Important assumptions
- One diagnostic test belongs to one centre.
- Payment is simulated and has no real money movement.
- Booking starts as `PENDING`; successful payment changes it to `CONFIRMED`, failed payment changes it to `FAILED`.
- Cancellation is not exposed as a separate endpoint because the assignment focuses on booking/payment flow; the status model supports it.
- Webhook processing is idempotent through unique provider event IDs and transactional updates.

## If I had more time
Add Alembic migrations, Redis caching, Celery for asynchronous webhook processing, stronger webhook signatures, rate limiting, structured JSON logging, richer test coverage, appointment-slot locking, and production secret management.
