from __future__ import annotations
from functools import cached_property, reduce


from .rule import Rule, pattern_match
from .formula import Binding, Formula, Const, Var, merge_bindings


class InferenceRule:
    def __init__(
        self,
        name: str,
        assumptions: Formula | list[Formula],
        conclusion: Formula,
        proof: Proof | None = None,
    ) -> None:
        self.name = name
        self.assumptions = (
            [assumptions] if isinstance(assumptions, Formula) else assumptions
        )
        self.conclusion = conclusion
        if proof is not None:
            assert (
                proof.assumptions == self.assumptions
            ), "The InferenceRule proof must have the same assumptions of the rule"
            assert (
                proof.conclusion == self.conclusion
            ), "The InferenceRule proof must have the same conclusion of the rule"
            assert proof.check_and_state() is not None
        self.proof = proof

    def __repr__(self) -> str:
        return self.name

    def __str__(self) -> str:
        assumptions = ", ".join(map(str, self.assumptions))
        conclusion = str(self.conclusion)
        bar = "—" * max(len(assumptions), len(conclusion))
        return f"{assumptions}\n{bar}\n{conclusion}"

    @cached_property
    def arity(self) -> int:
        """The number of assumptions of the inference rule."""
        return len(self.assumptions)

    @cached_property
    def assumptions_vars(self) -> set[Var]:
        """Set of variables present in the rule assumptions."""
        return set().union(*[a.vars for a in self.assumptions])

    @cached_property
    def conclusion_vars(self) -> set[Var]:
        """Set of variables present in the rule conclusion."""
        return self.conclusion.vars

    @cached_property
    def is_sound(self) -> bool:
        """Wether the rule is coherent with the semantics."""
        f = Const.TRUE
        for assumption in self.assumptions:
            f = f & assumption
        f = f >> self.conclusion
        return f.is_tauto

    def apply(
        self,
        assumptions: Formula | list[Formula],
        conclusion_binding: Binding | None = None,
    ) -> Formula | None:
        """
        TODO: Devolver mensajes de error según el tipo de fallo de aplicación.
        """

        assumptions = [assumptions] if isinstance(assumptions, Formula) else assumptions

        if len(self.assumptions) != len(assumptions):
            return None
        if conclusion_binding is None:
            conclusion_binding = dict()
        if self.conclusion_vars.difference(self.assumptions_vars) != set(
            conclusion_binding.keys()
        ):
            return None
        global_binding = conclusion_binding.copy()
        for gen_assumption, spec_assumption in zip(self.assumptions, assumptions):
            binding = next(pattern_match(gen_assumption, spec_assumption))
            if binding is None:
                return None
            global_binding = merge_bindings(global_binding, binding)
            if global_binding is None:
                return None
        return self.conclusion.subs(global_binding)

    def __call__(self, *assumption_indices: int) -> RuleApplication:
        return RuleApplication(self, list(assumption_indices))

    def specialize(self, binding: dict[Var, Formula]) -> InferenceRule:
        assumptions = list(map(lambda a: a.subs(binding), self.assumptions))
        conclusion = self.conclusion.subs(binding)
        return InferenceRule(self.name + " specialized", assumptions, conclusion)

    def is_specialization(self, other: InferenceRule) -> bool:
        if len(self.assumptions) != len(other.assumptions):
            return False
        global_binding = {}

        self_fs = list(self.assumptions) + [self.conclusion]
        other_fs = list(other.assumptions) + [other.conclusion]

        for self_f, other_f in zip(self_fs, other_fs):
            binding = next(pattern_match(other_f, self_f))
            if binding is None:
                return False
            global_binding = merge_bindings(global_binding, binding)
            if global_binding is None:
                return False
        return True


