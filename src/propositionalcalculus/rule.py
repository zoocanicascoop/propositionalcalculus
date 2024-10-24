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
    Algoritmo de reconocimiento de patrones.

    Dado un patrón y una fórmula, este algoritmo encuentra todas las ocurrencias
    del la estructura del patrón en la fórmula y sus subfórmulas, devolviendo un
    iterador que devuelve el binding para el subárbol actual, siguiendo un
    recorrido de fórmula particular.

    Args:
        pattern: el patrón a buscar 
        subject: la fórmula en la que busca el patrón
        traverse_order: el tipo de recorrido

    Returns: 
        un iterador que devuelve el binding asociado a cada posición, si se ha encontrado el patrón, o None en caso contrario.
    """

    def _match_inner(
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
                return _match_inner(A, B, bindings)
            case (BinaryOperator(A, B), BinaryOperator(C, D)):
                if current_pattern.__class__ != value.__class__:
                    return False
                return _match_inner(A, C, bindings) and _match_inner(B, D, bindings)
            case _:
                return False

    for subformula in subject.traverse(traverse_order):
        assert isinstance(subformula, Formula)
        bindings: dict[Var, Formula] = {}
        if _match_inner(pattern, subformula, bindings):
            yield bindings
        else:
            yield None


class Rule:
    """
    Reglas de sustitución basadas en el reconocimiento de patrones.

    Estas reglas consisten de una cabecera y un cuerpo. La aplicación de la
    regla consiste en buscar todas las ocurrencias del patrón de la cabecera en
    una fórmula y sustituirlo (una o más veces) por el cuerpo de la regla.
    """

    def __init__(self, head: Formula, body: Formula):
        """ 
        Args:
            head: cabecera de la regla (patrón que se va a sustituir)
            body: cuerpo de la regla (por lo que se va a sustituir)
        """
        self.head = head
        self.body = body
        assert self.body.vars.issubset(
            self.head.vars
        ), "Las variables del cuerpo de la regla deben aparecer en la cabecera"

    def __str__(self) -> str:
        return f"{self.head} ⇒ {self.body}"

    @cached_property
    def is_imp(self) -> bool:
        """
        Determina si la regla, convertida a una implicación, es una tautología.
        """
        return (self.head >> self.body).is_tauto

    @cached_property
    def is_equiv(self) -> bool:
        """
        Determina si la cabecera de la regla es equivalente al cuerpo de la regla.
        """
        return ((self.head >> self.body) & (self.body >> self.head)).is_tauto

    @cached_property
    def inverse(self) -> Rule:
        """
        Regla inversa: regla con la cabecera y el cuerpo intercambiados.
        Se restringe el uo de esta propiedad a reglas que sean equivalencias.
        """
        assert self.is_equiv
        return Rule(self.body, self.head)

    def match(
        self, value: Formula, traverse_order: OrderType = OrderType.BREADTH_FIRST
    ) -> Iterator[dict[Var, Formula] | None]:
        """
        Búsqueda de ocurrencias del patrón de la cabecera en una fórmula dada.

        Args:
            value: fórmula en la que se busca el patrón
            traverse_order: tipo de recorrido

        Returns:
            el iterador devuelto por el proceso de reconocimiento de patrones.
        """
        return pattern_match(self.head, value, traverse_order)

    def apply(
        self,
        value: Formula,
        pos: int,
        traverse_order: OrderType = OrderType.BREADTH_FIRST,
    ) -> Formula | None:
        """
        Aplicación de la regla a una fórmula, en una posición dada.

        Args:
            value: fórmula a la que se le aplica la regla
            pos: posición en la que se aplica la regla
            traverse_order: tipo de recorrido

        Returns:
            la fórmula resultante de aplicar la regla, o None si no se ha podido aplicar.
        """
        binding = next(islice(self.match(value, traverse_order), pos, pos + 1))
        if binding is None:
            return None
        new_subformula = self.body.subs(binding)
        result = value.replace_at_pos(pos, new_subformula, traverse_order)
        return result

    def apply_first(
        self, value: Formula, traverse_order: OrderType = OrderType.BREADTH_FIRST
    ) -> Formula | None:
        """
        Aplicación de la regla a una fórmula, en la primera posición en la que
        se puede aplicar.

        Args:
            value: fórmula a la que se le aplica la regla
            traverse_order: tipo de recorrido
        Returns:
            la fórmula resultante de aplicar la regla, o None si no se ha podido aplicar.
        """
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
        Aplica la regla a una fórmula iterativamente hasta que no se pueda aplicar más.
        Para evitar bucles infinitos, se comprueba que la cabecera de la regla no
        aparezca en el cuerpo de la regla.

        Args:
            value: fórmula a la que se le aplica la regla

        Returns:
            la fórmula resultante de aplicar la regla iterativamente.
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
        """
        Utilidad para aplicar una lista de reglas a una fórmula, hasta que ya no
        se puedan aplicar más reglas.
        Dada una lista de reglas, devuelve una función que aplica todas las
        reglas a una función.
        Args:
            rules: lista de reglas
        Returns: 
            función que dada una fórmula deveulve la fórmula resultante de aplicar todas las reglas de la lista a la fórmula.
        """
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
        """
        Implementación alternativa de la función apply_list_f, que aplica las
        reglas en un orden distinto, sin utilizar apply_all.
        """
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
        """
        Interfaz alternativa para la función Rule.apply_list_f.

        En lugar de devolver una función, esta función recibe la fórmula a la que
        aplicar las reglas como parámetro.

        Args:
            rules: lista de reglas
            value: fórmula a la que aplicar las reglas

        Returns: 
            fórmula resultante de aplicar todas las reglas a la fórmula
        """
        return Rule.apply_list_f(rules)(value)


    def applications(
        self, value: Formula, traverse_order: OrderType = OrderType.BREADTH_FIRST
    ) -> list[Formula]:
        """
        Devuelve una lista con todas las fórmulas resultantes de aplicar la
        regla en todas las posiciones en las que se puede aplicar.

        Args:
            value: fórmula a la que se le aplica la regla
            traverse_order: tipo de recorrido

        Returns:
            lista de fórmulas resultantes de aplicar la regla
        """
        positions = [
            i for i, m in enumerate(self.match(value, traverse_order)) if m is not None
        ]
        return [self.apply(value, pos) for pos in positions]

    @staticmethod
    def check_cycles(rules: list[Rule]) -> bool:
        """
        Utilidad para comprobar si un conjunto de reglas tiene ciclos.

        Args:
            rules: lista de reglas

        Returns: 
            True si hay ciclos, False en caso contrario.
        """
        G = DiGraph()
        for rule in rules:
            G.add_node(rule.head)
            G.add_node(rule.body)
            G.add_edge(rule.head, rule.body)
            for ruleB in rules:
                apps = ruleB.applications(rule.body)
                for ruleC in rules:
                    if ruleC.head in apps:
                        G.add_edge(rule.body, ruleC.head)
        try:
            find_cycle(G)
        except NetworkXNoCycle:
            return False
        else:
            return True
