from liar.inference import InferenceRule
from .proof import Proof, AxiomSpecialization
from .formula import Formula, Var, Binding

A, B, C = Var.generate(3)

MP = InferenceRule("MP", [A, A >> B], B)


def Ax(axiom_index: int, binding: Binding):
    return AxiomSpecialization(axiom_index, binding)


axioms: list[Formula] = [
    ~A >> (A >> B),
    B >> (A >> B),
    (A >> B) >> ((~A >> B) >> B),
    (A >> (B >> C)) >> ((A >> B) >> (A >> C)),
    A >> (B >> (A & B)),
    (A & B) >> A,
    (A & B) >> B,
    A >> (A | B),
    B >> (A | B),
    (A >> C) >> ((B >> C) >> ((A | B) >> C)),
]


a_implies_a_proof = Proof(
    axioms,
    A,
    A,
    [
        Ax(1, {A: A >> A, B: A}),
        Ax(3, {A: A, B: A >> A, C: A}),
        MP(1, 2),
        Ax(1, {A: A, B: A}),
        MP(4, 3),
        MP(0, 5),
    ],
)


elim_double_neg = InferenceRule(
    "E¬¬",
    ~~A,
    A,
    Proof(
        axioms,
        ~~A,
        A,
        [
            Ax(0, {A: ~A, B: A}),
            MP(0, 1),
            Ax(1, {A: ~A, B: A}),
            # TODO: Usar sub-demostración de A >> A
            Ax(1, {A: A >> A, B: A}),
            Ax(3, {A: A, B: A >> A, C: A}),
            MP(4, 5),
            Ax(1, {A: A, B: A}),
            MP(7, 6),
            # final de A >> A
            Ax(2, {A: A, B: A}),
            MP(8, 9),
            MP(2, 10),
        ],
    ),
)


intro_and = InferenceRule(
    "I∧",
    [A, B],
    A & B,
    Proof(
        axioms,
        [A, B],
        A & B,
        [
            Ax(4, {A: A, B: B}),
            MP(0, 2),
            MP(1, 3),
        ],
    ),
)

intro_double_neg = InferenceRule(
    "I¬¬",
    A,
    ~~A,
    Proof(
        axioms,
        A,
        ~~A,
        [
            Ax(2, {A: ~A, B: A >> ~~A}),
            Ax(0, {A: A, B: ~~A}),
            MP(2, 1),
            Ax(1, {A: A, B: ~~A}),
            MP(4, 3),
            MP(0, 5),
        ],
    ),
)


intro_or_left = InferenceRule(
    "I∧1",
    A,
    A | B,
    Proof(
        axioms,
        A,
        A | B,
        [
            Ax(7, {A: A, B: B}),
            MP(0, 1),
        ],
    ),
)


intro_or_right = InferenceRule(
    "I∧2",
    A,
    B | A,
    Proof(
        axioms,
        A,
        B | A,
        [
            Ax(8, {A: B, B: A}),
            MP(0, 1),
        ],
    ),
)
