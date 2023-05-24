from .inference import InferenceRule, Proof, AxS, ProofStep
from .formula import Formula, Var

A, B, C = Var.generate(3)

MP = InferenceRule("MP", [A, A >> B], B)

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


class PCProof(Proof):
    def __init__(
        self,
        assumptions: Formula | list[Formula],
        conclusion: Formula,
        steps: list[ProofStep],
    ):
        super(PCProof, self).__init__({MP}, axioms, assumptions, conclusion, steps)


a_implies_a_proof = PCProof(
    A,
    A,
    [
        AxS(1, {A: A >> A, B: A}),
        AxS(3, {A: A, B: A >> A, C: A}),
        MP(1, 2),
        AxS(1, {A: A, B: A}),
        MP(4, 3),
        MP(0, 5),
    ],
)


elim_double_neg = InferenceRule(
    "E¬¬",
    ~~A,
    A,
    PCProof(
        ~~A,
        A,
        [
            AxS(0, {A: ~A, B: A}),
            MP(0, 1),
            AxS(1, {A: ~A, B: A}),
            # TODO: Usar sub-demostración de A >> A
            AxS(1, {A: A >> A, B: A}),
            AxS(3, {A: A, B: A >> A, C: A}),
            MP(4, 5),
            AxS(1, {A: A, B: A}),
            MP(7, 6),
            # final de A >> A
            AxS(2, {A: A, B: A}),
            MP(8, 9),
            MP(2, 10),
        ],
    ),
)


intro_and = InferenceRule(
    "I∧",
    [A, B],
    A & B,
    PCProof(
        [A, B],
        A & B,
        [
            AxS(4, {A: A, B: B}),
            MP(0, 2),
            MP(1, 3),
        ],
    ),
)

intro_double_neg = InferenceRule(
    "I¬¬",
    A,
    ~~A,
    PCProof(
        A,
        ~~A,
        [
            AxS(2, {A: ~A, B: A >> ~~A}),
            AxS(0, {A: A, B: ~~A}),
            MP(2, 1),
            AxS(1, {A: A, B: ~~A}),
            MP(4, 3),
            MP(0, 5),
        ],
    ),
)


intro_or_left = InferenceRule(
    "I∧1",
    A,
    A | B,
    PCProof(
        A,
        A | B,
        [
            AxS(7, {A: A, B: B}),
            MP(0, 1),
        ],
    ),
)


intro_or_right = InferenceRule(
    "I∧2",
    A,
    B | A,
    PCProof(
        A,
        B | A,
        [
            AxS(8, {A: B, B: A}),
            MP(0, 1),
        ],
    ),
)
