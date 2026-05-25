import pytest
import re

from taskweave_protocol import JsonSchemaType, FieldSchema, MsgType
from taskweave_dialect import Field, RExtractor, DialectErrorKind, DialectError, DiagnosticInfoKind

def test_line_extractor_malformed():
    status_schema = FieldSchema("status", JsonSchemaType.INT)

    with pytest.raises(DialectError) as e:
        status_field = Field(schema = status_schema, target = r"status(") # unterminated group
    
    assert e.value.kind == DialectErrorKind.UNTERMINATED_GROUP


def test_line_extractor_no_group():
    status_schema = FieldSchema("status", JsonSchemaType.INT)

    with pytest.raises(DialectError) as e:
        status_field = Field(schema = status_schema, target = r"status") # no capturing group
        
    assert e.value.kind == DialectErrorKind.MISSING_GROUP


def test_line_extractor_out_of_bound():
    status_schema = FieldSchema("status", JsonSchemaType.INT)

    with pytest.raises(DialectError) as e:
        status_field = Field(schema = status_schema, target = r"status(.+)", group = 2) # group > capturing groups
        
    assert e.value.kind == DialectErrorKind.OUT_OF_BOUND_GROUP


def test_line_extractor(
        source_id,
        get_line,
        log_bus
    ):
    status_schema = FieldSchema("status", JsonSchemaType.INT)
    url_schema = FieldSchema("url", JsonSchemaType.STRING)

    status_field = Field(schema = status_schema, target = r"status\s*=\s*(\w+)")
    url_field = Field(schema = url_schema, target = r"url\s*=\s*([\w/:\.]+)")

    fetch_extractor = RExtractor(
        extractors = [status_field, url_field]
    )

    fetch_extractor.make_runner(
        log_bus = log_bus,
        source_id = source_id
    )

    result = fetch_extractor.parse(get_line())
    assert result["status"] == 200
    assert result["url"] == "http://example.com"

    result = fetch_extractor.parse(get_line())
    assert result["status"] == 404
    assert result["url"] == "http://example.com/fail"


def test_line_extractor_group(
        source_id,
        get_line,
        log_bus
    ):
    status_schema = FieldSchema("status", JsonSchemaType.INT)
    url_schema = FieldSchema("url", JsonSchemaType.STRING)
    exp = r"status\s*=\s*(\w+)\s*url\s*=\s*([\w/:\.]+)"
    
    status_field = Field(schema = status_schema, target = exp, group = 1)
    url_field = Field(schema = url_schema, target = exp, group = 2)

    fetch_extractor = RExtractor(
        extractors = [status_field, url_field]
    )

    fetch_extractor.make_runner(
        log_bus = log_bus,
        source_id = source_id
    )

    result = fetch_extractor.parse(get_line())
    assert result["status"] == 200
    assert result["url"] == "http://example.com"

    result = fetch_extractor.parse(get_line())
    assert result["status"] == 404
    assert result["url"] == "http://example.com/fail"


def test_line_extractor_group_over_max(
        get_line
    ):
    aggregate = FieldSchema("aggregate", JsonSchemaType.STRING)
    exp = r"status\s*=\s*(\w+)\s*url\s*=\s*([\w/:]+)"
    with pytest.raises(Exception) as e:
        status_field = Field(schema = aggregate, target = exp, group = 3)


def test_line_extractor_propagated_cast_error(
        source_id,
        get_line,
        log_events,
        log_bus
    ):
    status_schema = FieldSchema("status", JsonSchemaType.BOOL)

    status_field = Field(schema = status_schema, target = r"status\s*=\s*(\w+)")

    fetch_extractor = RExtractor(
        extractors = [status_field]
    )

    fetch_extractor.make_runner(
        log_bus = log_bus,
        source_id = source_id
    )
    result = fetch_extractor.parse(get_line())

    assert len(log_events) == 1
    assert log_events[0].msg_type == MsgType.DIALECT_ERROR



"""
TEST MODE
"""

def test_line_extractor_did_not_match(
        source_id,
        get_line,
        log_events,
        log_bus
    ):
    status_schema = FieldSchema("status", JsonSchemaType.INT)
    url_schema = FieldSchema("url", JsonSchemaType.STRING)

    status_pattern = r"status\s*=\s*(\w+)"
    url_pattern = r"url\s*=\s*([\w/:\.]+)"

    status_field = Field(schema = status_schema, target = status_pattern)
    url_field = Field(schema = url_schema, target = url_pattern)

    fetch_extractor = RExtractor(
        extractors = [status_field, url_field]
    )

    fetch_extractor.make_runner(
        log_bus = log_bus,
        source_id = source_id
    )

    messages = fetch_extractor.return_test("status = 200")
    collected_messages : list[tuple[DiagnosticInfoKind, str]] = []

    for m in messages:
        if m.kind == DiagnosticInfoKind.INFO:
            collected_messages.append((m.kind, m.msg))

    assert len(collected_messages) == 1
    assert collected_messages[0][0] == DiagnosticInfoKind.INFO
    assert "Extractor 'url' did not match" in collected_messages[0][1]


def test_line_extractor_too_few_matches(
        source_id,
        get_line,
        log_events,
        log_bus
    ):
    status_schema = FieldSchema("status", JsonSchemaType.INT)
    url_schema = FieldSchema("url", JsonSchemaType.STRING)

    status_pattern = r"status\s*=\s*(\w+)"
    url_pattern = r"url\s*=\s*([\w/:\.]+)"

    status_field = Field(schema = status_schema, target = status_pattern)
    url_field = Field(schema = url_schema, target = url_pattern)

    fetch_extractor = RExtractor(
        extractors = [status_field, url_field]
    )

    fetch_extractor.make_runner(
        log_bus = log_bus,
        source_id = source_id
    )

    messages = fetch_extractor.return_test("status = 200")
    collected_messages : list[tuple[DiagnosticInfoKind, str]] = []

    for m in messages:
        if m.kind == DiagnosticInfoKind.ERROR:
            collected_messages.append((m.kind, m.msg))
    
    assert len(collected_messages) == 1
    assert collected_messages[0][0] == DiagnosticInfoKind.ERROR
    assert "Too few extractors matched" in collected_messages[0][1]


