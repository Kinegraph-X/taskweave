"""
regex_inspector.py

Adapter over re._parser (formerly sre_parse) — isolates all access to
CPython regex AST internals so the rest of the codebase never touches them.

Public API (stable across this module's versions):
    inspect(pattern: str) -> RegexInspection
    RegexInspection.has_union          -> bool
    RegexInspection.has_named_groups   -> bool
    RegexInspection.group_count        -> int

Raises RegexInspectorUnavailable if the underlying CPython internals
change in a future version. Callers should catch it and fall back to
re.compile() alone (losing the structural checks).
"""

from __future__ import annotations

import re
from dataclasses import dataclass


# ---------------------------------------------------------------------------
# Availability guard — the internals we depend on
# ---------------------------------------------------------------------------

try:
    import re._parser as _sre  # CPython 3.11+
    _SubPattern = _sre.SubPattern
except (ImportError, AttributeError):
    try:
        import sre_parse as _sre  # CPython ≤ 3.10, deprecated
        _SubPattern = _sre.SubPattern
    except (ImportError, AttributeError):
        _sre = None
        _SubPattern = None


class RegexInspectorUnavailable(RuntimeError):
    """Raised when the CPython regex AST internals are not accessible."""


# ---------------------------------------------------------------------------
# Result type
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class RegexInspection:
    has_union: bool
    has_named_groups: bool
    group_count: int


# ---------------------------------------------------------------------------
# Internal AST walker
# ---------------------------------------------------------------------------

def _walk(node):
    """
    Yield (opcode_str, av, parent_opcode_str) for every node in the AST.
    Handles SubPattern, list, and tuple nodes recursively.
    """
    yield from _walk_inner(node, parent_op=None)


def _walk_inner(node, parent_op):
    if isinstance(node, _SubPattern):
        yield from _walk_inner(node.data, parent_op)
    elif isinstance(node, list):
        for item in node:
            yield from _walk_inner(item, parent_op)
    elif isinstance(node, tuple) and len(node) >= 2:
        op, av = node[0], node[1]
        op_str = str(op)
        yield (op_str, av, parent_op)
        if isinstance(av, (_SubPattern, list)):
            yield from _walk_inner(av, op_str)
        elif isinstance(av, tuple):
            # SUBPATTERN stores (group_id, add_flags, del_flags, SubPattern)
            # — the nested SubPattern is at index 3, not directly iterable
            # as (op, av) pairs. Descend into each element that is a
            # SubPattern or list; skip plain integers.
            for element in av:
                if isinstance(element, (_SubPattern, list)):
                    yield from _walk_inner(element, op_str)


# ---------------------------------------------------------------------------
# Detection predicates
# ---------------------------------------------------------------------------

_PIPE_ORD = ord("|")  # 124


def _has_union(parsed) -> bool:
    """
    True if the pattern contains a meaningful union (|) — i.e. an alternation
    between multi-character tokens, categories, or groups.

    The CPython regex AST produces two opcodes for alternation:

      - BRANCH : multi-char alternation (foo|bar, \\w|foo, (\\w+)|(foo)).
                 This is what we forbid — it means "match this OR that whole
                 token/group", which belongs in the Classifier, not a Field.

      - IN     : the parser optimises single-char-literal alternation (a|b)
                 into the same opcode as a character class ([ab]). The two
                 forms are semantically identical, so we leave them alone.

    Note: [a|b] also produces IN with a pipe literal among its children.
    Neither IN form is flagged — both are harmless char-class style.
    """
    for op, _av, _parent in _walk(parsed):
        if op == "BRANCH":
            return True
    return False


def _has_named_groups(parsed) -> bool:
    """True if any capturing group is named (?P<name>...)."""
    return bool(parsed.state.groupdict)


def _group_count(parsed) -> int:
    """Number of capturing groups (same as compiled.groups)."""
    return parsed.state.groups - 1  # state.groups is 1-indexed


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def inspect(pattern: str) -> RegexInspection:
    """
    Parse *pattern* and return a RegexInspection.

    Raises:
        re.error                    — pattern is syntactically invalid
        RegexInspectorUnavailable   — CPython internals not accessible
    """
    if _sre is None or _SubPattern is None:
        raise RegexInspectorUnavailable(
            "re._parser internals are not available in this Python build. "
            "Structural checks (union, named groups) cannot be performed."
        )

    try:
        parsed = _sre.parse(pattern)
    except Exception as exc:
        # Re-raise as a standard re.error so callers get a uniform exception.
        raise re.error(str(exc)) from exc

    try:
        return RegexInspection(
            has_union=_has_union(parsed),
            has_named_groups=_has_named_groups(parsed),
            group_count=_group_count(parsed),
        )
    except AttributeError as exc:
        raise RegexInspectorUnavailable(
            f"re._parser API changed in this Python version: {exc}"
        ) from exc


# ---------------------------------------------------------------------------
# Smoke-test (python regex_inspector.py)
# ---------------------------------------------------------------------------

# if __name__ == "__main__":
#     cases = [
#         # (pattern, expect_union, expect_named, expect_groups)
#         # BRANCH = real union -> forbidden
#         (r"foo|bar",           True,  False, 0),
#         (r"[a-z]|foo",         True,  False, 0),
#         (r"(\w+)|(foo)",       True,  False, 2),
#         (r"(?P<x>\w+)|foo",    True,  True,  1),
#         # IN = single-char alternation, optimised same as char class -> allowed
#         (r"a|b",               False, False, 0),
#         (r"[a|b]",             False, False, 0),
#         (r"(a|b)",             False, False, 1),
#         # No union
#         (r"(?P<name>\w+)",     False, True,  1),
#         (r"(\w+)(foo)",        False, False, 2),
#         (r"status=(\w+)",      False, False, 1),
#     ]

#     all_ok = True
#     for pattern, exp_union, exp_named, exp_groups in cases:
#         r = inspect(pattern)
#         ok = (
#             r.has_union == exp_union
#             and r.has_named_groups == exp_named
#             and r.group_count == exp_groups
#         )
#         status = "OK" if ok else "FAIL"
#         if not ok:
#             all_ok = False
#         print(
#             f"[{status}] {pattern!r:30}"
#             f"  union={r.has_union} (exp {exp_union})"
#             f"  named={r.has_named_groups} (exp {exp_named})"
#             f"  groups={r.group_count} (exp {exp_groups})"
#         )

#     print()
#     print("All OK" if all_ok else "FAILURES detected")