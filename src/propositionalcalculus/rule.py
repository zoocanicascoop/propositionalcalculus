from collections.abc import Iterator
from .formula import Formula, Var, Const, UnaryOperator, BinaryOperator, OrderType


def pattern_match(
    pattern: Formula,
    subject: Formula,
    traverse_order: OrderType = OrderType.BREADTH_FIRST,
) -> Iterator[dict[Var, Formula] | None]:
    """
    Pattern matching algorithm.

    Given a pattern and a formula, this algorithm finds all occurrencies of the
    pattern structure in the formula and subformulas, returning an iterator that
    returns the binding for the current subtree, following a particular
    traversal order.

    :pattern: the pattern formula
    :subject: the subject formula on which to search the pattern
    :traverse_order: the tree order traversal type
    """

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

    for subformula in subject.traverse(traverse_order):
        assert isinstance(subformula, Formula)
        bindings: dict[Var, Formula] = {}
        if match_inner(pattern, subformula, bindings):
            yield bindings
        else:
            yield None


class Rule:
    """
    Class for defining substitution rules based on pattern matching.

    """

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
