# FirmaFinder CRM - PRD

## Problem Statement
Build a CRM that finds leads from Romanian business directories (mfinante.gov.ro) for the printing industry. Users search by 9 specific CAEN codes, filter by county and establishment date ("data infiintari" / "Stare societate"), save companies to a pipeline, set reminders, and receive email/SMS notifications. Auth with email, phone number, and password.

## Architecture
- **Frontend**: React + Tailwind + Shadcn UI (port 3000)
- **Backend**: FastAPI (port 8001, /api prefix)
- **Database**: MongoDB (test_database)
- **Auth**: JWT (email + phone + password)
- **AI**: OpenAI GPT-5.2 via Emergent LLM Key
- **Data Sources**:
  - mfinante.gov.ro — company search by CAEN keywords and name
  - ANAF API (webservicesp.anaf.ro) — establishment dates, phone, J number, address
- **Email**: SendGrid (requires verified sender configuration)

## CAEN Codes (Printing, Publishing, Textiles, Advertising)
1811, 1812, 1813, 1814, 5811, 5812, 5813, 5814, 5819, 7311, 7312, 1330, 1392, 1395, 1396, 1399 (16 codes)

## What's Been Implemented
- [x] LIVE company search from mfinante.gov.ro (keyword matching per CAEN code)
- [x] Search by company name + county (42 Romanian counties)
- [x] 9 printing-specific CAEN codes with industry keywords
- [x] **ANAF API enrichment** — auto-fetches establishment date (data_inregistrare), phone, J number, address for all search results
- [x] **Establishment date filtering** — since_date parameter filters companies by registration date (>= comparison)
- [x] Company CRUD with pipeline categories (potential lead, prospect, client, rejected)
- [x] Company detail page with CUI, J, CAEN, address, county, establishment date
- [x] Reminder system with calendar + time picker
- [x] Background reminder checker (auto-creates overdue notifications)
- [x] AI message composition (GPT-5.2) for client outreach
- [x] JWT authentication with email + phone + password
- [x] Separate email, phone, password fields on registration form
- [x] Login by email OR phone number
- [x] Language toggle (EN/RO) with full translations
- [x] Dashboard with pipeline stats
- [x] Kanban pipeline view
- [x] Mobile responsive design
- [x] SendGrid integration (configured but requires verified sender)
- [x] Multi-county search endpoint
- [x] Test email endpoint for SendGrid validation

## How Establishment Date Works
1. User searches by CAEN code (e.g., 1812) in a county
2. Backend scrapes mfinante.gov.ro for matching companies (returns CUIs)
3. Backend batch-calls ANAF API (POST webservicesp.anaf.ro/api/PlatitorTvaRest/v9/tva) with CUIs
4. ANAF returns `data_inregistrare` (ISO date) and `stare_inregistrare` ("INREGISTRAT din data DD.MM.YYYY")
5. If user set a since_date filter, only companies with data_inregistrare >= since_date are returned
6. Results table shows establishment date column + enriched phone numbers

## Prioritized Backlog

### P0 (Immediate - User Requested)
- SendGrid sender verification: User needs to verify a sender email in SendGrid and set SENDGRID_FROM_EMAIL in backend/.env
- SMS notification integration (Twilio) for reminders
- AI agent autonomous email/SMS composition for missed reminders

### P1 (Next)
- CSV export of lead lists

### P2 (Future)
- Bulk import companies from CSV
- WhatsApp integration
- Revenue forecasting dashboard
- Team collaboration features

## Key API Endpoints
- POST /api/auth/register (email required, phone optional, password)
- POST /api/auth/login (identifier: email or phone, password)
- GET /api/auth/me
- GET /api/caen-codes (9 codes)
- GET /api/counties (42 counties)
- GET /api/search/caen/{code}?county=XX&since_date=YYYY-MM-DD
- GET /api/search?q=NAME&county=XX&since_date=YYYY-MM-DD
- GET /api/search/multi-county?q=CODE&type=caen&since_date=YYYY-MM-DD
- CRUD: /api/companies, /api/reminders
- GET /api/dashboard/stats
- POST /api/ai/compose-message
- POST /api/notifications/test-email

## DB Schema
- users: {user_id, email, phone, password_hash, name, language, created_at}
- companies: {id, user_id, company_name, cui, j_number, caen_code, caen_description, email, phone, contact_person, address, county, establishment_date, website, status, notes, source_url, created_at, updated_at}
- reminders: {id, user_id, company_id, company_name, reminder_type, due_date, message, is_completed, is_overdue, ai_action_taken, email_sent, created_at}
- notifications: {id, user_id, title, message, type, is_read, related_company_id, related_reminder_id, created_at}
