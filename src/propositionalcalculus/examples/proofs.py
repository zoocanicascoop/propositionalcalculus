from ..inference import AxS
from ..formula import Var
from ..hilbert_system import PCProof, MP

A, B, C = Var.generate(3)

absurd = PCProof(
    [~A, A],
    B,
    [
        AxS(0, {A: ~B, B: A}),
        AxS(0, {A: ~B, B: ~A}),
        MP(1, 2),
        MP(0, 3),
        AxS(2, {A: A, B: B}),
        MP(5, 6),
        MP(4, 7),
    ],
)

a_implies_a = PCProof(
    [],
    A >> A,
    [
        AxS(0, {A: A, B: A}),
        AxS(0, {A: A >> A, B: A}),
        AxS(1, {A: A, B: A >> A, C: A}),
        MP(1, 2),
        MP(0, 3),
    ],
)

implication_transitivity = PCProof(
    [A >> B, B >> C, A],
    C,
    [
        MP(2, 0),
        MP(3, 1),
    ],
)

mp_application = PCProof([A >> B, A], B, [MP(1, 0)])

valid_proofs = [absurd, a_implies_a, implication_transitivity, mp_application]
