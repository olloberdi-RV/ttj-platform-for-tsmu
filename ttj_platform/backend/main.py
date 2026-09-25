import os
import sys

# Ensure project root is in sys.path
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles

from backend.routes import (
    auth_routes, building_routes, student_routes,
    payment_routes, import_routes, report_routes,
    audit_routes, dashboard_routes, backup_routes,
    user_routes, ref_routes
)

app = FastAPI(
    title="Talabalar Turar Joyi (TTJ) Boshqaruv Platformasi",
    description="Toshkent Davlat Tibbiyot Universiteti va Oliy ta'lim muassasalari TTJ boshqaruv tizimi API",
    version="1.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include all API Routers
app.include_router(auth_routes.router)
app.include_router(building_routes.router)
app.include_router(student_routes.router)
app.include_router(payment_routes.router)
app.include_router(import_routes.router)
app.include_router(report_routes.router)
app.include_router(audit_routes.router)
app.include_router(dashboard_routes.router)
app.include_router(backup_routes.router)
app.include_router(user_routes.router)
app.include_router(ref_routes.router)

FRONTEND_PUBLIC_DIR = os.path.join(os.path.dirname(__file__), "../frontend/public")

if os.path.exists(FRONTEND_PUBLIC_DIR):
    app.mount("/static", StaticFiles(directory=FRONTEND_PUBLIC_DIR), name="static")

@app.get("/")
def serve_index():
    index_file = os.path.join(FRONTEND_PUBLIC_DIR, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return {
        "status": "online",
        "system": "Talabalar Turar Joyi (TTJ) Boshqaruv Tizimi API",
        "docs": "/docs",
        "version": "1.0.0"
    }

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    import traceback
    traceback.print_exc()
    return JSONResponse(
        status_code=500,
        content={"detail": f"Serverda xatolik yuz berdi: {str(exc)}"}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
