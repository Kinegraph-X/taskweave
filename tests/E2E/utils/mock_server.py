from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
import time

app = FastAPI()

# Dataset déterministe (aucun hasard)
URLS = [
    "https://a.com",
    "https://b.com",
    "https://error.com",
    "https://slow.com",
]

VALIDATION_RESULTS = {
    "https://a.com": {"valid": True},
    "https://b.com": {"valid": False},
    "https://error.com": "error",
    "https://slow.com": "slow",
}


@app.get("/urls")
def get_urls():
    return {"urls": URLS}


@app.get("/validate")
def validate(url: str):
    if url not in VALIDATION_RESULTS:
        raise HTTPException(status_code=404, detail="Unknown URL")

    result = VALIDATION_RESULTS[url]

    # Simule erreur serveur
    if result == "error":
        raise HTTPException(status_code=500, detail="Internal error")

    # Simule timeout / latence
    if result == "slow":
        time.sleep(2)
        return {"valid": True}

    return result


@app.get("/health")
def health():
    return {"status": "ok"}