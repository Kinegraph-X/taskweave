from __future__ import annotations
from typing import Pattern
from dataclasses import dataclass
import re

from .dialect_error import DialectErrorKind, MSG_TO_ERROR, DialectError
from .regex_inspector import inspect

@dataclass(kw_only = True)
class ValidateRule:
    rule : Pattern

    @staticmethod
    def validate(target : Pattern | str, group : int) -> ValidateRule:
        rule = ValidateRule._validate_malformed(target)
        ValidateRule._validate_missing_group(rule)
        ValidateRule._validate_out_of_bound(rule, group)
        ValidateRule._validate_named_group(rule)
        ValidateRule._validate_union(rule)
        return ValidateRule(rule = rule)  

    @staticmethod
    def _validate_malformed(target : Pattern | str) -> Pattern:
        try:
            rule = re.compile(target)
        except re.error as e: # re.error, re.PatternError python >= 3.13
            error = ValidateRule.get_error(
                target = target,
                msg = e.msg,
                pos = e.pos
            )
            raise error.with_traceback(None) from None

        return rule

    @staticmethod
    def _validate_missing_group(rule : Pattern):
        if rule.groups == 0:
            raise DialectError(
                kind = DialectErrorKind.MISSING_GROUP,
                pattern = rule.pattern,
                msg = f"Pattern '{rule.pattern}' must contain a capturing group — use (...)"
            ).with_traceback(None) from None

    @staticmethod
    def _validate_out_of_bound(rule : Pattern, group : int):
        print(group, rule.groups)
        if group > rule.groups:
            exc = DialectError(
                kind = DialectErrorKind.OUT_OF_BOUND_GROUP,
                pattern = rule.pattern,
                msg = f"""Field declaration : 'target' expects {rule.groups} to be max group, 
                    but group={group} was defined in Field"""
            )
            raise exc.with_traceback(None) from None

    @staticmethod
    def _validate_named_group(rule : Pattern):
        if rule.groupindex:
            exc = DialectError(
                kind = DialectErrorKind.NAMED_GROUP_FORBIDDEN,
                pattern = rule.pattern,
                msg = f"""Field declaration : 'target' uses named groups, 
                    they wouldn't be considered"""
            )
            raise exc.with_traceback(None) from None

    @staticmethod
    def _validate_union(rule : Pattern):
        try: 
            inspection_result = inspect(str(rule))
            if  inspection_result.has_union:
                raise DialectError(
                    kind = DialectErrorKind.UNION_FORBIDDEN,
                    pattern = rule.pattern,
                    msg = f"""Field declaration : 'target' uses unions, 
                        it is confusing/redundant with multiple RExtrator,
                        and so considered bad practice"""
                )
        except Exception as e:
            raise e

    @staticmethod
    def get_error(target : Pattern | str, msg : str, pos : int | None):
        for error in MSG_TO_ERROR.keys():
            if error in msg:
                kind = MSG_TO_ERROR[error]
                break
            else:
                kind = DialectErrorKind.UNKNOWN

        return DialectError(
            kind = kind,
            pattern = None,
            pos = pos,
            msg = f"{msg} in 'target' {target}"
        )