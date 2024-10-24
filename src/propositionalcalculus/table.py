from functools import cached_property

from rich.table import Table as rTable

from .formula import BinaryOperator, Const, Formula, UnaryOperator, Var

# Asignación semántica de variables. A cada variable le corresponde un booleano.
Assign = dict[Var, bool]


def sort_vars(vars: set[Var]) -> list[Var]:
    """Ordena un conjunto de variables alfabéticamente"""
    result = list(vars)
    result.sort(key=lambda v: v.value)
    return result


class TableLine:
    """
    Representa una línea de la tabla de verdad de una fórmula.
    La línea está determinada por una asignación de variables.
    """

    def __init__(self, f: Formula, ass: Assign, show_ass=True) -> None:
        """
        Args:
            f: Fórmula de la línea
            ass: Asignación de la línea
        """
        self.f = f
        self.ass = ass
        self.show_ass = show_ass
        self._table_line_rec_result = None

    @property
    def line(self) -> list[bool]:
        if self._table_line_rec_result is None:
            self._table_line_rec_result = TableLine._table_line_rec(self.f, self.ass)
        return self._table_line_rec_result[0]

    @property
    def repr_pos(self) -> int:
        """
        Índice del elemento principal de la línea (elemento correspondiente a la 
        raíz del árbol de la fórmula).
        """
        if self._table_line_rec_result is None:
            self._table_line_rec_result = TableLine._table_line_rec(self.f, self.ass)
        return self._table_line_rec_result[1]

    @property
    def repr(self) -> bool:
        """
        Valor de verdad del elemento principal de la línea.
        """
        return self.line[self.repr_pos]

    def __str__(self) -> str:
        """
        Representación en string de la línea, separando los valores por tabs.
        """
        vars = sort_vars(set(self.ass.keys()))
        result = (
            "\t".join([str(int(self.ass[v])) for v in vars]) if self.show_ass else ""
        )
        for i, e in enumerate(self.line):
            if i == self.repr_pos:
                result += f"{1 if e else 0}\t"
            else:
                result += f"{1 if e else 0}\t"
        return result

    def rich_row(self):
        """
        Representación de la línea en formato tabla, utilizando la librería
        rich.
        """
        return [str(int(self.ass[v])) for v in sort_vars(set(self.ass.keys()))] + [
            f"{1 if e else 0}" for e in self.line
        ]

    @staticmethod
    def _table_line_rec(f: Formula, ass: Assign) -> tuple[list[bool], int]:
        assert f.vars.issubset(set(ass.keys())), "La asignación no es correcta"
        if isinstance(f, Var):
            return ([ass[f]], 0)
        elif isinstance(f, Const):
            return ([bool(f.value)], 0)
        elif isinstance(f, UnaryOperator):
            line, pos = TableLine._table_line_rec(f.f, ass)
            value = f.semantics(line[pos])
            return ([value] + line, 0)
        elif isinstance(f, BinaryOperator):
            line1, pos1 = TableLine._table_line_rec(f.left, ass)
            line2, pos2 = TableLine._table_line_rec(f.right, ass)
            value = f.semantics(line1[pos1], line2[pos2])
            return (line1 + [value] + line2, len(line1))
        else:
            raise ValueError("UNREACHABLE")


class Table:
    """
    Tabla de verdad de una fórmula
    """
    def __init__(self, f: Formula, show_ass=True) -> None:
        self.f = f
        self.show_ass = show_ass

    @cached_property
    def vars(self) -> list[Var]:
        """
        Variables de la fórmula ordenadas alfabéticamente.
        """
        return sort_vars(self.f.vars)

    @cached_property
    def lines(self) -> list[TableLine]:
        """
        Líneas de la tabla de verdad.
        TODO: posibilidad de elegir el orden de las asignaciones.
        """
        n_vars = len(self.vars)
        table: list[TableLine] = []
        for i in range(2**n_vars):
            ass_raw = format(i, f"0{n_vars}b")
            ass = {v: bool(int(ass_raw[i])) for i, v in enumerate(self.vars)}
            table.append(TableLine(self.f, ass, self.show_ass))
        return table

    @cached_property
    def truth_list(self) -> list[bool]:
        """
        Columna principal de la tabla de verdad, correspondiente al elemento en
        la raíz del árbol de la fórmula. Esta es la columna que determina el
        valor de verdad de la fórmula.
        """
        return [line.repr for line in self.lines]

    def __str__(self) -> str:
        """
        Representación en string de la fórmula, separando las columnas con tabs.
        """
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

    def rich(self):
        """
        Representación en formato tabla utilizando la librería rich.
        """
        t = rTable()
        current_header = ""
        for var in self.vars:
            t.add_column(f"[green]{var}", style="green")
        for char in str(self.f):
            if char in "()":
                current_header += char
            else:
                current_header += char
                t.add_column(current_header)
                current_header = ""
        self.lines[0].repr_pos
        for line in self.lines:
            t.add_row(*line.rich_row())
        return t


def is_tauto(f: Formula):
    """
    Función que determina si una fórmula es una tautología utilizando la tabla 
    de verdad.
    """
    return all(Table(f).truth_list)
