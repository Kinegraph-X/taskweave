import pytest
import re

from taskweave_protocol import JsonSchemaType, FieldSchema
from taskweave_dialect import Field, RExtractor

# def test_line_extractor_malformed():
#     status_schema = FieldSchema("status", JsonSchemaType.INT)

#     with pytest.raises(ValueError) as e:
#         status_field = Field(schema = status_schema, target = r"status")


# def test_line_extractor(
#         get_line
#     ):
#     status_schema = FieldSchema("status", JsonSchemaType.INT)
#     url_schema = FieldSchema("url",    JsonSchemaType.STRING)

#     status_field = Field(schema = status_schema, target = r"status\s*=\s*(\w+)")
#     url_field = Field(schema = url_schema, target = r"url\s*=\s*([\w/:]+)")

#     fetch_extractor = RExtractor(
#         extractors = [status_field, url_field]
#     )

#     result = fetch_extractor.parse(get_line())
#     print(result)
#     assert result["status"] == 200
    # assert result["url"] == "http://example.com"

    # result = fetch_extractor.parse(get_line())
    # assert result["status"] == 404
    # assert result["url"] == "http://example.com/fail"


# def test_line_extractor_group(
#         get_line
#     ):
#     aggregate = FieldSchema("aggregate", JsonSchemaType.STRING)
#     exp = r"status\s*=\s*(\w+)\s*url\s*=\s*([\w/:]+)"
#     re.compile(exp)
#     status_field = Field(schema = aggregate, target = exp, group = 1)
#     url_field = Field(schema = aggregate, target = exp, group = 2)

#     fetch_extractor = RExtractor(
#         extractors = [status_field, url_field]
#     )

#     result = fetch_extractor.parse(get_line()())
#     assert result["status"] == "200"
#     assert result["url"] == "http://example.com"

#     result = fetch_extractor.parse(get_line()())
#     assert result["status"] == "404"
#     assert result["url"] == "http://example.com/fail"


# def test_line_extractor_group_over_max(
#         get_line
#     ):
#     aggregate = FieldSchema("aggregate", JsonSchemaType.STRING)
#     exp = r"status\s*=\s*(\w+)\s*url\s*=\s*([\w/:]+)"
#     with pytest.raises(Exception) as e:
#         status_field = Field(schema = aggregate, target = exp, group = 3)