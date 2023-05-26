from propositionalcalculus.formula import Formula, Formulas, Var
import pytest
from propositionalcalculus.inference import InferenceRule
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
    A, B = Var.generate(2)
    MP = InferenceRule("MP", [A >> B, A], B)
    f1 = Formula.random(5, 10)
    f2 = Formula.random(5, 10)
    assert MP.apply([f1 >> f2, f1]) == f2


def test_inference_rule_apply_invalid_assumptions_len():
    A, B = Var.generate(2)
    MP = InferenceRule("MP", [A >> B, A], B)
    f1 = Formula.random(5, 10)
    assert MP.apply([f1]) == None


def test_inference_rule_apply_conclusion_binding():
    A, B = Var.generate(2)
    MP = InferenceRule("MP", [A, ~A], B)
    f1 = Formula.random(5, 10)
    f2 = Formula.random(5, 10)
    assert MP.apply([f1, ~f1], {B: f2}) == f2


def test_inference_rule_apply_invalid_conclusion_binding():
    A, B = Var.generate(2)
    MP = InferenceRule("MP", [A, ~A], B)
    f1 = Formula.random(5, 10)
    assert MP.apply([f1, ~f1]) == None


def test_inference_rule_apply_invalid_application_pattern():
    A, B = Var.generate(2)
    MP = InferenceRule("MP", [A, ~A], B)
    f1 = Formula.random(5, 10)
    assert MP.apply([f1, f1], {B: B}) == None
