from __future__ import annotations
from collections.abc import Callable, Iterator
from functools import cached_property
from itertools import islice

from networkx import DiGraph, NetworkXNoCycle, find_cycle

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

    def __str__(self) -> str:
        return f"{self.head} ⇒ {self.body}"

    @cached_property
    def is_imp(self) -> bool:
        return (self.head >> self.body).is_tauto

    @cached_property
    def is_equiv(self) -> bool:
        return ((self.head >> self.body) & (self.body >> self.head)).is_tauto

    @cached_property
    def inverse(self) -> Rule:
        assert self.is_equiv
        return Rule(self.body, self.head)

    def match(
        self, value: Formula, traverse_order: OrderType = OrderType.BREADTH_FIRST
    ) -> Iterator[dict[Var, Formula] | None]:
        return pattern_match(self.head, value, traverse_order)

    def apply(
        self,
        value: Formula,
        pos: int,
        traverse_order: OrderType = OrderType.BREADTH_FIRST,
    ) -> Formula | None:
        binding = next(islice(self.match(value, traverse_order), pos, pos + 1))
        if binding is None:
            return None
        new_subformula = self.body.subs(binding)
        result = value.replace_at_pos(pos, new_subformula, traverse_order)
        return result

    def applications(
        self, value: Formula, traverse_order: OrderType = OrderType.BREADTH_FIRST
    ) -> list[Formula]:
        positions = [
            i for i, m in enumerate(self.match(value, traverse_order)) if m is not None
        ]
        return [self.apply(value, pos) for pos in positions]

    def apply_first(
        self, value: Formula, traverse_order: OrderType = OrderType.BREADTH_FIRST
    ) -> Formula | None:
        # TODO: optimizar para no hacer match dos veces
        pos = next(
            (
                pos
                for pos, binding in enumerate(self.match(value, traverse_order))
                if binding is not None
            ),
            None,
        )
        if pos is None:
            return None
        return self.apply(value, pos)

    def apply_all(self, value: Formula) -> Formula:
        """
        Apply all ocurrencies starting from the first one to the next ones.
        """
        assert (
            list(filter(lambda m: m is not None, pattern_match(self.head, self.body)))
            == []
        ), "For this algorithm to finish the rule head must not appear (match) in the body"
        while True:
            tmp = self.apply_first(value)
            if tmp:
                value = tmp
            else:
                break
        return value

    @staticmethod
    def apply_list_f(rules: list[Rule]) -> Callable[[Formula], Formula]:
        def f(value: Formula):
            result = value
            while True:
                current = result
                for rule in rules:
                    result = rule.apply_all(result)
                if result == current:
                    break
            return result

        return f

    @staticmethod
    def apply_list_f_(rules: list[Rule]) -> Callable[[Formula], Formula]:
        def f(value: Formula):
            result = value
            while True:
                current = result
                for rule in rules:
                    tmp = rule.apply_first(result)
                    if tmp:
                        print(rule)
                        result = tmp
                if result == current:
                    break
            return result

        return f

    @staticmethod
    def apply_list(rules: list[Rule], value: Formula) -> Formula:
        return Rule.apply_list_f(rules)(value)

    @staticmethod
    def check_cycles(rules: list[Rule]) -> bool:
        G = DiGraph()
        for rule in rules:
            G.add_node(rule.head)
            G.add_node(rule.body)
            G.add_edge(rule.head, rule.body)
            for ruleB in rules:
                apps = ruleB.applications(rule.body)
                for ruleC in rules:
                    if ruleC.head in apps:
                        G.add_edge(rule.body,ruleC.head  )
        try:
            find_cycle(G)
        except NetworkXNoCycle:
            return False
        else:
            return True
