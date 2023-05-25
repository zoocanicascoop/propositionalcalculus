from __future__ import annotations
from collections.abc import Iterable
from enum import Enum
from functools import cached_property
from random import choice, randint, sample

Binding = dict["Var", "Formula"]


def merge_bindings(a: Binding, b: Binding) -> Binding | None:
    for key in a.keys():
        if key in b and a[key] != b[key]:
            return None
    return a | b


class OrderType(Enum):
    INORDER = 0
    BREADTH_FIRST = 1


class Formula:
    """
    A class for representing propositional formulas of classical logic.
    """

    def __str__(self):
        return repr(self)

    @property
    def str_polish(self) -> str:
        raise NotImplementedError()

    @staticmethod
    def parse_polish(string: str, stack: list[Formula] = []) -> Formula | None:
        """Parses a formula expressed in the reversed polish notation."""
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
        """Graphviz code for visually representing the formula tree."""
        return "graph {\n  " + "\n  ".join(self._graph_rec()) + "\n}"

    def render_graph(self, path="./graph.gv"):
        """Utility for rendering the formula tree with graphviz."""
        import graphviz
        from graphviz.backend.rendering import pathlib

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
    def random(n_vars: int, max_depth: int, include_consts: bool = False) -> Formula:
        """
        Generates a random formula, represented in the reverse polish notation.

        :n_vars: number of variables from wich to choice when generating the random formula
        :max_depth: maximum depth of the formula tree
        :include_consts: wether to include constants in the formula generation
        """
        f = Formula.parse_polish(
            Formula.random_polish(n_vars, max_depth, include_consts)
        )
        assert isinstance(f, Formula)
        return f

    @staticmethod
    def random_polish(n_vars: int, max_depth: int, include_consts: bool = False) -> str:
        """
        Generates a random formula, represented in the reverse polish notation.

        :n_vars: number of variables from wich to choice when generating the random string
        :max_depth: maximum depth of the formula tree
        :include_consts: wether to include constants in the formula generation
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

    # Old implementation of random
    # @staticmethod
    # def random(n_vars: int, n_iters: int, include_consts: bool = False) -> Formula:
    #     """Random formula generator."""
    #     formulas: set[Const | Var | Neg | And | Or | Imp] = set(Var.generate(n_vars))
    #     if include_consts:
    #         formulas = formulas.union({Const.FALSE, Const.TRUE})
    #     current_formula = None
    #     assert n_iters > 0, "El número de iteraciones debe ser positivo"
    #     for _ in range(n_iters):
    #         option = choice(["unary", "binary"])
    #         if option == "unary":
    #             Op = choice(unary_operators)
    #             f = choice(list(formulas))
    #             current_formula = Op(f)
    #         elif option == "binary":
    #             Op = choice(binary_operators)
    #             f1, f2 = sample(list(formulas), 2)
    #             current_formula = Op(f1, f2)
    #         assert isinstance(current_formula, Formula)
    #         formulas.add(current_formula)
    #     assert isinstance(current_formula, Formula)
    #     return current_formula

    @cached_property
    def vars(self) -> set["Var"]:
        """Set of variables present in the formula."""
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
        """Set of constants present in the formula."""
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
        Substitutes variables of the formula with formulas.

        :binding: the dictionary that maps variables to formulas.
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
    ) -> Iterable[Formula]:
        """Traverses the formula tree in the given OrderType."""
        match order_type:
            case OrderType.INORDER:
                return self.traverse_inorder()
            case OrderType.BREADTH_FIRST:
                return self.traverse_breadth()

    def traverse_inorder(self) -> Iterable[Formula]:
        """Inorder tree traversal."""
        match self:
            case Var() | Const():
                yield self
            case UnaryOperator(A):
                yield self
                yield from A.traverse_inorder()
            case BinaryOperator(A, B):
                yield self
                yield from A.traverse_inorder()
                yield from B.traverse_inorder()

    def traverse_breadth(self) -> Iterable[Formula]:
        """Breadth first tree traversal."""
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

    @cached_property
    def simp_double_neg(self) -> Formula:
        """Equivalent function where all double negations are simplified."""
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
        Equivalent funciton where all implications are substituted using the
        A → B iff ¬A ∨ B equivalence.
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
        Equivalent function where all the negations are pushed down into the
        formula tree, using De Morgan formulas. Double negations are also
        eliminated.
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
        Equivalent function where the distributive property of the disjuntion is
        applied.
        """
        f1, f2 = self, self._distribute_or_step
        while f2 != f1:
            f1 = f2
            f2 = f1._distribute_or_step
        return f1

    @cached_property
    def _distribute_or_step(self) -> Formula:
        """
        Equivalent function where the distributive property of the disjunction
        is applied once in all subtrees of the formula.
        """
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
        Equivalent formula where all the redundant constants and negations of
        constants are simplified.
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
        Conjunctive Normal Form.

        This normal form is calculated by appliying sequentially the following equivalences:
        - All implications are removed using subs_imp,
        - all negations are pushed down the formula tree with push_neg,
        - the distributive property of disjuntion is applied with distribute_or,
        - redundant constants are deleted using simp_const.
        """
        return self.subs_imp.push_neg.distribute_or.simp_const

    @cached_property
    def CNF_structured(self) -> list[set[Neg | Var | Const]]:
        """
        A structured version of the CNF.

        This function returns a list of sets of simple formulas (negations of
        variables, variables or constants).
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
        return "∧".join(
            [f"({'∨'.join([ str(e) for e in list(disj)])})" for disj in cnf]
        )

    @cached_property
    def is_tauto(self) -> bool:
        """Determines if the formula is a tautology, using the formula CNF"""
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
