import os
from fastapi import Header, HTTPException, status


API_SECRET_KEY = os.getenv("API_SECRET_KEY", "")


async def verify_api_key(x_api_key: str = Header(...)):
    if not API_SECRET_KEY:
        raise HTTPException(status_code=500, detail="API_SECRET_KEY not configured")
    if x_api_key != API_SECRET_KEY:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")
