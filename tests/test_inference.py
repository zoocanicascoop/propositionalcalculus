from random import choice, randint, randrange
from propositionalcalculus.formula import Formula, Var
from propositionalcalculus.hilbert_system import MP, PCProof
import pytest
from propositionalcalculus.inference import (
    AxiomSpecialization,
    InferenceRule,
    Proof,
    RuleApplication,
)
from propositionalcalculus.natural_deduction import rules


def test_inference_rule_is_sound():
    A = Var("A")
    for rule in rules:
        assert rule.is_sound
    assert InferenceRule("test", [], A | (~A))


def test_inference_rule_is_sound_false():
    A, B = Var.generate(2)
    assert InferenceRule("test", A, B)
    assert InferenceRule("test", [], A)


def test_inference_rule_specialize():
    P = Var("P")
    Q = Var("Q")
    R = Var("R")
    S = Var("S")
    X = Var("X")
    Y = Var("Y")
    r1 = InferenceRule("test", ~~P, P)
    r2 = r1.specialize({P: Q >> R})
    assert r2.is_specialization(r1)

    r3 = r1.specialize({P: X})
    assert r3.is_specialization(r1)

    r1 = InferenceRule("test", [Q >> P, ~P], ~Q)
    r2 = r1.specialize({Q: ~R, P: X >> S})
    assert r2.is_specialization(r1)

    r1 = InferenceRule("test", (P | Q) | S, Q | S)
    r2 = r1.specialize({P: X & R, Q: ~Y})
    assert r2.is_specialization(r1)

    r1 = InferenceRule("test", (P | Q) | S, Q | S)
    r2 = r1.specialize({P: P & Q, Q: ~~Q})
    assert r2.is_specialization(r1)


def test_inference_rule_specialize_false():
    P = Var("P")
    Q = Var("Q")
    R = Var("R")

    r1 = InferenceRule("test", ~~P, P)
    r2 = InferenceRule("test", Q >> P, ~Q)
    r3 = InferenceRule("test", [Q >> P, ~P], ~Q)
    assert r2.is_specialization(r1) == False
    assert r3.is_specialization(r1) == False

    r1 = InferenceRule("test", [P, P >> Q], Q)
    r2 = InferenceRule("test", [R, P >> Q], Q)
    assert r2.is_specialization(r1) == False


def test_inference_rule_apply():
    f1 = Formula.random(5, 10)
    f2 = Formula.random(5, 10)
    assert MP.apply([f1, f1 >> f2]) == f2


def test_inference_rule_apply_invalid_assumptions_len():
    f1 = Formula.random(5, 10)
    assert MP.apply([f1]) == None


@pytest.fixture
def absurd_rule():
    A, B = Var.generate(2)
    return InferenceRule("absurd", [A, ~A], B)


def test_inference_rule_apply_conclusion_binding(absurd_rule):
    _, B = Var.generate(2)
    f1 = Formula.random(5, 10)
    f2 = Formula.random(5, 10)
    assert absurd_rule.apply([f1, ~f1], {B: f2}) == f2


def test_inference_rule_apply_invalid_conclusion_binding(absurd_rule):
    f1 = Formula.random(5, 10)
    assert absurd_rule.apply([f1, ~f1]) == None


def test_inference_rule_apply_invalid_application_pattern(absurd_rule):
    _, B = Var.generate(2)
    f1 = Formula.random(5, 10)
    assert absurd_rule.apply([f1, f1], {B: B}) == None


def test_axiom_specialization_apply():
    axioms = [Formula.random(5, 10)]
    binding = {v: Formula.random(3, 5) for v in axioms[0].vars}
    AxS = AxiomSpecialization(0, binding)
    assert isinstance(AxS.apply(axioms), Formula)


def test_rule_application_init():
    assert isinstance(MP(0, 1), RuleApplication)


def test_rule_application_invalid_init(absurd_rule):
    with pytest.raises(AssertionError):
        absurd_rule(0, 1, 2, 3)


def test_rule_application_apply():
    f1 = Formula.random(3, 5)
    f2 = Formula.random(2, 5)
    assumptions = [f1, f1 >> f2]
    assert RuleApplication(MP, [0, 1]).apply(assumptions) == f2


def test_rule_application_invalid_apply():
    f1 = Formula.random(5, 10)
    f2 = Formula.random(5, 10)
    assumptions = [f2, f1 >> f2]
    assert MP(10, 11).apply(assumptions) == None


def test_proof_check_and_state_valid(valid_proof: Proof):
    assert valid_proof.check_and_state() is not None
