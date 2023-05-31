from __future__ import annotations
from typing import Literal
from .formula import Formula, Imp, Var
from .inference import (
    Proof,
    ProofStep,
    InferenceRule,
    AxS,
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
        assumptions: Formula | list[Formula],
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
        assert isinstance(last_step, RuleApplication) and last_step.rule == MP
        return 3


def assumption_to_implication(proof: PCProof, assumption: Formula) -> PCProof:
    match assumption_to_implication_case(proof, assumption):
        case 1:
            proof = PCProof.from_proof(proof.delete_superflous_assumptions())
            proof.steps.append(AxS(0, {A: assumption, B: proof.conclusion}))
            i = len(proof.ssssteps)
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
            p1 = assumption_to_implication(
                PCProof.from_proof(proof.step_subproof(i1)), assumption
            )
            p2 = assumption_to_implication(
                PCProof.from_proof(proof.step_subproof(i2)), assumption
            )
            assumptions, steps = proof_mixer(p1, p2)
            assert isinstance(p1.conclusion, Imp)
            steps.append(
                AxS(1, {A: assumption, B: p1.conclusion.right, C: proof.conclusion})
            )
            proof_len = len(assumptions) + len(steps)
            steps.append(PCProof.MP(proof_len - 2, proof_len - 1))
            steps.append(PCProof.MP(len(assumptions) + len(p1.steps) - 1, proof_len))
            return PCProof(assumptions, assumption >> proof.conclusion, steps)


def assumption_to_implication_old(
    proof: PCProof, assumption: Formula, V: bool
) -> PCProof:
    global MP
    conclusion_dependencies = map(
        lambda i: proof.ssssteps[i],
        proof.step_dependencies(len(proof.assumptions) + len(proof.steps) - 1),
    )
    if assumption not in conclusion_dependencies:
        assumptions = proof.assumptions.copy()
        if assumption in assumptions:
            assumption_index = assumptions.index(assumption)
            assumptions.remove(assumption)
            steps: list[ProofStep] = []
            for step in proof.steps:
                match step:
                    case RuleApplication(_, [i1, i2]):
                        if i1 > assumption_index:
                            i1 -= 1
                        if i2 > assumption_index:
                            i2 -= 1
                        steps.append(MP(i1, i2))
                    case f:
                        steps.append(f)
        else:
            steps = proof.steps.copy()
        steps.append(AxS(0, {A: assumption, B: proof.conclusion}))
        i = len(steps)
        steps.append(MP(i - 1, i))
        p = PCProof(assumptions, assumption >> proof.conclusion, steps)
        if p.check_and_state() is None:
            p.check_and_state(True)
            assert False
        return p
    elif isinstance(proof.conclusion, Imp) and proof.conclusion.right == assumption:
        assumptions = proof.assumptions.copy()
        assumptions.remove(assumption)

        p = PCProof(
            assumptions,
            assumption >> proof.conclusion,
            [AxS(0, {A: proof.conclusion.left, B: assumption})],
        )
        assert p.check_and_state() is not None
        return p

    else:
        last_step = proof.steps[-1]
        assert isinstance(last_step, RuleApplication) and last_step.rule == MP
        i1, i2 = last_step.assumption_indices
        p1 = assumption_to_implication_old(
            PCProof.from_proof(proof.step_subproof(i1)), assumption, V
        )
        p2 = assumption_to_implication_old(
            PCProof.from_proof(proof.step_subproof(i2)), assumption, V
        )
        assumptions, steps = proof_mixer(p1, p2)
        steps.append(
            AxS(1, {A: assumption, B: p1_conclusion.right, C: proof.conclusion})
        )
        steps.append(PCProof.MP(len(steps) - 1, len(steps)))
        steps.append(PCProof.MP(len(p1.ssssteps), len(steps)))
        return PCProof(assumptions, assumption >> proof.conclusion, steps)
