from typing import Callable
import time, random

def retry_with_backoff(fn: Callable, max_attempts: int = 5) -> None:
    for attempt in range(max_attempts):
        try:
            fn()
            return
        except Exception:
            if attempt == max_attempts - 1:
                raise
            time.sleep(2 ** attempt + random.uniform(0, 1))
            #          ^ exponential   ^ jitter — avoids synchronisation