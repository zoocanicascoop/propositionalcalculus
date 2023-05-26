from propositionalcalculus.formula import Var
import pytest
from propositionalcalculus.inference import InferenceRule
from propositionalcalculus.natural_deduction import rules


def test_inference_is_sound():
    A = Var("A")
    for rule in rules:
        assert rule.is_sound
    assert InferenceRule("", (), A | (~A))


def test_inference_is_sound_false():
    A, B = Var.generate(2)
    assert InferenceRule("", A, B)
    assert InferenceRule("", (), A)


def test_inference_rule_specialize():
    P = Var("P")
    Q = Var("Q")
    R = Var("R")
    S = Var("S")
    X = Var("X")
    Y = Var("Y")
    r1 = InferenceRule("", ~~P, P)
    r2 = r1.specialize({P: Q >> R})
    assert r2.is_specialization(r1)

    r3 = r1.specialize({P: X})
    assert r3.is_specialization(r1)

    r1 = InferenceRule("", (Q >> P, ~P), ~Q)
    r2 = r1.specialize({Q: ~R, P: X >> S})
    assert r2.is_specialization(r1)

    r1 = InferenceRule("", (P | Q) | S, Q | S)
    r2 = r1.specialize({P: X & R, Q: ~Y})
    assert r2.is_specialization(r1)

    r1 = InferenceRule("", (P | Q) | S, Q | S)
    r2 = r1.specialize({P: P & Q, Q: ~~Q})
    assert r2.is_specialization(r1)


def test_inference_rule_specialize_false():
    P = Var("P")
    Q = Var("Q")
    R = Var("R")

    r1 = InferenceRule("", ~~P, P)
    r2 = InferenceRule("", Q >> P, ~Q)
    r3 = InferenceRule("", (Q >> P, ~P), ~Q)
    assert r2.is_specialization(r1) == False
    assert r3.is_specialization(r1) == False

    r1 = InferenceRule("", (P, P >> Q), Q)
    r2 = InferenceRule("", (R, P >> Q), Q)
    assert r2.is_specialization(r1) == False
