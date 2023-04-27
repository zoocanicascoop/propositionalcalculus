from functools import cached_property
from .formula import Formula, Var, Const, UnaryOperator, BinaryOperator


class Rule:
    def __init__(self, head: Formula, body: Formula):
        self.head = head
        self.body = body
        assert self.body.vars.issubset(
            self.head.vars
        ), "Las variables del cuerpo de la regla deben aparecer en la cabecera"

    def match(self, value: Formula) -> dict[Var, Formula] | None:
        def match_inner(
            pattern: Formula, value: Formula, bindings: dict[Var, Formula]
        ) -> bool:
            match (pattern, value):
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
                    if pattern.__class__ != value.__class__:
                        return False
                    return match_inner(A, B, bindings)
                case (BinaryOperator(A, B), BinaryOperator(C, D)):
                    if pattern.__class__ != value.__class__:
                        return False
                    return match_inner(A, C, bindings) and match_inner(B, D, bindings)
                case _:
                    return False

        bindings: dict[Var, Formula] = {}
        if match_inner(self.head, value, bindings):
            return bindings
        else:
            return None

    def apply(self, value: Formula) -> Formula | None:
        bindings = self.match(value)
        if bindings is not None:
            return self.body.subs(bindings)


class InferenceRule:
    def __init__(
        self, assumptions: Formula | tuple[Formula, ...], conclusion: Formula
    ) -> None:
        self.assumptions = (
            (assumptions,) if isinstance(assumptions, Formula) else assumptions
        )
        self.conclusion = conclusion

    @cached_property
    def is_sound(self) -> bool:
        f = Const.TRUE
        for assumption in self.assumptions:
            f = f & assumption
        f = f >> self.conclusion
        return f.is_tauto
