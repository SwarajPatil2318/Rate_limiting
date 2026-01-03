from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from collections import deque, defaultdict
import time

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

# ------------------ APP SETUP ------------------

app = FastAPI()

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ------------------ SHARED QUEUE ------------------

queue = deque()

class QueueItem(BaseModel):
    value: str

# ------------------ SLIDING WINDOW ------------------

WINDOW = 60
SLIDING_LIMIT = 3
sliding_requests = defaultdict(deque)

def sliding_window_allow(ip: str) -> bool:
    now = time.time()
    window = sliding_requests[ip]

    while window and window[0] <= now - WINDOW:
        window.popleft()

    if len(window) >= SLIDING_LIMIT:
        return False

    window.append(now)
    return True

# ------------------ LEAKY BUCKET ------------------

LEAK_RATE = 1          # requests per second
BUCKET_CAPACITY = 5

leaky_bucket = defaultdict(lambda: {
    "water": 0,
    "last_check": time.time()
})

def leaky_bucket_allow(ip: str) -> bool:
    now = time.time()
    bucket = leaky_bucket[ip]

    elapsed = now - bucket["last_check"]
    leaked = elapsed * LEAK_RATE

    bucket["water"] = max(0, bucket["water"] - leaked)
    bucket["last_check"] = now

    if bucket["water"] >= BUCKET_CAPACITY:
        return False

    bucket["water"] += 1
    return True

# ------------------ TOKEN BUCKET ------------------

TOKEN_RATE = 1         # tokens per second
TOKEN_CAPACITY = 5

token_bucket = defaultdict(lambda: {
    "tokens": TOKEN_CAPACITY,
    "last_refill": time.time()
})

def token_bucket_allow(ip: str) -> bool:
    now = time.time()
    bucket = token_bucket[ip]

    elapsed = now - bucket["last_refill"]
    refill = elapsed * TOKEN_RATE

    bucket["tokens"] = min(
        TOKEN_CAPACITY,
        bucket["tokens"] + refill
    )
    bucket["last_refill"] = now

    if bucket["tokens"] < 1:
        return False

    bucket["tokens"] -= 1
    return True

# ------------------ ENDPOINTS ------------------

@app.get("/")
def root():
    return {"message": "Queue with Rate Limiting is running 🚀"}

# ---------- FIXED WINDOW (SlowAPI) ----------

@app.post("/queue/fixed")
@limiter.limit("3/minute")
def queue_fixed(item: QueueItem, request: Request):
    queue.append(item.value)
    return {
        "message": "Added via Fixed Window",
        "queue": list(queue)
    }


# ---------- SLIDING WINDOW ----------

@app.post("/queue/sliding")
def queue_sliding(item: QueueItem, request: Request):
    ip = request.client.host

    if not sliding_window_allow(ip):
        raise HTTPException(
            status_code=429,
            detail="Sliding window rate limit exceeded"
        )

    queue.append(item.value)
    return {
        "message": "Added via Sliding Window",
        "queue": list(queue)
    }

# ---------- LEAKY BUCKET ----------

@app.post("/queue/leaky")
def queue_leaky(item: QueueItem, request: Request):
    ip = request.client.host

    if not leaky_bucket_allow(ip):
        raise HTTPException(
            status_code=429,
            detail="Leaky bucket rate limit exceeded"
        )

    queue.append(item.value)
    return {
        "message": "Added via Leaky Bucket",
        "queue": list(queue)
    }

# ---------- TOKEN BUCKET ----------

@app.post("/queue/token")
def queue_token(item: QueueItem, request: Request):
    ip = request.client.host

    if not token_bucket_allow(ip):
        raise HTTPException(
            status_code=429,
            detail="Token bucket rate limit exceeded"
        )

    queue.append(item.value)
    return {
        "message": "Added via Token Bucket",
        "queue": list(queue)
    }

# ---------- QUEUE REMOVE (NO RATE LIMITING) ----------

@app.delete("/queue")
def queue_out():
    if not queue:
        raise HTTPException(status_code=400, detail="Queue is empty")

    removed = queue.popleft()
    return {
        "message": "Item removed",
        "removed": removed,
        "queue": list(queue)
    }
