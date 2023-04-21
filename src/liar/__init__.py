from __future__ import annotations
from typing import Tuple
from enum import Enum
from functools import cache, cached_property


class Formula:
    def __str__(self):
        return repr(self)

    def str_polish(self):
        raise NotImplementedError()

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
        elif isinstance(self, And):
            return And(self.left.push_neg, self.right.push_neg)
        elif isinstance(self, Or):
            return Or(self.left.push_neg, self.right.push_neg)
        if isinstance(self, Imp):
            return And(self.left.push_neg, Neg(self.right).push_neg)
        else:
            raise ValueError("UNREACHABLE")

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

    def semantics(self, value: bool) -> bool:
        raise NotImplementedError()


class BinaryOperator(Formula):
    symbol: str

    def __init__(self, left: Formula, right: Formula):
        self.left, self.right = left, right

    def __repr__(self):
        return f"({self.left}{self.symbol}{self.right})"

    def semantics(self, left_value: bool, right_value: bool) -> bool:
        raise NotImplementedError()


class Var(Formula):
    def __init__(self, value: str):
        assert value.isupper(), "Las variables se representan con mayúsculas"
        assert len(value) == 1, "Las variables tienen que tener longitud uno"
        assert (
            value != "T" and value != "F"
        ), "Las variables no pueden ser T ni F puesto que son constantes"
        self.value = value

    def __repr__(self):
        return self.value


class Const(Formula, Enum):
    FALSE = 0
    TRUE = 1

    def __repr__(self):
        return "F" if self.name == "FALSE" else "T"


class Neg(UnaryOperator):
    symbol = "¬"

    def semantics(self, value: bool) -> bool:
        return not value


unary_operators = [Neg]


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


binary_operators = [And, Or, Imp]

Assign = dict[Var, bool]


def sort_vars(vars: set[Var]) -> list[Var]:
    result = list(vars)
    result.sort(key=lambda v: v.value)
    return result


def format_ass(ass: Assign) -> str:
    vars = sort_vars(set(ass.keys()))
    return "\t".join([str(int(ass[v])) for v in vars])


class TableLine:
    def __init__(self, f: Formula, ass: Assign, show_ass=True) -> None:
        self.f = f
        self.ass = ass
        self.show_ass = show_ass
        self._table_line_rec_result = None

    @property
    def line(self):
        if self._table_line_rec_result is None:
            self._table_line_rec_result = TableLine.table_line_rec(self.f, self.ass)
        return self._table_line_rec_result[0]

    @property
    def repr_pos(self):
        if self._table_line_rec_result is None:
            self._table_line_rec_result = TableLine.table_line_rec(self.f, self.ass)
        return self._table_line_rec_result[1]

    @property
    def repr(self):
        return self.line[self.repr_pos]

    def __str__(self) -> str:
        result = f"\033[92m{format_ass(self.ass)}\033[0m\t" if self.show_ass else ""
        for i, e in enumerate(self.line):
            if i == self.repr_pos:
                result += f"\033[91m{1 if e else 0}\033[0m\t"
            else:
                result += f"{1 if e else 0}\t"
        return result

    @staticmethod
    def table_line_rec(f: Formula, ass: Assign) -> Tuple[list[bool], int]:
        assert f.vars.issubset(set(ass.keys())), "La asignación no es correcta"
        if isinstance(f, Var):
            return ([ass[f]], 0)
        elif isinstance(f, Const):
            return ([bool(f.value)], 0)
        elif isinstance(f, UnaryOperator):
            line, pos = TableLine.table_line_rec(f.f, ass)
            value = f.semantics(line[pos])
            return ([value] + line, 0)
        elif isinstance(f, BinaryOperator):
            line1, pos1 = TableLine.table_line_rec(f.left, ass)
            line2, pos2 = TableLine.table_line_rec(f.right, ass)
            value = f.semantics(line1[pos1], line2[pos2])
            return (line1 + [value] + line2, len(line1))
        else:
            raise ValueError("UNREACHABLE")


class Table:
    def __init__(self, f: Formula, show_ass=True) -> None:
        self.f = f
        self.show_ass = show_ass

    @cached_property
    def vars(self):
        result = list(self.f.vars)
        result.sort(key=lambda v: v.value)
        return result

    @cached_property
    def lines(self) -> list[TableLine]:
        n_vars = len(self.vars)
        table: list[TableLine] = []
        for i in range(2**n_vars):
            ass_raw = format(i, f"0{n_vars}b")
            ass = {v: bool(int(ass_raw[i])) for i, v in enumerate(self.vars)}
            table.append(TableLine(self.f, ass, self.show_ass))
        return table

    @cached_property
    def truth_list(self) -> list[bool]:
        return [line.repr for line in self.lines]

    def __str__(self) -> str:
        result = "\t".join([str(v) for v in self.vars]) + "\t"
        for char in str(self.f):
            if char in ["(", ")"]:
                result += char
            else:
                result += char + "\t"
        result += "\n"
        for line in self.lines:
            result += f"{line}\n"
        return result


def is_tauto(f: Formula):
    return all(Table(f).truth_list)


def print_CNF_structured(cnf: list[set[Formula]]) -> str:
    return "∧".join([f"({'∨'.join([ str(e) for e in list(disj)])})" for disj in cnf])
