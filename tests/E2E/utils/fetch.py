import sys
import requests
import time
import json
import os
from pathlib import Path

BASE_URL = "http://localhost:8000"


def log(msg: str):
    # stdout → capté par taskweave
    print(msg, flush=True)


def main():
    try:
        log("INFO: starting fetch phase")

        response = requests.get(f"{BASE_URL}/urls", timeout=5)

        # Ligne parsable par ton dialect
        log(f"status={response.status_code} url={BASE_URL}/urls")

        response.raise_for_status()
        data = response.json()

        urls = data.get("urls", [])
        urls_file = os.path.join(os.getenv("PRODUCTS_FOLDER"), os.getenv("URLS_FILE"))
        Path(urls_file).write_text(json.dumps({"urls": urls}))
        log(f"urls_count={len(urls)}")

        for url in urls:
            try:
                # Simule un "traitement" réseau léger
                time.sleep(0.1)

                # Ici on ne fetch pas le contenu réel de l’URL,
                # on simule juste un passage dans le pipeline
                log(f"status=200 url={url}")

            except Exception as e:
                # Ligne non parsée → DISCARD normalement
                log(f"ERROR: failed processing url={url} error={str(e)}")

        log("INFO: fetch phase completed")

    except requests.RequestException as e:
        log(f"ERROR: fetch failed error={str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()