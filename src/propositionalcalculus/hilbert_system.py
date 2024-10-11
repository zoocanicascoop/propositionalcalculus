from __future__ import annotations

from typing import Literal

from .formula import Formula, Formulas, Imp, Var
from .inference import (
    AssumptionInclusion,
    AxS,
    InferenceRule,
    Proof,
    ProofStep,
    RuleApplication,
    proof_mixer,
)

A, B, C = Var.generate(3)


class PCProof(Proof):
    MP = InferenceRule("MP", [A, A >> B], B)
    axioms: list[Formula] = [
        B >> (A >> B),
        (A >> (B >> C)) >> ((A >> B) >> (A >> C)),
        (~B >> ~A) >> ((~B >> A) >> B),
    ]

    def __init__(
        self,
        assumptions: Formulas,
        conclusion: Formula,
        steps: list[ProofStep],
    ):
        super(PCProof, self).__init__(
            {PCProof.MP},
            PCProof.axioms,
            assumptions,
            conclusion,
            steps,
        )

    @staticmethod
    def from_proof(proof: Proof) -> PCProof:
        assert proof.rules == {PCProof.MP}
        assert proof.axioms == PCProof.axioms
        return PCProof(proof.assumptions, proof.conclusion, proof.steps)


MP = PCProof.MP


def assumption_to_implication_case(
    proof: PCProof, assumption: Formula
) -> Literal[1] | Literal[2] | Literal[3]:
    if proof.superflous_assumption(assumption):
        # The proof does not depend on the assumption
        return 1
    elif isinstance(proof.conclusion, Imp) and proof.conclusion.right == assumption:
        # The conclusion is of the form X >> assumption
        return 2
    else:
        # The conclusion comes from an application of a modus ponens.
        last_step = proof.steps[-1]
        assert (
            isinstance(last_step, RuleApplication) and last_step.rule == MP
        ), f"{last_step = }"
        return 3


def f_implies_f_proof(f: Formula, assumptions: list[Formula]):
    return PCProof(
        assumptions,
        f >> f,
        [
            AxS(0, {A: f, B: f}),
            AxS(0, {A: f >> f, B: f}),
            AxS(1, {A: f, B: f >> f, C: f}),
            MP(1, 2),
            MP(0, 3),
        ],
    )


def assumption_to_implication(proof: PCProof, assumption: Formula) -> PCProof:
    match assumption_to_implication_case(proof, assumption):
        case 1:
            proof = PCProof.from_proof(proof.delete_superflous_assumptions())
            proof.steps.append(AxS(0, {A: assumption, B: proof.conclusion}))
            i = len(proof.steps)
            proof.steps.append(MP(i - 2, i - 1))
            proof.conclusion = assumption >> proof.conclusion
            return proof

        case 2:
            assert (
                isinstance(proof.conclusion, Imp)
                and proof.conclusion.right == assumption
            )
            assumptions = proof.assumptions.copy()
            assumptions.remove(assumption)
            return PCProof(
                assumptions,
                assumption >> proof.conclusion,
                [AxS(0, {A: proof.conclusion.left, B: assumption})],
            )

        case 3:
            last_step = proof.steps[-1]
            assert isinstance(last_step, RuleApplication) and last_step.rule == MP
            i1, i2 = last_step.assumption_indices
            # TODO: Aqui i1 i2 pueden ser indices correspondientes a
            # assumptions.
            # Casos que hay que tener en cuenta:
            # - si A, A-> B |- B queremos obtener A->B |- A->B, pero ahora mismo
            # nuestras pruebas no tienen como pasos el uso de assumptions
            # Posible solucion: basarse en la demostracion del teorema de
            # deducción, que tiene en cuenta el caso particular de
            # demostraciones con solo un paso (teniendo en cuenta que las
            # demostraciones incluyen como pasos el uso de assumptions)
            if isinstance(proof.steps[i1], AssumptionInclusion):
                f: Formula = proof.assumptions[proof.steps[i1].index]
                if f == assumption:
                    p1 = proof.step_subproof(i1, delete_superflous_assumptions=True)
                else:
                    p1 = f_implies_f_proof(
                        f, proof.assumptions
                    ).delete_superflous_assumptions()
            else:
                p1 = assumption_to_implication(
                    PCProof.from_proof(proof.step_subproof(i1)), assumption
                )
            if isinstance(proof.steps[i2], AssumptionInclusion):
                f: Formula = proof.assumptions[proof.steps[i2].index]
                if f == assumption:
                    p2 = proof.step_subproof(i2, delete_superflous_assumptions=True)
                else:
                    p2 = f_implies_f_proof(
                        f, proof.assumptions
                    ).delete_superflous_assumptions()
            else:
                p2 = assumption_to_implication(
                    PCProof.from_proof(proof.step_subproof(i2)), assumption
                )
            assumptions, steps = proof_mixer(p1, p2)
            assert isinstance(p1.conclusion, Imp)
            steps.append(
                AxS(1, {A: assumption, B: p1.conclusion.right, C: proof.conclusion})
            )
            proof_len = len(steps)
            steps.append(PCProof.MP(proof_len - 2, proof_len - 1))
            steps.append(PCProof.MP(len(p1.steps) - 1, proof_len))
            return PCProof(assumptions, assumption >> proof.conclusion, steps)
