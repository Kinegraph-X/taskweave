import sys
import json
import time
import requests
import os
from pathlib import Path
from urllib.parse import urljoin

import dotenv

BASE_URL = "http://localhost:8000"

INPUT_FILE = Path(os.getenv("PRODUCTS_FOLDER") or "") / (os.getenv("URLS_FILE") or "")
OUTPUT_FILE = Path("validation_result.json")


def log(msg: str):
    print(msg, flush=True)


def load_urls():
    if INPUT_FILE.exists():
        data = json.loads(INPUT_FILE.read_text())
        return data.get("urls", [])
    # fallback (tests simples)
    return [
        "https://a.com",
        "https://b.com",
        "https://error.com",
        "https://slow.com",
    ]


def validate_url(url: str, retries: int = 1):
    attempt = 0

    while attempt <= retries:
        try:
            response = requests.get(
                f"{BASE_URL}/validate",
                params={"url": url},
                timeout=1.5,
            )

            log(f"status={response.status_code} url={url} attempt={attempt}")

            response.raise_for_status()
            data = response.json()

            valid = data.get("valid", False)
            log(f"valid={str(valid).lower()} url={url}")

            return {"valid": valid, "attempts": attempt + 1}

        except requests.Timeout:
            log(f"ERROR: timeout url={url} attempt={attempt}")

        except requests.HTTPError:
            log(f"ERROR: http_error url={url} status={response.status_code} attempt={attempt}")

        except Exception as e:
            log(f"ERROR: unexpected url={url} error={str(e)} attempt={attempt}")

        attempt += 1
        time.sleep(0.2)  # petit backoff

    return {"valid": False, "error": "max_retries_exceeded", "attempts": attempt}


def main():
    urls = load_urls()

    log(f"urls_count={len(urls)}")
    log("INFO: starting validation phase")

    results = {}
    valid_count = 0

    for idx, url in enumerate(urls):
        res = validate_url(url, retries=1)
        results[url] = res

        if res.get("valid"):
            valid_count += 1

        # 🔥 progression utile pour ton orchestrateur
        progress = int(((idx + 1) / len(urls)) * 100)
        log(f"progress={progress}")

    all_valid = valid_count == len(urls)

    output = {
        "valid": all_valid,
        "valid_count": valid_count,
        "total": len(urls),
        "results": results,
    }

    OUTPUT_FILE.write_text(json.dumps(output, indent=2))

    log(f"validation_complete valid={str(all_valid).lower()} valid_count={valid_count}")

    log("INFO: validation phase completed")

    # ⚠️ toujours 0 → laisse taskweave décider
    sys.exit(0)


if __name__ == "__main__":
    main()