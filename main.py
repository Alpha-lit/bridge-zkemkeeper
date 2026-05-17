"""
Gym Fingerprint Bridge Service (ZK9500 via zkemkeeper.dll)

FastAPI app that runs on the gym entrance Windows PC.
Communicates with ZK9500 via zkemkeeper.dll (same SDK as ZKAccess).
Listens on http://localhost:5555
"""

import sys
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from zkengine import engine, ZKFingerError

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger("bridge")


# --- Models ---

class StatusResponse(BaseModel):
    status: str
    device_ip: str
    user_count: int = 0
    device_time: str | None = None


class EnrollRequest(BaseModel):
    user_id: int
    name: str


class DeleteRequest(BaseModel):
    user_id: int


class SyncRequest(BaseModel):
    members: list[dict]


class SyncResponse(BaseModel):
    synced: int
    errors: list[str] = []


# --- App ---

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting bridge service...")
    try:
        engine.initialize()
    except ZKFingerError as e:
        logger.error(f"Scanner init failed: {e}")
    yield
    logger.info("Shutting down...")
    engine.cleanup()


app = FastAPI(title="Gym Fingerprint Bridge (ZK9500)", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# Allow browsers to access localhost from public origins (Private Network Access)
@app.middleware("http")
async def add_pna_header(request, call_next):
    response = await call_next(request)
    response.headers["Access-Control-Allow-Private-Network"] = "true"
    return response


@app.get("/status", response_model=StatusResponse)
async def check_status():
    if not engine.is_connected:
        # Try reconnecting
        try:
            engine.initialize()
        except ZKFingerError:
            pass

    user_count = 0
    device_time = None
    if engine.is_connected:
        try:
            user_count = engine.get_user_count()
        except Exception:
            pass
        try:
            device_time = engine.get_device_time()
        except Exception:
            pass

    return StatusResponse(
        status="ok" if engine.is_connected else "scanner_offline",
        device_ip=engine._ip,
        user_count=user_count,
        device_time=device_time,
    )


@app.post("/enroll")
async def enroll_user(req: EnrollRequest):
    """Create user on device and start finger enrollment."""
    if not engine.is_connected:
        raise HTTPException(status_code=503, detail="Scanner not connected")
    try:
        engine.enroll_user(req.user_id, req.name)
        engine.start_enroll(req.user_id, finger_index=0)
        return {"status": "ok", "message": "Place finger on scanner to enroll"}
    except ZKFingerError as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/user/{user_id}")
async def delete_user(user_id: int):
    """Remove a user from the device."""
    if not engine.is_connected:
        raise HTTPException(status_code=503, detail="Scanner not connected")
    try:
        engine.delete_user(user_id)
        return {"status": "ok"}
    except ZKFingerError as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/sync")
async def sync_members(req: SyncRequest):
    """Bulk sync Django members to ZK9500."""
    if not engine.is_connected:
        raise HTTPException(status_code=503, detail="Scanner not connected")

    synced = 0
    errors = []
    for member in req.members:
        try:
            engine.enroll_user(member["user_id"], member["name"])
            synced += 1
        except Exception as e:
            errors.append(f"Member {member.get('user_id')}: {e}")

    return SyncResponse(synced=synced, errors=errors)


@app.get("/users")
async def list_users():
    """List all users stored on device."""
    if not engine.is_connected:
        raise HTTPException(status_code=503, detail="Scanner not connected")
    try:
        return engine.get_all_users()
    except ZKFingerError as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/attendance")
async def get_attendance():
    """Get attendance/check-in logs from device."""
    if not engine.is_connected:
        raise HTTPException(status_code=503, detail="Scanner not connected")
    try:
        return engine.read_attendance_log()
    except ZKFingerError as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/attendance/clear")
async def clear_attendance():
    """Clear attendance logs from device."""
    if not engine.is_connected:
        raise HTTPException(status_code=503, detail="Scanner not connected")
    try:
        engine.clear_attendance_log()
        return {"status": "ok"}
    except ZKFingerError as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 5555
    logger.info(f"Bridge starting on http://localhost:{port}")
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="info")
