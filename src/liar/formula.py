from __future__ import annotations
from enum import Enum
from functools import cached_property
from random import choice, sample

import graphviz
from graphviz.backend.rendering import pathlib


class Formula:
    def __str__(self):
        return repr(self)

    @property
    def str_polish(self) -> str:
        raise NotImplementedError()

    # @staticmethod
    # def parse_polish_rec(string: str) -> tuple[Formula, list[Formula]]:
    #     if " " in string:
    #         token, tokens = string.split(" ", 1)
    #         if token == "Neg":
    #             f, stack = Formula.parse_polish_rec(tokens)
    #             return (Neg(f), stack)
    #         elif token == "And":
    #             f1, stack = Formula.parse_polish_rec(tokens)
    #             f2 = stack.pop()
    #             return (And(f1, f2), stack)
    #         elif token == "Or":
    #             f1, stack = Formula.parse_polish_rec(tokens)
    #             f2 = stack.pop()
    #             return (Or(f1, f2), stack)
    #         elif token == "Imp":
    #             f1, stack = Formula.parse_polish_rec(tokens)
    #             f2 = stack.pop()
    #             return (Imp(f1, f2), stack)
    #         elif token == "T" or token == "F":
    #             f = Const.TRUE if token == "T" else Const.FALSE
    #             f1, stack = Formula.parse_polish_rec(tokens)
    #             return (f, [f1]+stack)
    #         else:
    #             f = Var(token)
    #             f1, stack = Formula.parse_polish_rec(tokens)
    #             return (f, [f1]+stack)
    #     else:
    #         return (None, [])

    @staticmethod
    def parse_polish(string: str) -> Formula | None:
        ...

    # def graph(self, parent_name: str ="", dot: graphviz.Graph | None = None) -> graphviz.Graph:
    #     if dot is None:
    #         dot = graphviz.Graph()
    #     else:
    #         print(dot.source)
    #     if isinstance(self, Var) or isinstance(self, Const):
    #         name = f"{parent_name}{self}"
    #         dot.node(name, f"{self}")
    #     elif isinstance(self, UnaryOperator):
    #         name = f"{parent_name}{self.__class__.__name__}"
    #         dot.node(name, self.symbol)
    #         self.f.graph(name, dot)
    #     elif isinstance(self, BinaryOperator):
    #         name = f"{parent_name}{self.__class__.__name__}"
    #         dot.node(name, self.symbol)
    #         self.left.graph(name+"l", dot)
    #         self.right.graph(name+"r",  dot)
    #     else:
    #         raise ValueError("UNREACHABLE")
    #     if parent_name:
    #        dot.edge(parent_name, name)
    #     return dot

    @cached_property
    def graph(self):
        return "graph {\n  " + "\n  ".join(self._graph_rec()) + "\n}"

    def render_graph(self, path="./graph.gv", view=True):
        filepath = pathlib.Path(path)
        filepath.write_text(self.graph, encoding="utf8")
        graphviz.render("dot", "pdf", filepath).replace("\\", "/")

    def _graph_rec(self, prefix="") -> list[str]:
        def name(f: Formula) -> str:
            match f:
                case Var() | Const():
                    return str(f)
                case UnaryOperator() | BinaryOperator():
                    return f.__class__.__name__
                case _:
                    raise ValueError(f"UNREACHABLE")

        match self:
            case Var() | Const():
                return [f"{prefix}{self} [label={self}]"]
            case UnaryOperator(f):
                prefix = f"{prefix}{name(self)}"
                future_name = f"{prefix}{name(f)}"
                return [
                    f"{prefix} -- {future_name}",
                    f"{prefix} [label={self.symbol}]",
                ] + self.f._graph_rec(prefix)
            case BinaryOperator(A, B):
                prefix = f"{prefix}{name(self)}"
                future_name_A = f"{prefix}L{name(A)}"
                future_name_B = f"{prefix}R{name(B)}"
                return (
                    [
                        f"{prefix} [label={self.symbol}]",
                        f"{prefix} -- {future_name_A}",
                        f"{prefix} -- {future_name_B}",
                    ]
                    + A._graph_rec(prefix + "L")
                    + B._graph_rec(prefix + "R")
                )
            case _:
                raise ValueError(f"UNREACHABLE")

    def __eq__(self, other):
        return str(self) == str(other)

    def __invert__(self):
        return Neg(self)

    def __and__(self, other):
        return And(self, other)

    def __or__(self, other):
        return Or(self, other)

    def __rshift__(self, other):
        return Imp(self, other)

    def __hash__(self):
        return hash(repr(self))

    def __len__(self) -> int:
        match self:
            case Var() | Const():
                return 1
            case UnaryOperator():
                return 1 + len(self.f)
            case BinaryOperator():
                return 1 + len(self.left) + len(self.right)
            case _:
                raise ValueError("UNREACHABLE")

    @staticmethod
    def random(n_vars: int, n_iters: int, include_consts: bool = False) -> Formula:
        """Generador de funciones aleatorias."""
        formulas: set[Const | Var | Neg | And | Or | Imp] = Var.generate(n_vars)
        if include_consts:
            formulas = formulas.union({Const.FALSE, Const.TRUE})
        current_formula = None
        assert n_iters > 0, "El número de iteraciones debe ser positivo"
        for _ in range(n_iters):
            option = choice(["unary", "binary"])
            if option == "unary":
                Op = choice(unary_operators)
                f = choice(list(formulas))
                current_formula = Op(f)
            elif option == "binary":
                Op = choice(binary_operators)
                f1, f2 = sample(list(formulas), 2)
                current_formula = Op(f1, f2)
            assert isinstance(current_formula, Formula)
            formulas.add(current_formula)
        assert isinstance(current_formula, Formula)
        return current_formula

    @cached_property
    def vars(self) -> set["Var"]:
        """Conjunto de variables presentes en la fórmula."""
        match self:
            case Var():
                return {self}
            case Const():
                return set()
            case UnaryOperator():
                return self.f.vars
            case BinaryOperator():
                return self.left.vars.union(self.right.vars)
            case _:
                raise ValueError("UNREACHABLE")

    @cached_property
    def consts(self) -> set["Const"]:
        """Conjunto de constantes presentes en la fórmula."""
        match self:
            case Var():
                return set()
            case Const():
                return {self}
            case UnaryOperator():
                return self.f.consts
            case BinaryOperator():
                return self.left.consts.union(self.right.consts)
            case _:
                raise ValueError("UNREACHABLE")

    def subs(self, rules: dict[Var, Formula]) -> Formula:
        # assert set(rules.keys()).issubset(self.vars)
        match self:
            case Var():
                return rules[self] if self in rules else self
            case Const():
                return self
            case UnaryOperator(A):
                return self.__class__(A.subs(rules))
            case BinaryOperator(A ,B):
                return self.__class__(A.subs(rules), B.subs(rules))
            case _:
                raise ValueError("UNREACHABLE")

    @cached_property
    def simp_double_neg(self) -> Formula:
        """
        Función equivalente en la que se han elmiminado las dobles negaciones.
        """
        match self:
            case Var() | Const():
                return self
            case Neg(Neg(f)):
                return f.simp_double_neg
            case UnaryOperator(f):
                return self.__class__(f.simp_double_neg)
            case BinaryOperator(left, right):
                return self.__class__(left.simp_double_neg, right.simp_double_neg)
            case _:
                raise ValueError("UNREACHABLE")

    @cached_property
    def subs_imp(self) -> Formula:
        """
        Función equivalente en la que se han sustituido las implicaciones
        utilizando la equivalencia A→B sii ((¬A)∨B).
        """
        match self:
            case Var() | Const():
                return self
            case UnaryOperator(f):
                return self.__class__(f.subs_imp)
            case Imp(left, right):
                return Or(Neg(left.subs_imp), right.subs_imp)
            case BinaryOperator(left, right):
                return self.__class__(left.subs_imp, right.subs_imp)
            case _:
                raise ValueError("UNREACHABLE")

    @cached_property
    def push_neg(self) -> Formula:
        """
        Función equivalente en la que se han metido las negaciones todo lo
        dentro posible, utilizando las fórmulas de De Morgan.
        También se han eliminado las dobles negaciones.
        """
        match self:
            case Var() | Const():
                return self
            case Neg(Var()) | Neg(Const()):
                return Neg(self.f)
            case Neg(Neg(f)):
                return f.push_neg
            case Neg(And(left, right)):
                return Or(Neg(left).push_neg, Neg(right).push_neg)
            case Neg(Or(left, right)):
                return And(Neg(left).push_neg, Neg(right).push_neg)
            case Neg(Imp(left, right)):
                return And(left.push_neg, Neg(right).push_neg)
            case BinaryOperator(left, right):
                return self.__class__(left.push_neg, right.push_neg)
            case _:
                raise ValueError("UNREACHABLE")

    @cached_property
    def distribute_or_step(self) -> Formula:
        """
        Función equivalente aplicando recursivamente la propiedad distributiva
        de la disyunción.

        Como la recursión solo hace una pasada por el árbol de la función es
        posible que queden términos pendientes de simplificar.
        """
        match self:
            case Var() | Const():
                return self
            case UnaryOperator(f):
                return self.__class__(f.distribute_or_step)
            case Or(And(A, B), C):
                return And(
                    Or(A.distribute_or_step, C.distribute_or_step),
                    Or(B.distribute_or_step, C.distribute_or_step),
                )
            case Or(A, And(B, C)):
                return And(
                    Or(A.distribute_or_step, B.distribute_or_step),
                    Or(A.distribute_or_step, C.distribute_or_step),
                )
            case BinaryOperator(left, right):
                return self.__class__(left.distribute_or_step, right.distribute_or_step)
            case _:
                raise ValueError("UNREACHABLE")

    @cached_property
    def distribute_or(self) -> Formula:
        """
        Función equivalente en la que se ha aplicado todas las veces posible la
        propiedad distributiva de la disyunción.
        """
        f1, f2 = self, self.distribute_or_step
        while f2 != f1:
            f1 = f2
            f2 = f1.distribute_or_step
        return f1

    @cached_property
    def simp_const_step(self) -> Formula:
        match self:
            case Var() | Const():
                return self
            case Neg(Const.TRUE):
                    return Const.FALSE
            case Neg(Const.FALSE):
                    return Const.TRUE
            case Neg(A):
                return Neg(A.simp_const_step)
            case And(Const.TRUE, B):
                return B.simp_const_step
            case And(A, Const.TRUE):
                return A.simp_const_step
            case And(Const.FALSE, _):
                return Const.FALSE
            case And(_, Const.FALSE):
                return Const.FALSE
            case Or(_, Const.TRUE):
                return Const.TRUE
            case Or(Const.TRUE, _):
                return Const.TRUE
            case Or(A, Const.FALSE):
                return A.simp_const_step
            case Or(Const.FALSE, A):
                return A.simp_const_step
            case Imp(Const.TRUE, A):
                return A.simp_const_step
            case Imp(_, Const.TRUE):
                return Const.TRUE
            case Imp(Const.FALSE, _):
                return Const.TRUE
            case Imp(A, Const.FALSE):
                return Neg(A.simp_const_step)
            case BinaryOperator(A, B):
                return self.__class__(A.simp_const_step, B.simp_const_step)
            case _:
                raise ValueError("UNREACHABLE")

    @cached_property
    def simp_const(self) -> Formula:
        f1, f2 = self, self.simp_const_step
        while f2 != f1:
            f1 = f2
            f2 = f1.simp_const_step
        return f1


    @cached_property
    def CNF(self) -> Formula:
        """
        Forma Normal Conjuntiva.

        Se calcula aplicando el siguiente algoritmo:
        - Se eliminan las implicaciones utilizando subs_imp
        - Aplicación de push_neg para empujar las negaciones hacia las raíces
          del árbol de la fórmula
        - Se aplica recursivamente la propiedad distributiva de la disyunción,
          mediante distribute_or
        """
        return self.subs_imp.push_neg.distribute_or.simp_const

    @cached_property
    def CNF_structured(self) -> list[set[Formula]]:
        self = self.CNF
        result: list[set[Formula]] = list()
        current_set: set[Formula] = set()
        i = 0
        f_str = str(self)
        while i < len(f_str):
            if f_str[i] == "¬":
                i += 1
                if f_str[i] == "T":
                    current_set.add(Const.FALSE)
                elif f_str[i] == "F":
                    current_set.add(Const.TRUE)
                else:
                    current_set.add(Neg(Var(f_str[i])))
            elif f_str[i] == "∧":
                result.append(current_set)
                current_set = set()
            elif f_str[i] == "∨" or f_str[i] == "(" or f_str[i] == ")":
                pass
            else:
                if f_str[i] == "T":
                    current_set.add(Const.TRUE)
                elif f_str[i] == "F":
                    current_set.add(Const.FALSE)
                else:
                    current_set.add(Var(f_str[i]))
            i += 1
        result.append(current_set)
        return result

    @staticmethod
    def print_CNF_structured(cnf: list[set[Formula]]) -> str:
        return "∧".join(
            [f"({'∨'.join([ str(e) for e in list(disj)])})" for disj in cnf]
        )

    @cached_property
    def is_tauto(self) -> bool:
        """Determina si la fórmula es una tautología, utilizando la CNF."""
        for l in self.CNF_structured:
            affirmative, negative = set(), set()
            for f in l:
                match f:
                    case Const.TRUE:
                        return True
                    case Const.FALSE:
                        return False
                    case Neg(f):
                        negative.add(f)
                    case Var():
                        affirmative.add(f)
                    case _:
                        raise ValueError("UNREACHABLE")
            if len(affirmative.intersection(negative)) == 0:
                return False
        return True


