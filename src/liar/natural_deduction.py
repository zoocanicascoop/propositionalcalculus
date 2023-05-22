from .formula import Var
from .inference import InferenceRule

A, B, C = Var.generate(3)

elim_and_left = InferenceRule("E∧1", A & B, A)
elim_and_right = InferenceRule("E∧2", A & B, B)
modus_ponens = InferenceRule("MP", [A >> B, A], B)
elim_double_neg = InferenceRule("E¬¬", ~~A, A)
intro_or_left = InferenceRule("I∨1", A, A | B)
intro_or_right = InferenceRule("I∨2", A, B | A)
intro_and = InferenceRule("I∧", [A, B], A & B)

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
