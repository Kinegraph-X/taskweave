from typing import Callable, Pattern
from dataclasses import dataclass, field

from .field import Field
from .dialect_error import DialectError, DialectErrorKind
from .diagnostic_info import DiagnosticInfo, DiagnosticInfoKind

"""
Groupes non-consommés
Pattern partagé entre extractors
SHADOWED_MATCH potentiel (statiquement détectable)
GREEDY_GROUP
"""

@dataclass(kw_only = True)
class StaticDiagnostics:
    extractors : list[Field]
    messages : list[DiagnosticInfo] = field(default_factory = list)

    def analyze(self, parse_fn : Callable) -> list[DiagnosticInfo]:
        self._group_is_not_consumed()

        return self.messages


    def _group_is_not_consumed(self):
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