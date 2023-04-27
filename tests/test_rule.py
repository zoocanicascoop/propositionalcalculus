from liar.formula import Var
import pytest
from liar.rule import Rule, InferenceRule
from liar.natural_deduction import rules


def test_rule_match():
    pass

def test_inference_is_sound():
    A = Var('A')
    for rule in rules:
        assert rule.is_sound
    assert InferenceRule((), A|(~A))
        
def test_inference_is_sound_false():
    A, B = Var.generate(2)
    assert InferenceRule(A, B)
    assert InferenceRule((), A)
