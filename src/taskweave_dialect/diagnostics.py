from typing import Callable, Pattern
from dataclasses import dataclass, field

from .field import Field
from .dialect_error import DialectError, DialectErrorKind
from .diagnostic_info import DiagnosticInfo, DiagnosticInfoKind

"""
union is bad practice
WARNING:
group 2 matched but is not consumed by any extractor
INFO:
extractor "status" ignores groups [2, 3]
WARNING:
extractor "banner" did not match any sample lines
WARNING:
line matched multiple classifiers
"""

@dataclass(kw_only = True)
class Diagnostics:
    extractors : list[Field]
    messages : list[DiagnosticInfo] = field(default_factory = list)

    def analyze(self, parse_fn : Callable) -> list[DiagnosticInfo]:
        results : dict = {}
        error : DialectError | None = None
        try:
            results = parse_fn()
        except DialectError as e:
            error = e

        self._union_is_bad_practice(results, error)
        self._group_is_not_consumed(results, error)
        self._extractor_did_not_match_or_failed(results, error)
        self._multiple_extractors_matched(results, error)
        self._too_few_matches(results, error)
        self._multi_group_matched(results, error)
        self._multi_group_not_matched(results, error)

        return self.messages

    def _union_is_bad_practice(self, results : dict, error : DialectError | None):
        for extractor in self.extractors:
            if "|" in extractor.parser._rule.pattern:
                self.messages.append(
                    DiagnosticInfo(
                        kind = DiagnosticInfoKind.INFO,
                        msg = f"""
                            using 'or' in a 'target' is considered bad practice.
                            reason : confusing
                            using multiple extractors is considered cleaner
                            """
                    )
                )

    def _group_is_not_consumed(self, results : dict, error : DialectError | None):
        groups : dict[Pattern, list[int]] = {}
        consumed_groups : list[int] = []

        for extractor in self.extractors:
            consumed_groups.append(extractor.group)
            groups[extractor.parser._rule.pattern] = []
            for group in range(extractor.parser._rule.groups):
                groups[extractor.parser._rule.pattern].append(group + 1)

        for pattern, groups_list in groups.items():
            diff = set(groups_list) - set(consumed_groups)

            if len(diff):
                self.messages.append(
                    DiagnosticInfo(
                        kind = DiagnosticInfoKind.WARNING,
                        msg = f"""
                            Capturing group(s) {diff} in pattern /{pattern}/ are declared in the target
                            but no extractor consume them.
                            """
                    )
                )

    def _extractor_did_not_match_or_failed(self, results : dict, error : DialectError | None):
        if error is None or error.failures is None:
            return
        
        # reserve this diagnostics to single group targets
        for extractor in self.extractors:
            if extractor.parser._rule.groups > 1:
                return
        
        for failure in error.failures:
            if failure[2] == DialectErrorKind.NO_MATCH:
                self.messages.append(
                    DiagnosticInfo(
                        kind = DiagnosticInfoKind.INFO,
                        msg = f"""
                            Extractor '{failure[0]}' did not match : it might be by design
                            """
                    )
                )
            elif failure[2] == DialectErrorKind.INCOMPATIBLE_JSON_TYPE:
                self.messages.append(
                    DiagnosticInfo(
                        kind = DiagnosticInfoKind.ERROR,
                        msg = f"""
                            Extractor '{failure[0]}' failed when casting 
                            to declared JsonType {next((ext.schema.type for ext in self.extractors if ext.schema.name == failure[0]))}
                            """
                    )
                )

    def _multiple_extractors_matched(self, results : dict, error : DialectError | None):
        if len(results) < 2 or len(self.extractors) < 2:
            return
        
        self.messages.append(
            DiagnosticInfo(
                kind = DiagnosticInfoKind.INFO,
                msg = f"""
                    Multiple extractors matched on one line 
                    {[ext.schema.name for ext in self.extractors if ext.schema.name in results.keys()]}
                    """
            )
        )
        
    def _too_few_matches(self, results : dict, error : DialectError | None):
        # reserve this diagnostics to "actually matched"
        # but "partially matched" doesn't return results
        # -> check failures
        if error is None or error.failures is None:
            return

        if len(self.extractors) > 1:
            self.messages.append(
                DiagnosticInfo(
                    kind = DiagnosticInfoKind.WARNING,
                    msg = f"""
                        Too few extractors matched on one line (might be by design)
                        failurees are {error.failures}
                        """
                )
            )

    def _multi_group_matched(self, results : dict, error : DialectError | None):
        for extractor in self.extractors:
            if extractor.parser._rule.groups > 1:
                if len(results) > 0:
                    self.messages.append(
                        DiagnosticInfo(
                            kind = DiagnosticInfoKind.INFO,
                            msg = f"""
                                Multi group extractor matched on one line
                                {results.keys()} matched against extractors : {extractor.schema.name}
                                """
                        )
                    )

    def _multi_group_not_matched(self, results : dict, error : DialectError | None):
        for extractor in self.extractors:
            if extractor.parser._rule.groups > 1:
                if len(results) == 0:
                    self.messages.append(
                        DiagnosticInfo(
                            kind = DiagnosticInfoKind.ERROR,
                            msg = f"""
                                Multi group extractor didn't match on one line
                                {results.keys()} matched against extractors : {extractor.schema.name}
                                """
                        )
                    )
        
