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

    def graph_rec(self, prefix="") -> list[str]:
        if isinstance(self, Var) or isinstance(self, Const):
            return [f"{prefix}{self} [label={self}]"]
        elif isinstance(self, UnaryOperator):
            prefix = f"{prefix}{self.__class__.__name__}"
            if isinstance(self.f, Var) or isinstance(self.f, Const):
                future_name = f"{prefix}{self.f}"
            elif isinstance(self.f, UnaryOperator) or isinstance(self.f, UnaryOperator):
                future_name = f"{prefix}{self.__class__.__name__}"
            else:
                raise ValueError("UNREACHABLE")
            return [f"{prefix} -- {future_name}",f"{prefix} [label={self.symbol}]"] + self.f.graph_rec(prefix)
        elif isinstance(self, BinaryOperator):
            prefix = f"{prefix}{self.__class__.__name__}"
            result = [f"{prefix} [label={self.symbol}]"]
            if isinstance(self.left, Var) or isinstance(self.left, Const):
                future_name_left = f"{prefix}L{self.left}"
            elif isinstance(self.left, UnaryOperator) or isinstance(self.left, BinaryOperator):
                future_name_left = f"{prefix}L{self.__class__.__name__}"
            else:
                raise ValueError("UNREACHABLE")
            result.append(f"{prefix} -- {future_name_left}")
            result += self.left.graph_rec(prefix+"L")

            if isinstance(self.right, Var) or isinstance(self.right, Const):
                future_name_right = f"{prefix}L{self.right}"
            elif isinstance(self.right, UnaryOperator) or isinstance(self.right, BinaryOperator):
                future_name_right = f"{prefix}L{self.__class__.__name__}"
            else:
                raise ValueError("UNREACHABLE")
            result.append(f"{prefix} -- {future_name_right}")
            result += self.right.graph_rec(prefix+"L")
            return result
        else:
            raise ValueError("UNREACHABLE")

    @cached_property
    def graph(self):
        return "graph {\n  "+"\n  ".join(self.graph_rec())+"\n}"

    def render_graph(self, path="./graph.gv", view=True):
        filepath = pathlib.Path(path)
        filepath.write_text(self.graph, encoding='utf8')
        graphviz.render('dot', 'png', filepath).replace('\\', '/')

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
        if isinstance(self, Var) or isinstance(self, Const):
            return 1
        elif isinstance(self, UnaryOperator):
            return 1 + len(self.f)
        elif isinstance(self, BinaryOperator):
            return 1 + len(self.left) + len(self.right)
        else:
            raise ValueError("UNREACHABLE")

    @staticmethod
    def random(n_vars: int, n_iters: int) -> Formula:
        formulas: set[Var | Neg | And | Or | Imp] = Var.generate(n_vars)
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
        if isinstance(self, Var):
            return {self}
        elif isinstance(self, Const):
            return set()
        elif isinstance(self, UnaryOperator):
            return self.f.vars
        elif isinstance(self, BinaryOperator):
            return self.left.vars.union(self.right.vars)
        else:
            raise ValueError("UNREACHABLE")

    @cached_property
    def consts(self) -> set["Const"]:
        """Conjunto de constantes presentes en la fórmula."""
        if isinstance(self, Var):
            return set()
        elif isinstance(self, Const):
            return {self}
        elif isinstance(self, UnaryOperator):
            return self.f.consts
        elif isinstance(self, BinaryOperator):
            return self.left.consts.union(self.right.consts)
        else:
            raise ValueError("UNREACHABLE")

    @cached_property
    def simp_double_neg(self) -> Formula:
        """
        Función equivalente en la que se han elmiminado las dobles negaciones.
        """
        if isinstance(self, Var) or isinstance(self, Const):
            return self
        elif isinstance(self, Neg):
            if isinstance(self.f, Neg):
                return self.f.f.simp_double_neg
            else:
                return Neg(self.f.simp_double_neg)
        elif isinstance(self, And):
            return And(self.left.simp_double_neg, self.right.simp_double_neg)
        elif isinstance(self, Or):
            return Or(self.left.simp_double_neg, self.right.simp_double_neg)
        if isinstance(self, Imp):
            return Imp(self.left.simp_double_neg, self.right.simp_double_neg)
        else:
            raise ValueError("UNREACHABLE")

    @cached_property
    def subs_imp(self) -> Formula:
        """
        Función equivalente en la que se han sustituido las implicaciones
        utilizando la equivalencia A→B sii ((¬A)∨B).
        """
        if isinstance(self, Var) or isinstance(self, Const):
            return self
        elif isinstance(self, Neg):
            return Neg(self.f.subs_imp)
        elif isinstance(self, And):
            return And(self.left.subs_imp, self.right.subs_imp)
        elif isinstance(self, Or):
            return Or(self.left.subs_imp, self.right.subs_imp)
        if isinstance(self, Imp):
            return Or(Neg(self.left.subs_imp), self.right.subs_imp)
        else:
            raise ValueError("UNREACHABLE")

    @cached_property
    def push_neg(self) -> Formula:
        """
        Función equivalente en la que se han metido las negaciones todo lo
        dentro posible, utilizando las fórmulas de De Morgan.
        También se han eliminado las dobles negaciones.
        """
        if isinstance(self, Var) or isinstance(self, Const):
            return self
        elif isinstance(self, Neg):
            if isinstance(self.f, Var) or isinstance(self.f, Const):
                return Neg(self.f)
            elif isinstance(self.f, Neg):
                return self.f.f.push_neg
            elif isinstance(self.f, And):
                return Or(Neg(self.f.left).push_neg, Neg(self.f.right).push_neg)
            elif isinstance(self.f, Or):
                return And(Neg(self.f.left).push_neg, Neg(self.f.right).push_neg)
            elif isinstance(self.f, Imp):
                return And(self.f.left.push_neg, Neg(self.f.right).push_neg)
        elif isinstance(self, BinaryOperator):
            return self.__class__(self.left.push_neg, self.right.push_neg)
        else:
            raise ValueError(f"UNREACHABLE")

    @cached_property
    def distribute_or_step(self) -> Formula:
        """
        Función equivalente aplicando recursivamente la propiedad distributiva
        de la disyunción.

        Como la recursión solo hace una pasada por el árbol de la función es
        posible que queden términos pendientes de simplificar.
        """
        if isinstance(self, Var) or isinstance(self, Const):
            return self
        elif isinstance(self, Neg):
            return self
        elif isinstance(self, And):
            return And(self.left.distribute_or_step, self.right.distribute_or_step)
        elif isinstance(self, Or):
            if isinstance(self.left, And):
                # Propiedad distributiva de la disyunción en el primer parámetro
                return And(
                    Or(
                        self.left.left.distribute_or_step, self.right.distribute_or_step
                    ),
                    Or(
                        self.left.right.distribute_or_step,
                        self.right.distribute_or_step,
                    ),
                )
            elif isinstance(self.right, And):
                # Propiedad distributiva de la disyunción en el segundo parámetro
                return And(
                    Or(
                        self.left.distribute_or_step, self.right.left.distribute_or_step
                    ),
                    Or(
                        self.left.distribute_or_step,
                        self.right.right.distribute_or_step,
                    ),
                )
            else:
                return Or(self.left.distribute_or_step, self.right.distribute_or_step)
        if isinstance(self, Imp):
            return Imp(self.left.distribute_or_step, self.right.distribute_or_step)
        else:
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
        return self.subs_imp.push_neg.distribute_or

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
                if isinstance(f, Neg):
                    negative.add(f.f)
                else:
                    affirmative.add(f)
            if len(affirmative.intersection(negative)) == 0:
                return False
        return True


class UnaryOperator(Formula):
    symbol: str

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