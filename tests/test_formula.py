from random import random, randrange
import pytest
from propositionalcalculus.formula import (
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
from propositionalcalculus.table import is_tauto


@pytest.fixture(scope="function")
def random_formula() -> Formula:
    return Formula.random(10, 10, True)


def test_var_str():
    vars = Var.generate(10, random=True)
    for v in vars:
        assert str(v) == v.value


def test_polish_notation(random_formula: Formula):
    assert (
        Formula.parse_polish(random_formula.str_polish) == random_formula
    ), f"No se ha podido parsear correctamente la fórmula {random_formula.str_polish}"


def test_len_vars_consts(random_formula: Formula):
    match random_formula:
        case Var() | Const():
            assert len(random_formula) == 1
            assert len(random_formula) == len(random_formula.vars) + len(
                random_formula.consts
            )
        case _:
            assert len(random_formula) > len(random_formula.vars) + len(
                random_formula.consts
            )


def test_replace_at_pos_inorder(random_formula: Formula):
    """
    Atención: este test solo comprueba que no se cambie la formula antes de
    llegar al punto donde se reemplaza. A partir de ese punto deja de comprobar
    """
    new_f = ~Var("A")
    pos = randrange(0, len(random_formula))
    replaced_f = random_formula.replace_at_pos_inorder(pos, new_f)
    current_pos = 0
    original_generator = random_formula.traverse_inorder()
    replaced_generator = replaced_f.traverse_inorder()
    while True:
        try:
            original_current = next(original_generator)
            replaced_current = next(replaced_generator)
            if current_pos == pos:
                break  # Se deja de comprobar
            assert original_current.__class__ == replaced_current.__class__
            current_pos += 1
        except StopIteration:
            break


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
    A, B = Var.generate(2)

    assert (A & B).subs({A: A & B}) == (A & B) & B
    assert (~B).subs({A: A & B}) == ~B
