from __future__ import annotations
from .formula import Formula, Imp, Var
from .inference import Proof, ProofStep, InferenceRule, AxS, RuleApplication

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


def assumption_to_implication(proof: PCProof, assumption: Formula) -> PCProof:
    global MP
    conclusion_dependencies = map(
        lambda i: proof.ssssteps[i],
        proof.step_dependencies(len(proof.assumptions) + len(proof.steps) - 1),
    )
    if assumption not in conclusion_dependencies:
        steps = proof.steps.copy()
        steps.append(AxS(0, {A: assumption, B: proof.conclusion}))
        i = len(steps)
        steps.append(MP(i - 1, i))
        return PCProof(proof.assumptions.copy(), assumption >> proof.conclusion, steps)
    elif isinstance(proof.conclusion, Imp) and proof.conclusion.right == assumption:
        return PCProof(
            proof.assumptions.copy(),
            assumption >> proof.conclusion,
            [AxS(0, {A: proof.conclusion.left, B: assumption})],
        )

    else:
        last_step = proof.steps[-1]
        assert isinstance(last_step, RuleApplication) and last_step.rule == MP
        i1, i2 = last_step.assumption_indices
        p1 = assumption_to_implication(
            PCProof.from_proof(proof.step_subproof(i1)), assumption
        )
        p1_conclusion = p1.conclusion
        assert isinstance(p1_conclusion, Imp)
        p2 = assumption_to_implication(
            PCProof.from_proof(proof.step_subproof(i2)), assumption
        )
        p2_conclusion = p2.conclusion
        assert isinstance(p2_conclusion, Imp)

        assumptions = p1.assumptions.copy()
        reindex_p2: dict[int, int] = dict()
        added_assumptions = 0
        for i_old, assumption in enumerate(p2.assumptions):
            if assumption not in assumptions:
                reindex_p2[i_old] = len(assumptions)
                assumptions.append(assumption)
                added_assumptions += 1
            else:
                reindex_p2[i_old] = len(assumptions) - 1

        steps: list[ProofStep] = []
        for step in p1.steps:
            match step:
                case RuleApplication(MP, [j1, j2]):
                    steps.append(MP(j1 + added_assumptions, j2 + added_assumptions))
                case f:
                    steps.append(f)

        p2_assumptions_n = len(p2.assumptions)
        p1_steps_n = len(p1.steps)
        for step in p2.steps:
            match step:
                case RuleApplication(_, [j1, j2]):
                    if j1 < p2_assumptions_n:  # Assumption
                        k1 = reindex_p2[j1]
                    else:
                        k1 = j1 + added_assumptions + p1_steps_n
                    if j2 < p2_assumptions_n:  # Assumption
                        k2 = reindex_p2[j2]
                    else:
                        k2 = j2 + added_assumptions + p1_steps_n
                    steps.append(MP(k1, k2))
                case f:
                    steps.append(f)
        steps.append(
            AxS(2, {A: assumption, B: p1_conclusion.right, C: proof.conclusion})
        )
        # steps.append(PCProof.MP())
        return PCProof(assumptions, proof.conclusion, steps)