class Proof:
    def __init__(
        self,
        rules: set[InferenceRule],
        axioms: list[Formula],
        assumptions: Formula | list[Formula],
        conclusion: Formula,
        steps: list[ProofStep],
    ) -> None:
        assert len(steps) > 0, "La cantidad de pasos debe ser positiva"
        self.rules = rules
        self.axioms = axioms
        if isinstance(assumptions, Formula):
            assumptions = [assumptions]
        self.assumptions = assumptions
        assert len(self.assumptions) == len(
            set(self.assumptions)
        ), "There cannot be repeated assumptions"
        self.conclusion = conclusion
        self.steps = steps
        for step in self.steps:
            match step:
                case RuleApplication(rule, _):
                    assert (
                        rule in self.rules
                    ), "All RuleApplication steps must use rules explicitly declared in the proof rules"

    def __repr__(self):
        return f"{', '.join(map(str, self.assumptions))} ⊢ {self.conclusion}"

    @property
    def ssssteps(self):
        """
        TODO: Change name of this property. Currently we have self.steps that
        are the steps that are not assumptions and this property that includes
        the assumptions.
        """
        return self.assumptions + self.steps

    def step_dependencies(self, index: int) -> set[int]:
        match self.ssssteps[index]:
            case RuleApplication(_, assumption_indices):
                return reduce(
                    set.union, [self.step_dependencies(i) for i in assumption_indices]
                ).union(set(assumption_indices))
            case _:
                return set()

    def step_subproof(self, index: int) -> Proof:
        state = self.check_and_state()
        assert state is not None
        steps_indices = list(self.step_dependencies(index)) + [index]
        steps_indices.sort()
        reindex_dict: dict[int, int] = dict()
        assumptions: list[Formula] = []
        steps: list[ProofStep] = []
        for i_new, i_old in enumerate(steps_indices):
            reindex_dict[i_old] = i_new
            match self.ssssteps[i_old]:
                case Formula() as f:
                    assumptions.append(f)
                case AxiomSpecialization() as f:
                    steps.append(f)
                case RuleApplication(rule, assumption_indices) as f:
                    new_indices = [reindex_dict[i] for i in assumption_indices]
                    steps.append(RuleApplication(rule, new_indices))
        return Proof(self.rules, self.axioms, assumptions, state[index], steps)

    def check_and_state(self, verbose=False) -> list[Formula] | None:
        info = lambda s: print(s) if verbose else None
        info("Axioms:")
        info("\n".join([f"Ax {i}. {f}" for i, f in enumerate(self.axioms)]))
        info("Assumptions:")
        info("\n".join([f"{i}. {f}" for i, f in enumerate(self.assumptions)]))
        info("Steps:")
        k = len(self.assumptions)
        state = self.assumptions.copy()
        for i, step in enumerate(self.steps):
            match step:
                case AxiomSpecialization():
                    new_f = step.apply(self.axioms)
                    state.append(new_f)
                    if verbose:
                        info(f"{i+k}. {new_f} [Ax {step.axiom_index}]")
                case RuleApplication():
                    new_f = step.apply(state)
                    if new_f is None:
                        info(
                            f"{i+k}. Invalid application of {step.rule.name} to formulas {step.assumption_indices}"
                        )
                        return None
                    else:
                        info(
                            f"{i+k}. {new_f} [{step.rule.name} {step.assumption_indices}]"
                        )
                        state.append(new_f)
        finished = state[-1] == self.conclusion
        if verbose:
            info(
                f"Proof finished succesfully!"
                if finished
                else f"Unfinished proof! Goal {self.conclusion}"
            )
        return state if finished else None

    def superflous_assumption(self, assumption: Formula) -> bool:
        if assumption not in self.assumptions:
            return True
        elif self.assumptions.index(assumption) in self.step_dependencies(
            len(self.ssssteps) - 1
        ):
            return False
        else:
            return True

    def delete_superflous_assumptions(self) -> Proof:
        return self.step_subproof(len(self.ssssteps) - 1)

    # def delete_superflous_assumption(self, assumption: Formula) -> Proof:
    #     assert self.superflous_assumption(assumption), "The assumption must be superflous"
    #     if assumption not in self.assumptions:
    #         return self
    #     assumption_index = self.assumptions.index(assumption)
    #     assumptions = self.assumptions.copy()
    #     assumptions.remove(assumption)
    #     steps: list[ProofStep] = []
    #     for step in self.steps:
    #         match step:
    #             case RuleApplication(rule, indexes):
    #                 new_indexes = [
    #                     i - 1
    #                     if i > assumption_index
    #                     else i
    #                     for i in indexes
    #                 ]
    #                 steps.append(RuleApplication(rule, new_indexes))
    #             case _:
    #                 steps.append(step)
    #     return Proof(self.rules, self.axioms, assumptions, self.conclusion, steps)