class UnaryOperator(Formula):
    symbol: str
    __match_args__ = ("f",)

    def __init__(self, f: Formula) -> None:
        self.f = f

    def __repr__(self):
        return f"{self.symbol}{self.f}"

    @property
    def str_polish(self) -> str:
        return f"{self.symbol} {self.f.str_polish}"

    def semantics(self, value: bool) -> bool:
        raise NotImplementedError()


class BinaryOperator(Formula):
    symbol: str
    __match_args__ = ("left", "right")

    def __init__(self, left: Formula, right: Formula):
        self.left, self.right = left, right

    def __repr__(self):
        return f"({self.left}{self.symbol}{self.right})"

    @property
    def str_polish(self) -> str:
        return f"{self.symbol} {self.left.str_polish} {self.right.str_polish}"

    def semantics(self, left_value: bool, right_value: bool) -> bool:
        raise NotImplementedError()


class Var(Formula):
    var_names = "ABCDEGHIJKLMNOPQRSVWXYZ"

    def __init__(self, name: str):
        assert name in Var.var_names, "Nombre de variable inválido"
        self.value = name

    def __repr__(self):
        return self.value

    @property
    def str_polish(self):
        return str(self)

    @staticmethod
    def generate(n: int, random: bool = False) -> set[Var]:
        """
        Función que genera una lista de variables.

        Si el parámetro random es cierto, escoje los nombres de las variables
        aleatoriamente. En caso contrario los escoje en orden alfabético.
        """
        assert n <= len(
            Var.var_names
        ), "No hay suficientes nombres de variables para escojer"
        return set(map(Var, sample(Var.var_names, n) if random else Var.var_names[0:n]))


class Const(Formula, Enum):
    FALSE = 0
    TRUE = 1

    def __repr__(self):
        return "F" if self.name == "FALSE" else "T"

    @property
    def str_polish(self):
        return str(self)


class Neg(UnaryOperator):
    symbol = "¬"

    def semantics(self, value: bool) -> bool:
        return not value


class And(BinaryOperator):
    symbol = "∧"

    def semantics(self, left_value: bool, right_value: bool) -> bool:
        return left_value and right_value


class Or(BinaryOperator):
    symbol = "∨"

    def semantics(self, left_value: bool, right_value: bool) -> bool:
        return left_value or right_value


class Imp(BinaryOperator):
    symbol = "→"

    def semantics(self, left_value: bool, right_value: bool) -> bool:
        return (not left_value) or right_value


unary_operators: list[type[Neg]] = [Neg]
binary_operators: list[type[And] | type[Or] | type[Imp]] = [And, Or, Imp]
