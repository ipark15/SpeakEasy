from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
import traceback

load_dotenv()

app = FastAPI(title="SpeechScore API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    traceback.print_exc()
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc)},
        headers={"Access-Control-Allow-Origin": "*"},
    )


from backend.routers import assess
from backend.routers import dashboard

app.include_router(assess.router, prefix="/api")
app.include_router(dashboard.router, prefix="/api")


@app.get("/api/health")
def health():
    return {"status": "ok"}
