import os 
from datetime import datetime, timedelta
from fastapi import HTTPException, Request
import redis

# Define rate limiting settings
RATE_LIMIT = 1  # Number of requests
RATE_LIMIT_TIME = 3600  # Time window in seconds

redis_host = os.environ.get("REDIS_HOST")
redis_port = os.environ.get("REDIS_PORT")
redis_password = os.environ.get("REDIS_PASSWORD")

# Create a Redis client instance
redis_client = redis.Redis(
    host=redis_host,
    port=redis_port,
    password=redis_password,
    ssl=True,  # Enable SSL/TLS
    decode_responses=True,
)

def rate_limiter(request: Request):
    client_ip = request.client.host
    current_time = datetime.now()

    redis_key = "rate_limit:" + client_ip

    last_request_time, count, status = redis_client.hmget(redis_key, "timestamp", "count", "status")

    if status == b"failed":
        count = 0  # Reset the count if the last request failed
        return  # Skip counting failed requests

    elif last_request_time and (current_time - datetime.strptime(last_request_time, "%Y-%m-%d %H:%M:%S.%f")) <= timedelta(seconds=RATE_LIMIT_TIME):
        if int(count) >= RATE_LIMIT:
            raise HTTPException(
                status_code=429,
                detail="Account creation rate limit exceeded! Please wait before trying again.",
            )
    else:
        # Create a new Redis key for each new client and store request info
        redis_client.hmset(
            redis_key,
            {
                "timestamp": current_time.strftime("%Y-%m-%d %H:%M:%S.%f"),
                "count": 0,
                "status": b"failed",  # Set a default value here
            },
        )

def update_request_info(redis_client, redis_key, status):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
    if status == "failed":
        count = 0
    else:
        count = int(redis_client.hget(redis_key, "count") or 0) + 1
        
    redis_client.hmset(
        redis_key,
        {
            "timestamp": timestamp,
            "count": count,
            "status": status,
        },
    )
