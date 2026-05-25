from contextlib import asynccontextmanager

from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware

from config import database
from routes import (
    ai_chatbot, analytics, appointments, auth, clinical_support,
    drug_checker, patients, report_analyzer, medicines, live_chat,
    staff, departments, wards, billing, lab_tests, prescriptions,
    notifications, users, websocket_handler,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await database.connect_to_postgres()
    yield
    await database.close_postgres_connection()


app = FastAPI(
    title="MedAI — Intelligent Hospital Ecosystem",
    description="FastAPI backend for a multi-provider AI hospital platform with patient & admin portals.",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
        "http://localhost:5175",
        "http://127.0.0.1:5175",
        "http://localhost:4173",
        "http://127.0.0.1:4173",
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Existing routes
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(patients.router, prefix="/api/patients", tags=["patients"])
app.include_router(appointments.router, prefix="/api/appointments", tags=["appointments"])
app.include_router(ai_chatbot.router, prefix="/api/ai", tags=["ai-chatbot"])
app.include_router(report_analyzer.router, prefix="/api/ai", tags=["report-analyzer"])
app.include_router(drug_checker.router, prefix="/api/ai", tags=["drug-checker"])
app.include_router(clinical_support.router, prefix="/api/ai", tags=["clinical-support"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["analytics"])

# New hospital management routes
app.include_router(staff.router, prefix="/api/staff", tags=["staff"])
app.include_router(departments.router, prefix="/api/departments", tags=["departments"])
app.include_router(wards.router, prefix="/api/wards", tags=["wards"])
app.include_router(billing.router, prefix="/api/billing", tags=["billing"])
app.include_router(lab_tests.router, prefix="/api/lab-tests", tags=["lab-tests"])
app.include_router(prescriptions.router, prefix="/api/prescriptions", tags=["prescriptions"])
app.include_router(medicines.router, prefix="/api/medicines", tags=["medicines"])
app.include_router(live_chat.router, prefix="/api/chat", tags=["live-chat"])
app.include_router(notifications.router, prefix="/api/notifications", tags=["notifications"])
app.include_router(users.router, prefix="/api/users", tags=["users"])

# WebSocket for real-time sync
app.include_router(websocket_handler.router, prefix="", tags=["websocket"])


@app.get("/api/health")
async def health_check():
    return {
        "status": "ok",
        "db": "connected" if database.pool is not None else "disconnected",
        "database": database.BACKEND_NAME,
        "websocket": "ws://localhost:8000/ws",
    }


@app.get("/")
async def root():
    return {
        "message": "MedAI backend is running",
        "admin_portal": "http://127.0.0.1:5173",
        "patient_portal": "http://127.0.0.1:5174",
        "health": "http://127.0.0.1:8000/api/health",
        "docs": "http://127.0.0.1:8000/docs",
        "websocket": "ws://localhost:8000/ws",
    }


@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return Response(status_code=204)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
