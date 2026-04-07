from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import export, files, parse, reminders

app = FastAPI(
    title="Syllabus Parser API",
    version="0.1.0",
    description="API for parsing syllabi and exporting to calendars",
)

ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "https://syllabuddy.vercel.app",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(parse.router, prefix="/parse", tags=["parse"])
app.include_router(export.router, prefix="/export", tags=["export"])
app.include_router(reminders.router, prefix="/reminders", tags=["reminders"])
app.include_router(files.router, prefix="/files", tags=["files"])


@app.get("/health")
async def health():
    return {"status": "ok"}
