from typing import Tuple
from enum import Enum
from functools import cached_property


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

    @cached_property
    def vars(self) -> set['Var']:
        """ Conjunto de variables presentes en la fórmula. """
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
    def consts(self) -> set['Const']:
        """ Conjunto de constantes presentes en la fórmula. """
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

    def __len__(self) -> int:
        if isinstance(self, Var) or isinstance(self, Const):
            return 1
        elif isinstance(self, UnaryOperator):
            return 1 + len(self.f)
        elif isinstance(self, BinaryOperator):
            return 1 + len(self.left) + len(self.right)
        else:
            raise ValueError("UNREACHABLE")


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
        self._lines = None
        self._vars = None

    @property
    def vars(self):
        if self._vars is None:
            self._vars = list(self.f.vars)
            self._vars.sort(key=lambda v: v.value)
        return self._vars

    @property
    def lines(self) -> list[TableLine]:
        if self._lines is None:
            n_vars = len(self.vars)
            table: list[TableLine] = []
            for i in range(2**n_vars):
                ass_raw = format(i, f"0{n_vars}b")
                ass = {v: bool(int(ass_raw[i])) for i, v in enumerate(self.vars)}
                table.append(TableLine(self.f, ass, self.show_ass))
            return table
        return self._lines

    @property
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


def subs_imp(f: Formula) -> Formula:
    """
    Reemplaza todas las apariciones de la implicación en una fórmula mediante la
    equivalencia A→B sii ((¬A)∨B)
    """
    if isinstance(f, Var) or isinstance(f, Const):
        return f
    elif isinstance(f, Neg):
        return Neg(subs_imp(f.f))
    elif isinstance(f, And):
        return And(subs_imp(f.left), subs_imp(f.right))
    elif isinstance(f, Or):
        return Or(subs_imp(f.left), subs_imp(f.right))
    if isinstance(f, Imp):
        return Or(Neg(subs_imp(f.left)), subs_imp(f.right))
    else:
        raise ValueError("UNREACHABLE")


def simp_double_neg(f: Formula) -> Formula:
    """
    Simplifica las dobles negaciones en una fórmula
    """
    if isinstance(f, Var) or isinstance(f, Const):
        return f
    elif isinstance(f, Neg):
        if isinstance(f.f, Neg):
            return simp_double_neg(f.f.f)
        else:
            return Neg(simp_double_neg(f.f))
    elif isinstance(f, And):
        return And(simp_double_neg(f.left), simp_double_neg(f.right))
    elif isinstance(f, Or):
        return Or(simp_double_neg(f.left), simp_double_neg(f.right))
    if isinstance(f, Imp):
        return Imp(simp_double_neg(f.left), simp_double_neg(f.right))
    else:
        raise ValueError("UNREACHABLE")


def push_neg(f: Formula) -> Formula:
    """
    Mete las negaciones todo lo dentro posible de una fórmula y simplifica las
    dobles negaciones.
    """
    if isinstance(f, Var) or isinstance(f, Const):
        return f
    elif isinstance(f, Neg):
        if isinstance(f.f, Var) or isinstance(f.f, Const):
            return Neg(f.f)
        elif isinstance(f.f, Neg):
            return push_neg(f.f.f)
        elif isinstance(f.f, And):
            return Or(push_neg(Neg(f.f.left)), push_neg(Neg(f.f.right)))
        elif isinstance(f.f, Or):
            return And(push_neg(Neg(f.f.left)), push_neg(Neg(f.f.right)))
    elif isinstance(f, And):
        return And(push_neg(f.left), push_neg(f.right))
    elif isinstance(f, Or):
        return Or(push_neg(f.left), push_neg(f.right))
    if isinstance(f, Imp):
        raise ValueError("No debería haber implicaciones")
    else:
        raise ValueError("UNREACHABLE")


def distribute_or_step(f: Formula) -> Formula:
    """
    Paso en la conversión a CNF, utilizando la propiedad distributiva de la
    disyunción.
    """
    if isinstance(f, Var) or isinstance(f, Const):
        return f
    elif isinstance(f, Neg):
        return f
    elif isinstance(f, And):
        return And(distribute_or_step(f.left), distribute_or_step(f.right))
    elif isinstance(f, Or):
        if isinstance(f.left, And):
            # Distributiva de la disyunción en el primer parámetro
            return And(
                Or(distribute_or_step(f.left.left), distribute_or_step(f.right)),
                Or(distribute_or_step(f.left.right), distribute_or_step(f.right)),
            )
        elif isinstance(f.right, And):
            # Distributiva de la disyunción en el segundo parámetro
            return And(
                Or(distribute_or_step(f.left), distribute_or_step(f.right.left)),
                Or(distribute_or_step(f.left), distribute_or_step(f.right.right)),
            )
        else:
            return Or(distribute_or_step(f.left), distribute_or_step(f.right))
    if isinstance(f, Imp):
        raise ValueError("No debería haber implicaciones")
    else:
        raise ValueError("UNREACHABLE")


def distribute_or(f: Formula) -> Formula:
    """
    Aplicación sucesiva de distribute_or_step hasta que se deja de modificar la
    fórmula.
    """
    fnext = distribute_or_step(f)
    while fnext != f:
        f = fnext
        fnext = distribute_or_step(f)
    return f


def CNF(f: Formula) -> Formula:
    """
    Devuelve la Forma Normal Conjuntiva de una fórmula.
    """
    return distribute_or(push_neg(subs_imp(f)))


def CNF_list_of_sets(f: Formula) -> list[set[Formula]]:
    f = CNF(f)
    result: list[set[Formula]] = list()
    current_set: set[Formula] = set()
    i = 0
    f_str = str(f)
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


def pretty_print_CNF_list_of_sets(cnf: list[set[Formula]]) -> str:
    return "∧".join([f"({'∨'.join([ str(e) for e in list(disj)])})" for disj in cnf])


def detect_tauto_inner(formulas: set[Formula]) -> bool:
    affirmative = set()
    negative = set()
    for f in formulas:
        if isinstance(f, Neg):
            negative.add(f.f)
        else:
            affirmative.add(f)
    return len(affirmative.intersection(negative)) > 0


def detect_tauto(f: Formula) -> bool:
    cnf = CNF_list_of_sets(f)
    return all(map(detect_tauto_inner, cnf))
