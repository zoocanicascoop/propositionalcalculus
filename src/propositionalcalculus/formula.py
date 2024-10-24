from __future__ import annotations
from collections.abc import Iterable, Iterator
from enum import Enum
from functools import cached_property
from random import choice, randint, sample

# Definición de tipo Binding. Un binding es una asignación de variables a fórmulas.
Binding = dict["Var", "Formula"]


def merge_bindings(a: Binding, b: Binding) -> Binding | None:
    """
    Mezcla dos bindings.

    Si ambas combinaciones contienen la misma clave con valores diferentes, se
    devuelve None en lugar del binding mezclado (equivalente a un error).

    :param a: binding 
    :param b: binding 
    :return: nuevo binding en caso de que no haya conflictos. None en otro caso.
    """
    for key in a.keys():
        if key in b and a[key] != b[key]:
            return None
    return a | b


class OrderType(Enum):
    """Tipos de orden para recorrer un árbol"""
    PREORDER = 0
    BREADTH_FIRST = 1


class Formula:
    """
    Representación de fórmulas proposicionales.

    Esta clase no está entendida para ser utilizada directamente, salvo por los
    métodos estáticos de generación de fórmulas aleatorias o a partir de una
    representación en string.

    La definición recursiva de las fórmulas está implementada en este módulo
    mediante la dependencia de clases entre esta clase, Formula, y:
    - Clases Var y Const (casos base de la definición recursiva)
    - Clase Not (operador unario)
    - Clases And, Or e Imp (operadores binarios)

    Los operadores tienen como parámetros de sus constructures otras fórmulas.
    Aquí es dónde se encuentra esta recursividad.
    """

    def __repr__(self):
        """
        Representación en string de la fórmula. Las clases que heredan de
        Formula deben implementar esta función.
        """
        raise NotImplementedError()

    @property
    def str_polish(self) -> str:
        """
        Representación en notación polaca. Propiedad implementada por las clases
        que heredan de Formula.
        """
        raise NotImplementedError()

    @staticmethod
    def parse_polish(string: str, stack: list[Formula] = []) -> Formula | None:
        """
        Dada una string de una fórmula en notación polaca, construye y devuelve 
        la fórmula correspondiente.
        """
        string = string.replace(" ", "")
        if len(string) == 0:
            return stack.pop()
        match string[-1]:
            case Neg.symbol:
                assert len(stack) >= 1
                f = stack.pop()
                stack.append(Neg(f))
                return Formula.parse_polish(string[0:-1], stack)
            case And.symbol:
                assert len(stack) >= 2
                A = stack.pop()
                B = stack.pop()
                stack.append(And(A, B))
            case Or.symbol:
                assert len(stack) >= 2
                A = stack.pop()
                B = stack.pop()
                stack.append(Or(A, B))
            case Imp.symbol:
                assert len(stack) >= 2
                A = stack.pop()
                B = stack.pop()
                stack.append(Imp(A, B))
            case "T":
                stack.append(Const.TRUE)
            case "F":
                stack.append(Const.FALSE)
            case _ as c:
                assert c in Var.var_names
                stack.append(Var(c))
        return Formula.parse_polish(string[0:-1], stack)

    @cached_property
    def graph(self):
        """
        Código fuente de la representación del árbol de la fórmula en Graphviz.

        """
        return "graph {\n  " + "\n  ".join(self._graph_rec()) + "\n}"

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

    def render_graph(self, path="./graph.gv"):
        """
        Utilidad para llamar a graphviz y renderizar el árbol de la fórmula.
        Se generarán dos ficheros: uno con el código graphviz y otro con la
        renderización en pdf.
        :param path: ruta donde se guardará el fichero con el código graphviz.
        """
        import graphviz
        from graphviz.backend.rendering import pathlib

        filepath = pathlib.Path(path)
        filepath.write_text(self.graph, encoding="utf8")
        graphviz.render("dot", "pdf", filepath).replace("\\", "/")

    def __eq__(self, other):
        """Dos fórmulas son iguales si su representación en string es igual."""
        return str(self) == str(other)

    def __invert__(self):
        """Override del operador ~ para la negación."""
        return Neg(self)

    def __and__(self, other):
        """Override del operador & para la conjunción."""
        return And(self, other)

    def __or__(self, other):
        """Override del operador | para la disyunción."""
        return Or(self, other)

    def __rshift__(self, other):
        """Override del operador >> para la implicación."""
        return Imp(self, other)

    def __hash__(self):
        """El hash de una fórmula es el hash de su representación en string."""
        return hash(repr(self))

    def __len__(self) -> int:
        """La longitud de una fórmula es el número de nodos en su árbol."""
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
    def random(n_vars: int, max_depth: int, include_consts: bool = False) -> Formula:
        """
        Generador de fórmulas aleatorias, en base a Formula.random_polish.
        Esta función es un wrapper de Formula.parse_polish, en el que
        posteriormente a la generación aleatoria, se convierte la
        representación en una fórmula utilizando Formula.parse_polish.
        """
        f = Formula.parse_polish(
            Formula.random_polish(n_vars, max_depth, include_consts)
        )
        assert isinstance(f, Formula)
        return f

    @staticmethod
    def random_polish(n_vars: int, max_depth: int, include_consts: bool = False) -> str:
        """
        Generador aleatorio de representaciones de fórmulas en notación polaca.

        :n_vars: número máximo de variables que incluir
        :max_depth: profundidad máxima del árbol de la fórmula
        :include_consts: si se incluyen las constantes T y F en la fórmula.
        :return: representación en notación polaca de la fórmula generada.
        """
        assert max_depth >= 1
        if max_depth == 1:
            if include_consts and randint(0, 1) == 0:
                return choice(["T", "F"])
            return str(choice(Var.generate(n_vars)))
        else:
            f_ = lambda: Formula.random_polish(
                n_vars, randint(1, max_depth - 1), include_consts
            )
            match randint(0, 3):
                case 0:
                    return f"¬ {f_()}"
                case 1:
                    return f"∧ {f_()} {f_()}"
                case 2:
                    return f"∨ {f_()} {f_()}"
                case 3:
                    return f"→ {f_()} {f_()}"
                case _:
                    raise ValueError("UNREACHABLE")

    @cached_property
    def vars(self) -> set["Var"]:
        """Conjunto de variables de una fórmula."""
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
        """Conjuento de constantes de una fórmula."""
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

    def subs(self, binding: Binding) -> Formula:
        """
        Dado un binding, sustituye las variables de la fórmula por las fórmulas
        correspondientes en el binding.

        :binding: el binding a aplicar en la sustitución.
        :return: la nueva fórmula en la que se han sustituido las variables.
        """
        match self:
            case Var():
                return binding[self] if self in binding else self
            case Const():
                return self
            case UnaryOperator(A):
                return self.__class__(A.subs(binding))
            case BinaryOperator(A, B):
                return self.__class__(A.subs(binding), B.subs(binding))
            case _:
                raise ValueError("UNREACHABLE")

    def traverse(
        self, order_type: OrderType = OrderType.BREADTH_FIRST
    ) -> Iterator[Formula]:
        """Recorre la fórmula siguiendo un orden determinado."""
        match order_type:
            case OrderType.PREORDER:
                return self.traverse_preorder()
            case OrderType.BREADTH_FIRST:
                return self.traverse_breadth()

    def traverse_preorder(self) -> Iterator[Formula]:
        """Recorre la fórmula en preorden."""
        match self:
            case Var() | Const():
                yield self
            case UnaryOperator(A):
                yield self
                yield from A.traverse_preorder()
            case BinaryOperator(A, B):
                yield self
                yield from A.traverse_preorder()
                yield from B.traverse_preorder()

    def traverse_breadth(self) -> Iterator[Formula]:
        """Recorre la fórmula en el orden de anchura primero."""
        queue = [self]
        while len(queue) > 0:
            v = queue.pop()
            yield v
            match v:
                case Var() | Const():
                    pass
                case UnaryOperator(A):
                    queue.insert(0, A)
                case BinaryOperator(A, B):
                    queue.insert(0, A)
                    queue.insert(0, B)

    @staticmethod
    def from_traversal_breadth_first(traversal: Iterable[Formula]) -> Formula:
        """Construye una fórmula a partir de un recorrido en anchura primero."""
        traversal = list(traversal)
        assert len(traversal) > 0
        queue = []
        v: Formula = Const.TRUE  # for type checking
        while len(traversal) > 0:
            v = traversal.pop()
            match v:
                case Var() | Const():
                    queue.append(v)
                case UnaryOperator():
                    f = queue.pop(0)
                    queue.append(v.__class__(f))
                case BinaryOperator():
                    right = queue.pop(0)
                    left = queue.pop(0)
                    queue.append(v.__class__(left, right))
        return queue.pop()

    def replace_at_pos(
        self, pos: int, f: Formula, order_type: OrderType = OrderType.BREADTH_FIRST
    ) -> Formula:
        """
        Reemplaza la fórmula en una posición determinada por otra fórmula.

        :param pos: posición en la que se va a reemplazar la fórmula.
        :param f: fórmula por la que se va a reemplazar.
        :param order_type: tipo de orden en el que se va a recorrer la fórmula.

        :return: la fórmula con la sustitución realizada.
        """
        assert pos < len(self)
        match order_type:
            case OrderType.PREORDER:
                return self.replace_at_pos_preorder(pos, f)
            case OrderType.BREADTH_FIRST:
                return self.replace_at_pos_breadth(pos, f)

    def replace_at_pos_preorder(
        self, pos: int, f: Formula, current_pos: int = 0
    ) -> Formula:
        """
        Reemplaza la fórmula en una posición determinada por otra fórmula, 
        siguiendo el orden de preorden.
        """
        if current_pos == pos:
            return f
        match self:
            case Var() | Const():
                return self
            case UnaryOperator(A):
                return self.__class__(
                    A.replace_at_pos_preorder(pos, f, current_pos + 1)
                )
            case BinaryOperator(A, B):
                left = A.replace_at_pos_preorder(pos, f, current_pos + 1)
                right = B.replace_at_pos_preorder(pos, f, current_pos + 1 + len(left))
                return self.__class__(left, right)
            case _:
                raise ValueError("UNREACHABLE")

    def replace_at_pos_breadth(self, pos: int, f: Formula) -> Formula:
        """
        Reemplaza la fórmula en una posición determinada por otra fórmula, 
        siguiendo el orden de anchura primero.
        """
        queue = [self]
        traversal = []
        i = 0
        while len(queue) > 0:
            v = queue.pop()
            if pos == i:
                queue.append(f)
            else:
                traversal.append(v)
                match v:
                    case Var() | Const():
                        pass
                    case UnaryOperator(A):
                        queue.insert(0, A)
                    case BinaryOperator(A, B):
                        queue.insert(0, A)
                        queue.insert(0, B)
            i += 1
        return Formula.from_traversal_breadth_first(traversal)

    @cached_property
    def simp_double_neg(self) -> Formula:
        """
        Fórmula equivalente en la que se han eliminado las dobles negaciones.
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
        Fórula equivalente en la que se han eliminado las implicaciones,
        mediante la equivalencia A → B iff ¬A ∨ B.
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
        Fórmula eqiuvalente en la que se han empujado todas las negaciones hacia
        abajo en el árbol de la fórmula, utilizando las fórmulas de De Morgan.
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
    def distribute_or(self) -> Formula:
        """
        Fórmula equivalente en la que se ha aplicado la propiedad distributiva
        de la disyunción.
        """
        f1, f2 = self, self._distribute_or_step
        while f2 != f1:
            f1 = f2
            f2 = f1._distribute_or_step
        return f1

    @cached_property
    def _distribute_or_step(self) -> Formula:
        match self:
            case Var() | Const():
                return self
            case UnaryOperator(f):
                return self.__class__(f._distribute_or_step)
            case Or(And(A, B), C):
                return And(
                    Or(A._distribute_or_step, C._distribute_or_step),
                    Or(B._distribute_or_step, C._distribute_or_step),
                )
            case Or(A, And(B, C)):
                return And(
                    Or(A._distribute_or_step, B._distribute_or_step),
                    Or(A._distribute_or_step, C._distribute_or_step),
                )
            case BinaryOperator(left, right):
                return self.__class__(
                    left._distribute_or_step, right._distribute_or_step
                )
            case _:
                raise ValueError("UNREACHABLE")

    @cached_property
    def simp_const(self) -> Formula:
        """
        Fórmula equivalente en la que se han eliminado las constantes
        redundantes y simplificado las negaciones de constantes.
        """
        f1, f2 = self, self._simp_const_step
        while f2 != f1:
            f1 = f2
            f2 = f1._simp_const_step
        return f1

    @cached_property
    def _simp_const_step(self) -> Formula:
        match self:
            case Var() | Const():
                return self
            case Neg(Const.TRUE):
                return Const.FALSE
            case Neg(Const.FALSE):
                return Const.TRUE
            case Neg(A):
                return Neg(A._simp_const_step)
            case And(Const.TRUE, B):
                return B._simp_const_step
            case And(A, Const.TRUE):
                return A._simp_const_step
            case And(Const.FALSE, _):
                return Const.FALSE
            case And(_, Const.FALSE):
                return Const.FALSE
            case Or(_, Const.TRUE):
                return Const.TRUE
            case Or(Const.TRUE, _):
                return Const.TRUE
            case Or(A, Const.FALSE):
                return A._simp_const_step
            case Or(Const.FALSE, A):
                return A._simp_const_step
            case Imp(Const.TRUE, A):
                return A._simp_const_step
            case Imp(_, Const.TRUE):
                return Const.TRUE
            case Imp(Const.FALSE, _):
                return Const.TRUE
            case Imp(A, Const.FALSE):
                return Neg(A._simp_const_step)
            case BinaryOperator(A, B):
                return self.__class__(A._simp_const_step, B._simp_const_step)
            case _:
                raise ValueError("UNREACHABLE")

    @cached_property
    def CNF(self) -> Formula:
        """
        Forma normal conjuntiva de la fórmula.

        Se calcula aplicando de forma secuencial las siguientes equivalencias:
        - ee eliminan todas las implicaciones con subs_imp,
        - se empujan todas las negaciones hacia abajo en el árbol de la fórmula
          utilizando push_neg,
        - se aplica la propiedad distributiva de la disyunción con distribute_or,
        - se eliminan las constantes redundantes con simp_const.
        """
        return self.subs_imp.push_neg.distribute_or.simp_const

    @cached_property
    def CNF_structured(self) -> list[set[Neg | Var | Const]]:
        """
        Versión estructurada de la CNF.

        :return: lista de conjuntos de fórmulas simples (negaciones de variables,
            variables o constantes).
        """
        self = self.CNF
        result: list[set[Neg | Var | Const]] = list()
        current_set: set[Neg | Var | Const] = set()
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
        """
        Función de utilidad para imprimir una fórmula a partir de su CNF 
        estructurada.
        """
        return "∧".join(
            [f"({'∨'.join([ str(e) for e in list(disj)])})" for disj in cnf]
        )

    @cached_property
    def is_tauto(self) -> bool:
        """
        Determina si una fórmula es una tautología en base a su CNF.
        """
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

# Tipo auxiliar para representar una fórmula o una lista de fórmulas.
Formulas = Formula | list[Formula]


def formulas_to_list(fs: Formulas) -> list[Formula]:
    """Convierte una fórmula o una lista de fórmulas en una lista de fórmulas."""
    return [fs] if isinstance(fs, Formula) else fs


class UnaryOperator(Formula):
    """
    Los operadores unarios son aquellos que tienen una única fórmula como 
    argumento.
    """
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
    """
    Los operadores binarios son aquellos que tienen dos fórmulas como argumento.
    """
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
    """
    Las variables son fórmulas simples, representadas por una letra, que podrá
    tomar valores semánticos de verdadero o falso.
    """
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
    def generate(n: int, random: bool = False) -> list[Var]:
        """
        Función que genera una lista de variables.

        Si el parámetro random es cierto, escoje los nombres de las variables
        aleatoriamente. En caso contrario los escoje en orden alfabético.
        """
        assert n <= len(
            Var.var_names
        ), "No hay suficientes nombres de variables para escojer"
        return list(
            map(Var, sample(Var.var_names, n) if random else Var.var_names[0:n])
        )


class Const(Formula, Enum):
    """
    Las constantes son fórmulas simples que representan valores semánticos fijos
    de verdadero o falso.
    """
    FALSE = 0
    TRUE = 1

    def __repr__(self):
        return "F" if self.name == "FALSE" else "T"

    @property
    def str_polish(self):
        return str(self)


class Neg(UnaryOperator):
    """
    Neg es el operador unario de negación.
    """
    symbol = "¬"

    def semantics(self, value: bool) -> bool:
        return not value


class And(BinaryOperator):
    """
    And es el operador binario de conjunción.
    """
    symbol = "∧"

    def semantics(self, left_value: bool, right_value: bool) -> bool:
        return left_value and right_value


class Or(BinaryOperator):
    """ 
    Or es el operador binario de disyunción.
    """
    symbol = "∨"

    def semantics(self, left_value: bool, right_value: bool) -> bool:
        return left_value or right_value


class Imp(BinaryOperator):
    """
    Imp es el operador binario de implicación.
    """
    symbol = "→"

    def semantics(self, left_value: bool, right_value: bool) -> bool:
        return (not left_value) or right_value


unary_operators: list[type[Neg]] = [Neg]
binary_operators: list[type[And] | type[Or] | type[Imp]] = [And, Or, Imp]
