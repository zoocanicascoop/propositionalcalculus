from __future__ import annotations
from functools import reduce
from typing import Union

from .formula import Formula, Binding
from .inference import InferenceRule

ProofStep = Union["RuleApplication", "AxiomSpecialization"]


class Proof:
    def __init__(
        self,
        axioms: list[Formula],
        assumptions: Formula | list[Formula],
        conclusion: Formula,
        steps: list[ProofStep],
    ) -> None:
        assert len(steps) > 0, "La cantidad de pasos debe ser positiva"
        self.axioms = axioms
        self.assumptions = (
            [assumptions] if isinstance(assumptions, Formula) else assumptions
        )
        self.conclusion = conclusion
        self.steps = steps

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
                    new_indices = tuple(
                        map(lambda i_old: reindex_dict[i_old], assumption_indices)
                    )
                    steps.append(RuleApplication(rule, new_indices))
        return Proof(self.axioms, assumptions, state[index], steps)

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


class AxiomSpecialization:
    def __init__(self, axiom_index: int, binding: Binding) -> None:
        self.axiom_index = axiom_index
        self.binding = binding

    def apply(self, axioms: list[Formula]) -> Formula:
        return axioms[self.axiom_index].subs(self.binding)

    def pad(self, n: int) -> AxiomSpecialization:
        return AxiomSpecialization(self.axiom_index + n, self.binding)


class RuleApplication:
    __match_args__ = ("rule", "assumption_indices")

    def __init__(
        self, rule: InferenceRule, assumption_indices: tuple[int, ...]
    ) -> None:
        assert rule.arity == len(
            assumption_indices
        ), f"La cantidad de premisas debe coincidir con la aridad de la regla."
        self.rule = rule
        self.assumption_indices = assumption_indices

    def apply(self, current_assumptions: list[Formula]) -> Formula | None:
        for i in self.assumption_indices:
            if i + 1 > len(current_assumptions):
                return None
        return self.rule.apply(
            tuple([current_assumptions[index] for index in self.assumption_indices])
        )

    def pad(self, n: int) -> RuleApplication:
        return RuleApplication(
            self.rule, tuple(map(lambda v: v + n, self.assumption_indices))
        )
