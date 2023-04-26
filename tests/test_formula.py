import pytest
from liar.formula import (
    And,
    BinaryOperator,
    Const,
    Formula,
    Imp,
    Neg,
    Or,
    UnaryOperator,
    Var,
)
from liar.table import is_tauto


@pytest.fixture(scope="function")
def random_formula() -> Formula:
    return Formula.random(10, 100, True)


def test_var_str():
    vars = Var.generate(10, random=True)
    for v in vars:
        assert str(v) == v.value


def test_simp_double_neg(random_formula: Formula):
    f = random_formula.simp_double_neg
    match f:
        case Neg(Neg()):
            pytest.fail(f"{f} contiene una doble negación")
        case UnaryOperator(A):
            test_simp_double_neg(A)
        case BinaryOperator(A, B):
            test_simp_double_neg(A)
            test_simp_double_neg(B)
        case _:
            pass


def test_push_neg(random_formula: Formula):
    f = random_formula.push_neg
    match f:
        case Neg(f):
            assert isinstance(f, Var) or isinstance(
                f, Const
            ), f"{f} no es de tipo Var ni Const"
        case UnaryOperator(A):
            test_push_neg(A)
        case BinaryOperator(A, B):
            test_push_neg(A)
            test_push_neg(B)
        case _:
            pass


def test_subs_imp(random_formula: Formula):
    f = random_formula.subs_imp
    match f:
        case Imp():
            pytest.fail(f"{f} contiene una implicación")
        case UnaryOperator(A):
            test_subs_imp(A)
        case BinaryOperator(A, B):
            test_subs_imp(A)
            test_subs_imp(B)
        case _:
            pass


def test_distribute_or(random_formula: Formula):
    f = random_formula.distribute_or
    match f:
        case Or(And(_, _), _):
            pytest.fail(f"{f} contiene un And dentro de un Or")
        case Or(_, And(_, _)):
            pytest.fail(f"{f} contiene un And dentro de un Or")
        case UnaryOperator(A):
            test_distribute_or(A)
        case BinaryOperator(A, B):
            test_distribute_or(A)
            test_distribute_or(B)
        case _:
            pass

def test_simp_const(random_formula: Formula):
    f = random_formula.simp_const
    match f:
        case Const():
            pass
        case _:
            assert f.consts == set(), f"La fórmula {f} no debería contener constantes"

def test_is_tauto_congruent(random_formula: Formula):
    assert random_formula.is_tauto == is_tauto(random_formula)


def test_subs_examples():
    A = Var('A')
    B = Var('B')
    C = Var('C')
    D = Var('D')

    assert (A & B).subs({A: A & B}) == (A & B)&B
    assert (~B).subs({A: A & B}) == ~B
