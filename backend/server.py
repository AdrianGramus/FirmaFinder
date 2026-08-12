from fastapi import FastAPI, APIRouter, HTTPException, Request, Response
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
import uuid
import asyncio
import bcrypt
import jwt
from pathlib import Path
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timezone, timedelta
from fastapi.middleware.cors import CORSMiddleware

from scraper import (
    search_mfinante_by_name,
    search_by_caen_code,
    fetch_company_detail,
    get_counties,
    get_caen_codes,
    enrich_companies_with_anaf,
)

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]
JWT_SECRET = os.environ.get('JWT_SECRET', 'fallback-secret-change-me')

app = FastAPI()
api_router = APIRouter(prefix="/api")

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


# ===== Pydantic Models =====
class RegisterBody(BaseModel):
    email: str
    phone: str = ""
    password: str
    name: str = ""

class LoginBody(BaseModel):
    identifier: str  # email or phone
    password: str

class CompanyCreate(BaseModel):
    company_name: str
    cui: str = ""
    j_number: str = ""
    caen_code: str = ""
    caen_description: str = ""
    email: str = ""
    phone: str = ""
    contact_person: str = ""
    address: str = ""
    county: str = ""
    establishment_date: str = ""
    website: str = ""
    status: str = "potential_lead"
    notes: str = ""
    source_url: str = ""

class CompanyUpdate(BaseModel):
    company_name: Optional[str] = None
    cui: Optional[str] = None
    j_number: Optional[str] = None
    caen_code: Optional[str] = None
    caen_description: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    contact_person: Optional[str] = None
    address: Optional[str] = None
    county: Optional[str] = None
    establishment_date: Optional[str] = None
    website: Optional[str] = None
    status: Optional[str] = None
    notes: Optional[str] = None
    source_url: Optional[str] = None

class ReminderCreate(BaseModel):
    company_id: str
    company_name: str
    reminder_type: str = "call"
    due_date: str
    message: str = ""

class ReminderUpdate(BaseModel):
    reminder_type: Optional[str] = None
    due_date: Optional[str] = None
    message: Optional[str] = None
    is_completed: Optional[bool] = None

class ComposeMessageRequest(BaseModel):
    company_name: str
    contact_person: str = ""
    email: str = ""
    context: str = ""
    language: str = "en"

class LanguageUpdate(BaseModel):
    language: str


# ===== JWT Auth Helpers =====
def create_token(user_id: str) -> str:
    payload = {
        "user_id": user_id,
        "exp": datetime.now(timezone.utc) + timedelta(days=7),
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))


async def get_current_user(request: Request) -> dict:
    token = None
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header[7:]
    if not token:
        token = request.cookies.get("session_token")
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        user_id = payload.get("user_id")
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
    user_doc = await db.users.find_one({"user_id": user_id}, {"_id": 0})
    if not user_doc:
        raise HTTPException(status_code=401, detail="User not found")
    return user_doc


