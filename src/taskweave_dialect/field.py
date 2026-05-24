from typing import Any, Pattern, Callable
from dataclasses import asdict, field
import re, ast, json, traceback

from .dialect_error import DialectErrorKind, MSG_TO_ERROR, DialectError
from .field_parser import DialectParser, FieldParser
from .dialect_cast import DIALECT_CAST

from taskweave_protocol import FieldSchema, OutputType, JsonSchemaType


class Field:
    """
    Cast & lightweight Validation step
    """
    def __init__(
        self,
        *,
        schema: FieldSchema,
        target : str | Pattern,
        group : int = 1,
        category: OutputType = OutputType.PROGRESS,
        parser : DialectParser = field(init = False)
    ):
        if not target:
            raise ValueError('Bad argument to Field() : "target" isn\'t defined')
        elif not isinstance(target, (str, Pattern)):
            raise ValueError('Bad argument to Field() : "target" must be str | Pattern')

        self.schema = schema
        self.group = group
        self.category = category
        if callable(parser):
            parser(target = target)
        else:
            self.parser = FieldParser(target = target)

        try:
            self.parser.compile()
        except Exception as e:
            raise e.with_traceback(None) from None
        
        if self.group > self.parser._rule.groups:
            exc = DialectError(
                kind = DialectErrorKind.OUT_OF_BOUND_GROUP,
                pattern = self.parser._rule.pattern,
                msg = f"""Field declaration : 'target' has {self.parser._rule.groups} group(s), 
                    but group={self.group} was requested"""
            )
            raise exc.with_traceback(None) from None

    def parse(self, line : str, is_test : bool = False) -> Any | None:
        try:
            ret = self.cast(
                self.parser.parse(
                    line,
                    self.group,
                    is_test
                )
            )
        except Exception as e:
            raise e
        return ret
    
    def cast(self, value : str) -> Any :
        caster = DIALECT_CAST[self.schema.type]
        assert callable(caster)

        try:
            ret = caster(value)
        except Exception as e:
            raise DialectError(
                kind = DialectErrorKind.INCOMPATIBLE_JSON_TYPE,
                msg = f'log eval incompatible with declared field type in schema : expected {self.schema.type}: {self.get_error(e)}',
                pattern = self.parser._rule.pattern
            ).with_traceback(None) from None
        return ret

    def get_error(self, e : Exception):
        if isinstance(e, ValueError):
            return f"ValueError : {str(e)}"
        elif isinstance(e, TypeError):
            return f"TypeError : {str(e)}"
        else:
            return f"Exception : {str(e)}"