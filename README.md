
# Library Management System

This project is a Library Management System built with Django REST Framework, featuring a Books Service, Users Service, and Borrowing & Payment functionality. The project uses JWT authentication, Stripe API for payments, and Celery for scheduled tasks such as overdue borrowing notifications.

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

## Installation

### Prerequisites

- Python 3.x
- Django 5.x
- PostgreSQL (or any other database supported by Django)
- Stripe account (test mode)
- Telegram account and bot for notifications
- Redis (for Celery task queue)

### Clone the Repository

```bash
git clone https://github.com/MasakDirt/library-api.git
cd library-api
```

### Install Dependencies

It's recommended to use a virtual environment to manage dependencies:

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Configure Environment Variables

Create a `.env` file in the project root and add your environment-specific variables. Here's an example:

```bash
# .env
SECRET_KEY=your_secret_key
DEBUG=True

# JWT
JWT_SECRET_KEY=your_jwt_secret_key

# Stripe
STRIPE_SECRET_KEY=your_stripe_secret_key
STRIPE_PUBLIC_KEY=your_stripe_public_key

# Telegram
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_CHAT_ID=your_telegram_chat_id
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

---

## Usage

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

## Notifications & Celery Setup

### Telegram Notifications

1. Set up a Telegram bot and get the `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` for the bot.
2. The bot will send messages for:
   - New borrowings created.
   - Overdue borrowings (checked daily).
3. Run Telegram Fast Api:
   ```bash
   uvicorn telegram_bot.notify:app --host 0.0.0.0 --port 8001 --reload
   ```

### Celery Setup

1. Install and configure Redis as the message broker for Celery.
2. Run Celery workers:
   ```bash
   celery -A library_api worker -l INFO
   ```

3. To start the scheduler:
   ```bash
   celery -A proj beat -l INFO --scheduler django_celery_beat.schedulers:DatabaseScheduler
   ```

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

