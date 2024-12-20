
# Library Management System

This project is a Library Management System built with Django REST Framework, featuring a Books Service, Users Service, and Borrowing & Payment functionality. The project uses JWT authentication, Stripe API for payments, and Celery for scheduled tasks such as overdue borrowing notifications.

<!-- TOC -->
* [Library API](#library-management-system)
  * [Features](#features)
  * [Prerequisites](#prerequisites)
  * [Manual project start](#manual-starting)
    * [Dependencies installation](#install-dependencies)
    * [Environment configuration](#configure-environment-variables)
    * [Server running](#run-the-server)
  * [Docker](#docker-starting)
    * [Start Servio (Stripe)](#servio-start-for-stripe-payment)
    * [Docker starting](#docker-run)
  * [Usage](#usage)
  * [Stripe Integration](#stripe-integration)
  * [Scheduled Tasks](#scheduled-tasks)
  * [Documentations](#documentations)
<!-- TOC -->

## Features

1. **Books Service**
   - CRUD operations for managing books.
   - Admin users can create, update, and delete books.
   - All users (authenticated or not) can view the list of available books.
   - Inventory tracking for books, including automatic decrements when borrowed.

2. **Users Service**
   - JWT-based authentication for user management.
   - Admin users can manage all user data.
   - Users can register, log in, and manage their profiles.

3. **Borrowing Service**
   - Users can borrow books if available.
   - Books will have an inventory check to ensure availability.
   - Only authenticated users can borrow books.
   - Admins can view all borrowings; non-admins can only see their own.
   - Borrowings include tracking for borrow date, expected return date, and actual return date.

4. **Payment Service**
   - Stripe integration for handling payments.
   - Users are required to pay a fee when borrowing books.
   - If books are returned late, a fine is calculated and applied automatically.
   - Admins can see all payments, and users can only see their own.

5. **Notifications**
   - Integration with Telegram for notifications on new borrowings and overdue alerts.
   - Scheduled tasks to notify admins of overdue borrowings.

---

## Prerequisites

- Python 3.x
- Django 4.x
- Stripe account (test mode)
- Telegram account and bot for notifications
- Redis (for Celery task queue)

### Clone the Repository

```bash
git clone https://github.com/MasakDirt/library-api.git
cd library-api
```


## Manual Starting
### Install Dependencies

It's recommended to use a virtual environment to manage dependencies:

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

You need to have before starting:
1) Stripe account;
2) Telegram Bot and Chat;
3) Installed Redis and PostgresSQL databases;

### Configure Environment Variables

Create a `.env` file in the project root and add your environment-specific variables. Here's an example:

```bash
# .env

# Django
DJANGO_SECRET_KEY=<YOUR_SECRET_KEY>
ALLOWED_HOSTS=<YOUR_ALLOWED_HOSTS>
DEBUG=False

# Telegram
TELEGRAM_TOKEN=<YOUR_TOKEN>
CHAT_ID=<YOUR_CHAT_ID>
TELEGRAM_BOT_HOST=<YOUR_BOT_HOST>
TELEGRAM_BOT_PORT=<8002>

# Stripe
STRIPE_SECRET_KEY=<YOUR_STRIPE_SECRET_KEY>
STRIPE_PUBLISHABLE_KEY=<YOUR_STRIPE_PUBLISHABLE_KEY>
ENDPOINT_SECRET_WEBHOOK=<YOUR_SECRET_WEEBHOOK>

# Tests
DJANGO_SETTINGS_MODULE=library_api.settings  # include this only for running tests

# Postgres
POSTGRES_PASSWORD=<YOUR_SECRET_PASSWORD>
POSTGRES_USER=<YOUR_USER>
POSTGRES_DB=<YOUR_DB>
POSTGRES_HOST=<YOUR_HOST>
POSTGRES_PORT=5432
PGDATA=<YOUR_PGDATA>

# Redis
REDIS_HOST=<redis>
REDIS_PORT=<6379>

# Production value
IS_PRODUCTION=<False>
```

### Apply Migrations

```bash
python manage.py migrate
```

### Create Superuser (Admin)

```bash
python manage.py createsuperuser
```

### Run the Server

```bash
python manage.py runserver
```

### Run the Serveo for Stripe payments

```bash
ssh -R 80:localhost:8000 serveo.net
```

### Run Telegram Fast Api

```bash
uvicorn telegram_bot.notify:app --host 0.0.0.0 --port 8001 --reload
```


### Run Celery Worker

```bash
celery -A library_api worker --loglevel=INFO
```


### Run Celery Beat

```bash
# also create scheduled task in database
celery -A library_api beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler
```


## Docker Starting

### Set environment variables
[Env setting guide](#configure-environment-variables)

### Servio start for Stripe payment

```bash
ssh -R 80:localhost:8001 serveo.net
```

Add link that you received into Stripe -> Webhook -> `Endpoint URL`

### Docker run
```bash
docker-compose up --build
```

---

## Usage

### API Documentation

For convenient use of the API, interactive documentation is available:
- **Swagger UI** – for viewing and testing the API:
  - `GET api/v1/schema/swagger-ui/`

- **ReDoc** – alternative documentation for the API:
  - `GET api/v1/schema/redoc/`

### Books Service

1. **List Books** (Open to everyone, even unauthenticated users):
   - `GET /api/v1/books/`

2. **Create Book** (Admin only):
   - `POST /api/v1/books/`

3. **Retrieve, Update, or Delete Book** (Admin only):
   - `GET /api/v1/books/<id>/`
   - `PUT /api/v1/books/<id>/`
   - `DELETE /api/v1/books/<id>/`

### Users Service

1. **Register User**:
   - `POST /api/v1/user/register/`

2. **Login (JWT Token)**:
   - `POST /api/v1/user/token/`

3. **Refresh Token**:
   - `POST /api/v1/user/token/refresh/`

4. **Verify Token**:
   - `POST /api/v1/user/token/verify/`

5. **Get User Profile** (Authenticated Users Only):
   - `GET /api/v1/user/me/`

### Borrowing Service

1. **List Borrowings**:
   - Non-admin users: View their own borrowings.
   - Admin users: View all borrowings or filter by `user_id`.
   - `GET /api/v1/borrowings/`

2. **Borrow a Book** (Authenticated users only):
   - `POST /api/v1/borrowings/`
   - Automatically decreases book inventory and generates a Stripe payment session.

3. **Return a Book**:
   - `POST /api/v1/borrowings/<id>/return/`
   - Inventory is updated, and overdue fines are applied if applicable.

### Payments Service

1. **List Payments**:
   - Admins can see all payments, non-admin users can see only their own payments.
   - `GET /api/v1/payments/`

---

## Stripe Integration

1. You can work with the Stripe API in test mode by using the provided `STRIPE_SECRET_KEY` and `STRIPE_PUBLIC_KEY`.
2. The `Payment` model will track each payment with a `session_url` and `session_id` from Stripe.

### Stripe Payment Workflow

- On borrowing a book, a payment session is created.
- If the borrowing is overdue, a fine will be calculated and added to the payment amount.

---

## Scheduled Tasks

- A scheduled task runs daily to check for overdue borrowings using Celery.
- If any borrowings are overdue, a message will be sent to the Telegram bot.

---

### Documentations

- [Django Rest Framework](https://www.django-rest-framework.org/)
- [Redis](https://redis.io/docs/latest/)
- [Stripe](https://stripe.com/docs)
- [Celery](https://docs.celeryq.dev/en/stable/)
- [Telegram Bot API](https://core.telegram.org/bots/api)
