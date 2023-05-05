from collections.abc import Iterator
from .formula import Formula, Var, Const, UnaryOperator, BinaryOperator


def pattern_match(
    pattern: Formula, subject: Formula
) -> Iterator[dict[Var, Formula] | None]:
    def match_inner(
        current_pattern: Formula, value: Formula, bindings: dict[Var, Formula]
    ) -> bool:
        match (current_pattern, value):
            case (Const.TRUE, Const.TRUE):
                return True
            case (Const.FALSE, Const.FALSE):
                return True
            case (Var() as v, _):
                if not v in bindings:
                    bindings[v] = value
                elif bindings[v] != value:
                    return False
                return True
            case (UnaryOperator(A), UnaryOperator(B)):
                if current_pattern.__class__ != value.__class__:
                    return False
                return match_inner(A, B, bindings)
            case (BinaryOperator(A, B), BinaryOperator(C, D)):
                if current_pattern.__class__ != value.__class__:
                    return False
                return match_inner(A, C, bindings) and match_inner(B, D, bindings)
            case _:
                return False

    for subformula in subject.traverse():
        assert isinstance(subformula, Formula)
        bindings: dict[Var, Formula] = {}
        if match_inner(pattern, subformula, bindings):
            yield bindings
        else:
            yield None


class Rule:
    def __init__(self, head: Formula, body: Formula):
        self.head = head
        self.body = body
        assert self.body.vars.issubset(
            self.head.vars
        ), "Las variables del cuerpo de la regla deben aparecer en la cabecera"

    def match(self, subject: Formula) -> Iterator[dict[Var, Formula] | None]:
        return pattern_match(self.head, subject)

    def apply(self, value: Formula) -> Formula | None:
        ...
