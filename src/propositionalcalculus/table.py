from functools import cached_property
from .formula import Formula, Var, Const, UnaryOperator, BinaryOperator

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
    def table_line_rec(f: Formula, ass: Assign) -> tuple[list[bool], int]:
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
