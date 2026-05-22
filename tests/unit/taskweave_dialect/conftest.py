import pytest
from itertools import cycle

@pytest.fixture
def get_line():
    lines = cycle([
        "status = 200 url = http://example.com",
        "status = 404 url = http://example.com/fail"
    ])

    return lambda: next(lines)