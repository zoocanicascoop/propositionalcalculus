from .formula import Var
from .rule import InferenceRule

A, B, C = Var.generate(3)

elim_and_left = InferenceRule(A & B, A)
elim_and_right = InferenceRule(A & B, B)
modus_ponens = InferenceRule((A >> B, A), B)
elim_double_neg = InferenceRule(~~A, A)
intro_or_left = InferenceRule(A, A | B)
intro_or_right = InferenceRule(A, B | A)
intro_and = InferenceRule((A, B), A & B)

# TODO: entender bien como codificar las reglas y cuales nos hacen falta

rules = [
    elim_and_left,
    elim_and_right,
    modus_ponens,
    elim_double_neg,
    intro_or_left,
    intro_or_right,
    intro_and,
]