# ===== Auth Routes =====
@api_router.post("/auth/register")
async def register(body: RegisterBody, response: Response):
    email = body.email.strip().lower()
    phone = body.phone.strip()
    if not email:
        raise HTTPException(status_code=400, detail="Email is required")
    if len(body.password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")
    existing = await db.users.find_one({"email": email})
    if existing:
        raise HTTPException(status_code=409, detail="Account already exists with this email")
    user_id = f"user_{uuid.uuid4().hex[:12]}"
    now_str = datetime.now(timezone.utc).isoformat()
    user_doc = {
        "user_id": user_id,
        "email": email,
        "phone": phone,
        "password_hash": hash_password(body.password),
        "name": body.name.strip() or email.split("@")[0],
        "language": "en",
        "created_at": now_str,
    }
    await db.users.insert_one(user_doc)
    token = create_token(user_id)
    response.set_cookie(
        key="session_token", value=token, httponly=True,
        secure=True, samesite="none", path="/", max_age=7 * 24 * 3600,
    )
    return {
        "user_id": user_id,
        "email": user_doc["email"],
        "phone": user_doc["phone"],
        "name": user_doc["name"],
        "language": user_doc["language"],
        "token": token,
    }


@api_router.post("/auth/login")
async def login(body: LoginBody, response: Response):
    identifier = body.identifier.strip().lower()
    user = await db.users.find_one(
        {"$or": [{"email": identifier}, {"phone": identifier}]},
        {"_id": 0}
    )
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if not verify_password(body.password, user.get("password_hash", "")):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_token(user["user_id"])
    response.set_cookie(
        key="session_token", value=token, httponly=True,
        secure=True, samesite="none", path="/", max_age=7 * 24 * 3600,
    )
    return {
        "user_id": user["user_id"],
        "email": user.get("email", ""),
        "phone": user.get("phone", ""),
        "name": user.get("name", ""),
        "language": user.get("language", "en"),
        "token": token,
    }


@api_router.get("/auth/me")
async def auth_me(request: Request):
    user = await get_current_user(request)
    return {k: v for k, v in user.items() if k != "password_hash"}


@api_router.post("/auth/logout")
async def auth_logout(response: Response):
    response.delete_cookie(key="session_token", path="/", secure=True, samesite="none")
    return {"status": "ok"}


# ===== Search Routes =====
@api_router.get("/search")
async def search_companies(q: str = "", county: str = "40", type: str = "name", since_date: str = ""):
    if not q:
        raise HTTPException(status_code=400, detail="Query required")
    results = await asyncio.get_event_loop().run_in_executor(
        None, search_mfinante_by_name, q, county
    )
    # Enrich with ANAF data (establishment dates, phone, etc.)
    results = await asyncio.get_event_loop().run_in_executor(
        None, enrich_companies_with_anaf, results
    )
    # Filter by establishment date if provided
    if since_date:
        results = [c for c in results if c.get("establishment_date", "") >= since_date]
    return {"companies": results, "total": len(results), "query": q, "county": county, "source": "mfinante.gov.ro", "since_date": since_date}


@api_router.get("/search/caen/{code}")
async def search_by_caen(code: str, county: str = "40", since_date: str = ""):
    # Support multiple CAEN codes separated by commas
    codes = [c.strip() for c in code.split(",") if c.strip()]
    all_results = []
    seen_cuis = set()
    for single_code in codes:
        results = await asyncio.get_event_loop().run_in_executor(
            None, search_by_caen_code, single_code, county
        )
        for c in results:
            if c["cui"] not in seen_cuis:
                seen_cuis.add(c["cui"])
                all_results.append(c)
    # Enrich with ANAF data (establishment dates, phone, etc.)
    all_results = await asyncio.get_event_loop().run_in_executor(
        None, enrich_companies_with_anaf, all_results
    )
    # Filter by establishment date if provided
    if since_date:
        all_results = [c for c in all_results if c.get("establishment_date", "") >= since_date]
    caen_codes_list = get_caen_codes()
    descriptions = [next((c["description_ro"] for c in caen_codes_list if c["code"] == cd), "") for cd in codes]
    return {
        "companies": all_results,
        "total": len(all_results),
        "caen_code": code,
        "caen_description": ", ".join(filter(None, descriptions)),
        "county": county,
        "source": "mfinante.gov.ro",
        "since_date": since_date,
    }


@api_router.get("/search/multi-county")
async def search_multi_county(q: str = "", type: str = "caen", since_date: str = ""):
    """Search by CAEN code across all counties."""
    if not q:
        raise HTTPException(status_code=400, detail="Query required")
    if type == "caen":
        all_results = []
        seen_cuis = set()
        county_list = list(COUNTY_CODES.keys())[:10]  # Top 10 counties to avoid timeout
        for county_code in county_list:
            try:
                results = await asyncio.get_event_loop().run_in_executor(
                    None, search_by_caen_code, q, county_code
                )
                for c in results:
                    if c["cui"] not in seen_cuis:
                        seen_cuis.add(c["cui"])
                        all_results.append(c)
            except Exception:
                continue
        all_results = await asyncio.get_event_loop().run_in_executor(
            None, enrich_companies_with_anaf, all_results
        )
        if since_date:
            all_results = [c for c in all_results if c.get("establishment_date", "") >= since_date]
        return {"companies": all_results, "total": len(all_results), "query": q, "source": "mfinante.gov.ro", "since_date": since_date}
    else:
        results = await asyncio.get_event_loop().run_in_executor(
            None, search_mfinante_by_name, q, "40"
        )
        results = await asyncio.get_event_loop().run_in_executor(
            None, enrich_companies_with_anaf, results
        )
        if since_date:
            results = [c for c in results if c.get("establishment_date", "") >= since_date]
        return {"companies": results, "total": len(results), "query": q, "source": "mfinante.gov.ro", "since_date": since_date}


# ===== County codes for multi-county search =====
from scraper import COUNTY_CODES


@api_router.get("/counties")
async def list_counties():
    return get_counties()


@api_router.get("/caen-codes")
async def list_caen_codes():
    return get_caen_codes()


# ===== Company CRUD =====
@api_router.get("/companies")
async def get_companies(request: Request, status: Optional[str] = None, since_date: Optional[str] = None):
    user = await get_current_user(request)
    query = {"user_id": user["user_id"]}
    if status:
        query["status"] = status
    if since_date:
        query["establishment_date"] = {"$gte": since_date}
    companies = await db.companies.find(query, {"_id": 0}).sort("updated_at", -1).to_list(500)
    return companies


@api_router.post("/companies")
async def create_company(request: Request, body: CompanyCreate):
    user = await get_current_user(request)
    now = datetime.now(timezone.utc).isoformat()
    doc = {
        "id": str(uuid.uuid4()),
        "user_id": user["user_id"],
        **body.model_dump(),
        "created_at": now,
        "updated_at": now,
    }
    await db.companies.insert_one(doc)
    return await db.companies.find_one({"id": doc["id"]}, {"_id": 0})


@api_router.get("/companies/{company_id}")
async def get_company(request: Request, company_id: str):
    user = await get_current_user(request)
    company = await db.companies.find_one({"id": company_id, "user_id": user["user_id"]}, {"_id": 0})
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    return company


@api_router.put("/companies/{company_id}")
async def update_company(request: Request, company_id: str, body: CompanyUpdate):
    user = await get_current_user(request)
    updates = {k: v for k, v in body.model_dump().items() if v is not None}
    updates["updated_at"] = datetime.now(timezone.utc).isoformat()
    result = await db.companies.update_one({"id": company_id, "user_id": user["user_id"]}, {"$set": updates})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Company not found")
    return await db.companies.find_one({"id": company_id}, {"_id": 0})


@api_router.delete("/companies/{company_id}")
async def delete_company(request: Request, company_id: str):
    user = await get_current_user(request)
    result = await db.companies.delete_one({"id": company_id, "user_id": user["user_id"]})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Company not found")
    await db.reminders.delete_many({"company_id": company_id, "user_id": user["user_id"]})
    return {"status": "deleted"}


# ===== Reminder CRUD =====
@api_router.get("/reminders")
async def get_reminders(request: Request, upcoming: Optional[bool] = None):
    user = await get_current_user(request)
    query = {"user_id": user["user_id"]}
    if upcoming:
        query["is_completed"] = False
    reminders = await db.reminders.find(query, {"_id": 0}).sort("due_date", 1).to_list(500)
    now = datetime.now(timezone.utc).isoformat()
    for r in reminders:
        if not r.get("is_completed") and r.get("due_date", "") < now:
            r["is_overdue"] = True
    return reminders


@api_router.post("/reminders")
async def create_reminder(request: Request, body: ReminderCreate):
    user = await get_current_user(request)
    now = datetime.now(timezone.utc).isoformat()
    doc = {
        "id": str(uuid.uuid4()),
        "user_id": user["user_id"],
        **body.model_dump(),
        "is_completed": False,
        "is_overdue": False,
        "ai_action_taken": False,
        "email_sent": False,
        "created_at": now,
    }
    await db.reminders.insert_one(doc)
    return await db.reminders.find_one({"id": doc["id"]}, {"_id": 0})


@api_router.put("/reminders/{reminder_id}")
async def update_reminder(request: Request, reminder_id: str, body: ReminderUpdate):
    user = await get_current_user(request)
    updates = {k: v for k, v in body.model_dump().items() if v is not None}
    result = await db.reminders.update_one({"id": reminder_id, "user_id": user["user_id"]}, {"$set": updates})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Reminder not found")
    return await db.reminders.find_one({"id": reminder_id}, {"_id": 0})


@api_router.delete("/reminders/{reminder_id}")
async def delete_reminder(request: Request, reminder_id: str):
    user = await get_current_user(request)
    result = await db.reminders.delete_one({"id": reminder_id, "user_id": user["user_id"]})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Reminder not found")
    return {"status": "deleted"}


@api_router.post("/reminders/{reminder_id}/complete")
async def complete_reminder(request: Request, reminder_id: str):
    user = await get_current_user(request)
    result = await db.reminders.update_one(
        {"id": reminder_id, "user_id": user["user_id"]},
        {"$set": {"is_completed": True}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Reminder not found")
    return await db.reminders.find_one({"id": reminder_id}, {"_id": 0})


# ===== Notifications (Email via SendGrid) =====
_sendgrid_last_error_time = None

def send_email_notification(to_email: str, subject: str, body_text: str):
    global _sendgrid_last_error_time
    api_key = os.environ.get("SENDGRID_API_KEY")
    from_email = os.environ.get("SENDGRID_FROM_EMAIL", "")
    if not api_key or not to_email or not from_email:
        if not from_email:
            # Only log once per 10 min to avoid spam
            now = datetime.now(timezone.utc)
            if _sendgrid_last_error_time is None or (now - _sendgrid_last_error_time).total_seconds() > 600:
                logger.warning("SendGrid FROM email not configured. Set SENDGRID_FROM_EMAIL in .env to a verified sender.")
                _sendgrid_last_error_time = now
        return False
    try:
        from sendgrid import SendGridAPIClient
        from sendgrid.helpers.mail import Mail
        message = Mail(
            from_email=from_email,
            to_emails=to_email,
            subject=subject,
            html_content=f"<div style='font-family:sans-serif;padding:20px'>{body_text}</div>",
        )
        sg = SendGridAPIClient(api_key)
        response = sg.send(message)
        logger.info(f"Email sent to {to_email}, status: {response.status_code}")
        return response.status_code in (200, 201, 202)
    except Exception as e:
        now = datetime.now(timezone.utc)
        if _sendgrid_last_error_time is None or (now - _sendgrid_last_error_time).total_seconds() > 600:
            logger.error(f"SendGrid error: {e}")
            if hasattr(e, 'body'):
                logger.error(f"SendGrid body: {e.body}")
            _sendgrid_last_error_time = now
        return False


@api_router.get("/notifications")
async def get_notifications(request: Request, unread: Optional[bool] = None):
    user = await get_current_user(request)
    query = {"user_id": user["user_id"]}
    if unread:
        query["is_read"] = False
    return await db.notifications.find(query, {"_id": 0}).sort("created_at", -1).to_list(100)


@api_router.put("/notifications/{notification_id}/read")
async def mark_notification_read(request: Request, notification_id: str):
    user = await get_current_user(request)
    await db.notifications.update_one({"id": notification_id, "user_id": user["user_id"]}, {"$set": {"is_read": True}})
    return {"status": "ok"}


@api_router.put("/notifications/read-all")
async def mark_all_notifications_read(request: Request):
    user = await get_current_user(request)
    await db.notifications.update_many({"user_id": user["user_id"], "is_read": False}, {"$set": {"is_read": True}})
    return {"status": "ok"}


@api_router.post("/notifications/test-email")
async def test_email(request: Request):
    """Test SendGrid email configuration."""
    user = await get_current_user(request)
    user_email = user.get("email", "")
    if not user_email:
        raise HTTPException(status_code=400, detail="Your account has no email address")
    from_email = os.environ.get("SENDGRID_FROM_EMAIL", "")
    if not from_email:
        raise HTTPException(status_code=400, detail="SENDGRID_FROM_EMAIL not configured on server. Ask admin to set a verified sender email.")
    sent = send_email_notification(
        user_email,
        "[FirmaFinder] Test Email",
        "<h2>Test Email</h2><p>If you received this, SendGrid is configured correctly.</p>"
    )
    if sent:
        return {"status": "sent", "to": user_email}
    raise HTTPException(status_code=500, detail="Failed to send email. Check SendGrid configuration and sender verification.")


# ===== AI Compose Message =====
@api_router.post("/ai/compose-message")
async def compose_message(request: Request, body: ComposeMessageRequest):
    await get_current_user(request)
    llm_key = os.environ.get("EMERGENT_LLM_KEY")
    if not llm_key:
        raise HTTPException(status_code=500, detail="AI not configured")
    try:
        from emergentintegrations.llm.chat import LlmChat, UserMessage
        lang = "in Romanian" if body.language == "ro" else "in English"
        prompt = f"""Compose a professional business outreach message {lang} for:
Company: {body.company_name}
Contact: {body.contact_person or 'Unknown'}
Context: {body.context or 'Initial business outreach'}
Keep it brief, professional, with greeting and call to action."""
        chat = LlmChat(
            api_key=llm_key,
            session_id=f"compose_{uuid.uuid4().hex[:8]}",
            system_message="You are a professional business communication assistant."
        ).with_model("openai", "gpt-5.2")
        response_text = await chat.send_message(UserMessage(text=prompt))
        return {"message": response_text, "company_name": body.company_name}
    except Exception as e:
        logger.error(f"AI error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ===== Dashboard =====
@api_router.get("/dashboard/stats")
async def get_dashboard_stats(request: Request):
    user = await get_current_user(request)
    uid = user["user_id"]
    total = await db.companies.count_documents({"user_id": uid})
    potential = await db.companies.count_documents({"user_id": uid, "status": "potential_lead"})
    prospects = await db.companies.count_documents({"user_id": uid, "status": "prospect"})
    clients = await db.companies.count_documents({"user_id": uid, "status": "client"})
    rejected = await db.companies.count_documents({"user_id": uid, "status": "rejected"})
    now = datetime.now(timezone.utc).isoformat()
    upcoming = await db.reminders.find({"user_id": uid, "is_completed": False}, {"_id": 0}).sort("due_date", 1).to_list(10)
    overdue_count = 0
    for r in upcoming:
        if r.get("due_date", "") < now:
            r["is_overdue"] = True
            overdue_count += 1
    unread = await db.notifications.count_documents({"user_id": uid, "is_read": False})
    recent = await db.companies.find({"user_id": uid}, {"_id": 0}).sort("created_at", -1).to_list(5)
    return {
        "total_companies": total, "potential_leads": potential, "prospects": prospects,
        "clients": clients, "rejected": rejected, "upcoming_reminders": upcoming,
        "overdue_reminders": overdue_count, "unread_notifications": unread, "recent_companies": recent,
    }


# ===== User Settings =====
@api_router.put("/user/language")
async def update_language(request: Request, body: LanguageUpdate):
    user = await get_current_user(request)
    await db.users.update_one({"user_id": user["user_id"]}, {"$set": {"language": body.language}})
    return {"status": "ok", "language": body.language}


# ===== Background: Check overdue reminders & send email =====
async def check_overdue_reminders():
    while True:
        try:
            await asyncio.sleep(60)
            now = datetime.now(timezone.utc).isoformat()
            overdue = await db.reminders.find(
                {"is_completed": False, "email_sent": {"$ne": True}, "due_date": {"$lt": now}},
                {"_id": 0}
            ).to_list(50)
            for reminder in overdue:
                user = await db.users.find_one({"user_id": reminder["user_id"]}, {"_id": 0})
                if not user:
                    continue
                user_email = user.get("email", "")
                company = await db.companies.find_one({"id": reminder.get("company_id")}, {"_id": 0})
                company_name = reminder.get("company_name", "Unknown")
                r_type = reminder.get("reminder_type", "task")
                r_msg = reminder.get("message", "")

                # Send email notification to the user
                if user_email:
                    subject = f"[FirmaFinder] Overdue {r_type}: {company_name}"
                    body_html = f"""
                    <h2>Reminder Overdue</h2>
                    <p>Your <strong>{r_type}</strong> for <strong>{company_name}</strong> is overdue.</p>
                    <p>Notes: {r_msg}</p>
                    <p>Please take action as soon as possible.</p>
                    <hr/>
                    <p style='color:#888;font-size:12px'>FirmaFinder CRM</p>
                    """
                    sent = send_email_notification(user_email, subject, body_html)
                    if sent:
                        await db.reminders.update_one({"id": reminder["id"]}, {"$set": {"email_sent": True}})
                        await db.notifications.insert_one({
                            "id": str(uuid.uuid4()), "user_id": reminder["user_id"],
                            "title": f"Email sent: {r_type} - {company_name}",
                            "message": f"Overdue notification email sent to {user_email}",
                            "type": "email_sent", "is_read": False,
                            "related_company_id": reminder.get("company_id", ""),
                            "related_reminder_id": reminder["id"],
                            "created_at": datetime.now(timezone.utc).isoformat(),
                        })

                # Also try AI auto-compose
                if company and company.get("email"):
                    llm_key = os.environ.get("EMERGENT_LLM_KEY")
                    if llm_key and not reminder.get("ai_action_taken"):
                        try:
                            from emergentintegrations.llm.chat import LlmChat, UserMessage
                            chat = LlmChat(
                                api_key=llm_key,
                                session_id=f"auto_{uuid.uuid4().hex[:8]}",
                                system_message="You are a professional business assistant."
                            ).with_model("openai", "gpt-5.2")
                            ai_msg = await chat.send_message(UserMessage(
                                text=f"Write a brief follow-up for {company_name}. Context: {r_msg or 'Business follow-up'}. Under 100 words."
                            ))
                            await db.notifications.insert_one({
                                "id": str(uuid.uuid4()), "user_id": reminder["user_id"],
                                "title": f"AI composed message for {company_name}",
                                "message": ai_msg[:300], "type": "ai_action", "is_read": False,
                                "related_company_id": reminder.get("company_id", ""),
                                "related_reminder_id": reminder["id"],
                                "created_at": datetime.now(timezone.utc).isoformat(),
                            })
                            await db.reminders.update_one({"id": reminder["id"]}, {"$set": {"ai_action_taken": True}})
                        except Exception as e:
                            logger.error(f"AI auto error: {e}")

                # If no email available, create in-app notification
                if not user_email:
                    await db.notifications.insert_one({
                        "id": str(uuid.uuid4()), "user_id": reminder["user_id"],
                        "title": f"OVERDUE: {r_type} - {company_name}",
                        "message": f"Your {r_type} for {company_name} is overdue. {r_msg}",
                        "type": "overdue_reminder", "is_read": False,
                        "related_company_id": reminder.get("company_id", ""),
                        "related_reminder_id": reminder["id"],
                        "created_at": datetime.now(timezone.utc).isoformat(),
                    })
                    await db.reminders.update_one({"id": reminder["id"]}, {"$set": {"email_sent": True}})

        except Exception as e:
            logger.error(f"Reminder checker error: {e}")


@app.on_event("startup")
async def startup():
    await db.companies.create_index("user_id")
    await db.reminders.create_index("user_id")
    await db.notifications.create_index("user_id")
    await db.users.create_index("email")
    await db.users.create_index("phone")

    # Seed admin account if configured
    admin_email = os.environ.get("ADMIN_EMAIL")
    admin_pass = os.environ.get("ADMIN_PASSWORD")
    if admin_email and admin_pass:
        existing = await db.users.find_one({"email": admin_email})
        if not existing:
            await db.users.insert_one({
                "user_id": f"user_{uuid.uuid4().hex[:12]}",
                "email": admin_email,
                "phone": "",
                "password_hash": hash_password(admin_pass),
                "name": "Admin",
                "language": "en",
                "created_at": datetime.now(timezone.utc).isoformat(),
            })
            logger.info(f"Admin account created: {admin_email}")

    asyncio.create_task(check_overdue_reminders())
    logger.info("CRM Backend started")


@app.on_event("shutdown")
async def shutdown():
    client.close()


app.include_router(api_router)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Forces local bypass
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
