from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import parse, export, reminders

app = FastAPI(title="Syllabus Parser API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(parse.router, prefix="/parse", tags=["parse"])
app.include_router(export.router, prefix="/export", tags=["export"])
app.include_router(reminders.router, prefix="/reminders", tags=["reminders"])


@app.get("/health")
async def health():
    return {"status": "ok"}
