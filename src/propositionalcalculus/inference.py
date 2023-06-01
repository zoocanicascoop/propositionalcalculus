from __future__ import annotations
from functools import cached_property, reduce
from copy import copy


from .rule import pattern_match
from .formula import (
    Binding,
    Formula,
    Const,
    Formulas,
    Var,
    formulas_to_list,
    merge_bindings,
)


class InferenceRule:
    def __init__(
        self,
        name: str,
        assumptions: Formulas,
        conclusion: Formula,
    ) -> None:
        self._name = name
        self._assumptions = formulas_to_list(assumptions)
        self._conclusion = conclusion

    def __repr__(self) -> str:
        return f"<InferenceRule {self._name}>"

    @property
    def name(self) -> str:
        return self.name

    def __str__(self) -> str:
        assumptions = ", ".join(map(str, self._assumptions))
        conclusion = str(self._conclusion)
        bar = "—" * max(len(assumptions), len(conclusion))
        return f"{assumptions}\n{bar}\n{conclusion}"

    def __hash__(self) -> int:
        """TODO: Decide how to define equality and hash"""
        return (
            hash(self._name)
            + sum(hash(a) for a in self._assumptions)
            + hash(self._conclusion)
        )

    def __eq__(self, other: InferenceRule) -> bool:
        """TODO: Decide how to define equality and hash"""
        return (
            self._name == other._name
            and self._assumptions == other._assumptions
            and self._conclusion == other._conclusion
        )

    @cached_property
    def arity(self) -> int:
        """The number of assumptions of the inference rule."""
        return len(self._assumptions)

    @cached_property
    def assumptions_vars(self) -> set[Var]:
        """Set of variables present in the rule assumptions."""
        return set().union(*[a.vars for a in self._assumptions])

    @cached_property
    def conclusion_vars(self) -> set[Var]:
        """Set of variables present in the rule conclusion."""
        return self._conclusion.vars

    @cached_property
    def is_sound(self) -> bool:
        """Wether the rule is coherent with the semantics."""
        f = Const.TRUE
        for assumption in self._assumptions:
            f = f & assumption
        f = f >> self._conclusion
        return f.is_tauto

    def apply(
        self,
        assumptions: Formulas,
        conclusion_binding: Binding | None = None,
    ) -> Formula | None:
        """
        TODO: Devolver mensajes de error según el tipo de fallo de aplicación.
        """

        assumptions = formulas_to_list(assumptions)

        if len(self._assumptions) != len(assumptions):
            return None
        if conclusion_binding is None:
            conclusion_binding = dict()
        if self.conclusion_vars.difference(self.assumptions_vars) != set(
            conclusion_binding.keys()
        ):
            return None
        global_binding = conclusion_binding.copy()
        for gen_assumption, spec_assumption in zip(self._assumptions, assumptions):
            binding = next(pattern_match(gen_assumption, spec_assumption))
            if binding is None:
                return None
            global_binding = merge_bindings(global_binding, binding)
            if global_binding is None:
                return None
        return self._conclusion.subs(global_binding)

    def __call__(self, *assumption_indices: int) -> RuleApplication:
        return RuleApplication(self, list(assumption_indices))

    def specialize(self, binding: dict[Var, Formula]) -> InferenceRule:
        assumptions = list(map(lambda a: a.subs(binding), self._assumptions))
        conclusion = self._conclusion.subs(binding)
        return InferenceRule(self._name + " specialized", assumptions, conclusion)

    def is_specialization(self, other: InferenceRule) -> bool:
        if len(self._assumptions) != len(other._assumptions):
            return False
        global_binding = {}

        self_fs = list(self._assumptions) + [self._conclusion]
        other_fs = list(other._assumptions) + [other._conclusion]

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
        assumptions: Formulas,
        conclusion: Formula,
        steps: list[ProofStep],
    ) -> None:
        assert len(steps) > 0, "La cantidad de pasos debe ser positiva"
        self.rules = rules
        self.axioms = axioms
        self.assumptions = formulas_to_list(assumptions)
        assert len(self.assumptions) == len(
            set(self.assumptions)
        ), "There cannot be repeated assumptions"
        self.conclusion = conclusion
        self.steps = steps
        assert all(
            [s.rule in self.rules for s in self.steps if isinstance(s, RuleApplication)]
        ), "All RuleApplication steps must use rules explicitly declared in the proof rules"

    def __repr__(self):
        return f"{', '.join(map(str, self.assumptions))} ⊢ {self.conclusion}"

    def step_dependencies(self, index: int) -> set[int]:
        match self.steps[index]:
            case RuleApplication(_, indices):
                return reduce(
                    set.union, [self.step_dependencies(i) for i in indices]
                ).union(set(indices))
            case _:
                return set()

    def step_subproof(
        self, index: int, delete_superflous_assumptions: bool = False
    ) -> Proof:
        state = self.check_and_state()
        assert state is not None
        steps_indices = list(self.step_dependencies(index)) + [index]
        steps_indices.sort()
        if delete_superflous_assumptions:
            assumptions = []
        else:
            assumptions = self.assumptions.copy()
        assumptions_reindex: dict[int, int] = dict()
        steps: list[ProofStep] = []
        steps_reindex: dict[int, int] = dict()
        for i_new, i_old in enumerate(steps_indices):
            steps_reindex[i_old] = i_new
            match self.steps[i_old]:
                case AssumptionInclusion(i) as f:
                    if delete_superflous_assumptions:
                        assumptions.append(self.assumptions[i])
                        if i not in assumptions_reindex:
                            assumptions_reindex[i] = len(assumptions) - 1
                        steps.append(AssumptionInclusion(assumptions_reindex[i]))
                    else:
                        steps.append(f)
                case AxiomSpecialization() as f:
                    steps.append(f)
                case RuleApplication(rule, assumption_indices) as f:
                    new_indices = [steps_reindex[i] for i in assumption_indices]
                    steps.append(RuleApplication(rule, new_indices))
        return Proof(
            self.rules.copy(),
            self.axioms.copy(),
            assumptions,
            state[index],
            steps,
        )

    def check_and_state(self, verbose=False) -> list[Formula] | None:
        info = lambda s: print(s) if verbose else None
        info("Axioms:")
        info("\n".join([f"Ax {i}. {f}" for i, f in enumerate(self.axioms)]))
        info("Assumptions:")
        info("\n".join([f"{i}. {f}" for i, f in enumerate(self.assumptions)]))
        info("Steps:")
        state = []
        for i, step in enumerate(self.steps):
            match step:
                case AssumptionInclusion():
                    new_f = step.apply(self.assumptions)
                    state.append(new_f)
                case AxiomSpecialization():
                    new_f = step.apply(self.axioms)
                    state.append(new_f)
                case RuleApplication():
                    new_f = step.apply(state)
                    if new_f is None:
                        info(
                            f"{i}. Invalid application of {step.rule._name} to formulas {step.assumption_indices}"
                        )
                        return None
                    else:
                        state.append(new_f)
            info(f"{i}. {new_f} [{step}]")
        finished = state[-1] == self.conclusion
        if verbose:
            info(
                f"Proof finished succesfully!"
                if finished
                else f"Unfinished proof! Goal {self.conclusion}"
            )
        return state if finished else None

    @cached_property
    def used_assumptions(self) -> list[Formula]:
        return [
            step.apply(self.assumptions)
            for step in self.steps
            if isinstance(step, AssumptionInclusion)
        ]

    def superflous_assumption(self, assumption: Formula) -> bool:
        return assumption in self.used_assumptions

    def delete_superflous_assumptions(self) -> Proof:
        return self.step_subproof(len(self.steps) - 1, True)


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
    # First we add proof1 steps
    steps: list[ProofStep] = proof1.steps.copy()

    # Then we add proof2 steps
    for step in proof2.steps:
        match step:
            case AssumptionInclusion(i):
                steps.append(AssumptionInclusion(reindex_assumptions_proof2[i]))
            case RuleApplication():
                steps.append(step.pad(len(proof1.steps)))
            case _:
                steps.append(step)

    return assumptions, steps


class AssumptionInclusion:
    __match_args__ = ("index",)

    def __init__(self, index: int):
        self.index = index

    def __repr__(self):
        return f"Ass {self.index}"

    def apply(self, assumptions: list[Formula]) -> Formula:
        return assumptions[self.index]


Ass = AssumptionInclusion


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
        return f"{self.rule._name} {', '.join(map(str, self.assumption_indices))}"

    def pad(self, pad: int) -> RuleApplication:
        return RuleApplication(
            copy(self.rule), [i + pad for i in self.assumption_indices]
        )

    def apply(self, state: list[Formula]) -> Formula | None:
        for i in self.assumption_indices:
            if i + 1 > len(state):
                return None
        return self.rule.apply([state[index] for index in self.assumption_indices])


ProofStep = AssumptionInclusion | AxiomSpecialization | RuleApplication