def proof_mixer(proof1: Proof, proof2: Proof) -> tuple[list[Formula], list[ProofStep]]:
    assert (
        proof1.axioms == proof2.axioms and proof1.rules == proof2.rules
    ), "The proofs axioms and rules must match"
    # Mixing of proof1 and proof2 assumptions, starting with proof1 assumptions
    # and adding proof2 assumptions not in proof1.
    assumptions = proof1.assumptions.copy()
    reindex_assumptions_proof2: dict[int, int] = dict()
    ass_not_in_proof1 = 0
    for i_old, assumption in enumerate(proof2.assumptions):
        if assumption not in assumptions:
            reindex_assumptions_proof2[i_old] = len(assumptions)
            assumptions.append(assumption)
            ass_not_in_proof1 += 1
        else:
            reindex_assumptions_proof2[i_old] = assumptions.index(assumption)

    # Mixing proof steps
    steps: list[ProofStep] = []
    # First we add proof1 steps, reindexing the rule applications.
    proof1_assumptions_number = len(proof1.assumptions)
    for step in proof1.steps:
        match step:
            case RuleApplication(rule, indexes):
                new_indexes = [
                    i if i < proof1_assumptions_number else i + ass_not_in_proof1
                    for i in indexes
                ]
                steps.append(RuleApplication(rule, new_indexes))
            case _:
                steps.append(step)

    # Then we add proof2 steps
    proof2_assumptions_number = len(proof2.assumptions)
    proof2_padding = len(proof1.steps) + (len(assumptions) - len(proof2.assumptions))
    for step in proof2.steps:
        match step:
            case RuleApplication(rule, indexes):
                new_indexes = [
                    reindex_assumptions_proof2[i]
                    if i < proof2_assumptions_number
                    else i + proof2_padding
                    for i in indexes
                ]
                steps.append(RuleApplication(rule, new_indexes))
            case _:
                steps.append(step)

    return assumptions, steps


class AxiomSpecialization:
    __match_args__ = ("axiom_index", "binding")

    def __init__(self, axiom_index: int, binding: Binding) -> None:
        self.axiom_index = axiom_index
        self.binding = binding

    def __repr__(self):
        return f"Ax {self.axiom_index} {self.binding}"

    def apply(self, axioms: list[Formula]) -> Formula:
        return axioms[self.axiom_index].subs(self.binding)


AxS = AxiomSpecialization


class RuleApplication:
    __match_args__ = ("rule", "assumption_indices")

    def __init__(self, rule: InferenceRule, assumption_indices: list[int]) -> None:
        assert rule.arity == len(
            assumption_indices
        ), f"La cantidad de premisas debe coincidir con la aridad de la regla."
        self.rule = rule
        self.assumption_indices = assumption_indices

    def __repr__(self):
        return f"{self.rule.name} {', '.join(map(str, self.assumption_indices))}"

    def apply(self, current_assumptions: list[Formula]) -> Formula | None:
        for i in self.assumption_indices:
            if i + 1 > len(current_assumptions):
                return None
        return self.rule.apply(
            [current_assumptions[index] for index in self.assumption_indices]
        )


ProofStep = RuleApplication | AxiomSpecialization
