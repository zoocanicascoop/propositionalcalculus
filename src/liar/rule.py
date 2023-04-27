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
            print(f"{pattern  = }")
            print(f"{value    = }")
            print(f"{bindings = }")
            match (pattern, value):
                case (Const.TRUE, Const.TRUE):
                    print("case (Const.TRUE, Const.TRUE):")
                    input("\n --- Press ENTER to continue ---\n")
                    return True
                case (Const.FALSE, Const.FALSE):
                    print("case (Const.FALSE, Const.FALSE):")
                    input("\n --- Press ENTER to continue ---\n")
                    return True
                case (Var() as v, _):
                    print("case (Var() as v, _):")
                    input("\n --- Press ENTER to continue ---\n")
                    if not v in bindings:
                        bindings[v] = value
                    elif bindings[v] != value:
                        return False
                    return True
                case (UnaryOperator(A), UnaryOperator(B)):
                    print("case (UnaryOperator(A), UnaryOperator(B)):")
                    input("\n --- Press ENTER to continue ---\n")
                    if pattern.__class__ != value.__class__:
                        return False
                    return match_inner(A, B, bindings)
                case (BinaryOperator(A, B), BinaryOperator(C, D)):
                    print("case (BinaryOperator(A, B), BinaryOperator(C, D)):")
                    input("\n --- Press ENTER to continue ---\n")
                    if pattern.__class__ != value.__class__:
                        return False
                    return match_inner(A, C, bindings) and match_inner(B, D, bindings)
                case _:
                    print("case _:")
                    input("\n --- Press ENTER to continue ---\n")
                    return False

        bindings: dict[Var, Formula] = {}
        if match_inner(self.head, value, bindings):
            print(f"Returning {bindings = }")
            return bindings
        else:
            print("Returning None")
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
