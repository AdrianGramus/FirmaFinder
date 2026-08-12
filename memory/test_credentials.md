# Test Credentials

## Auth Method
Email/Phone + Password (JWT-based)

## Admin Account (seeded on startup)
- Email: admin@firmafinder.com
- Password: Admin123!

## Test User Account
- Email: newtest@example.com
- Phone: +40721999888
- Password: Test123!

## Login
Use email OR phone number as the identifier field.

## Registration
POST /api/auth/register with:
- email (required)
- phone (optional)
- password (min 6 chars)
- name (optional)
