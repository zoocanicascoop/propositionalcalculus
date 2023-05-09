from __future__ import annotations
from functools import cached_property

from .rule import pattern_match
from .formula import Formula, Const, Var

Binding = dict[Var, Formula]


def merge_bindings(a: Binding, b: Binding) -> Binding | None:
    for key in a.keys():
        if key in b and a[key] != b[key]:
            return None
    return a | b


class InferenceRule:
    def __init__(
        self,
        name: str,
        assumptions: Formula | tuple[Formula, ...],
        conclusion: Formula,
        proof: Proof | None = None,
    ) -> None:
        self.name = name
        self.assumptions = (
            (assumptions,) if isinstance(assumptions, Formula) else assumptions
        )
        self.conclusion = conclusion
        if proof is not None:
            assert (
                proof.assumptions == self.assumptions
            ), "The InferenceRule proof must have the same assumptions of the rule"
            assert (
                proof.conclusion == self.conclusion
            ), "The InferenceRule proof must have the same conclusion of the rule"
            proof.check()
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
        return len(self.assumptions)

    @cached_property
    def assumptions_vars(self) -> set[Var]:
        return set().union(*[a.vars for a in self.assumptions])

    @cached_property
    def conclusion_vars(self) -> set[Var]:
        return self.conclusion.vars

    @cached_property
    def is_sound(self) -> bool:
        f = Const.TRUE
        for assumption in self.assumptions:
            f = f & assumption
        f = f >> self.conclusion
        return f.is_tauto

    def apply(
        self,
        assumptions: Formula | tuple[Formula, ...],
        conclusion_binding: Binding | None = None,
    ) -> Formula | None:
        """
        TODO: Devolver mensajes de error según el tipo de fallo de aplicación.
        """

        assumptions = (
            (assumptions,) if isinstance(assumptions, Formula) else assumptions
        )

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

    def specialize(self, binding: dict[Var, Formula]) -> InferenceRule:
        assumptions = tuple(map(lambda a: a.subs(binding), self.assumptions))
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


class ProofStepApplyRule:
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

    def pad(self, n: int) -> ProofStepApplyRule:
        return ProofStepApplyRule(
            self.rule, tuple(map(lambda v: v + n, self.assumption_indices))
        )


class ProofStepSpecializeAxiom:
    def __init__(self, axiom_index: int, binding: Binding) -> None:
        self.axiom_index = axiom_index
        self.binding = binding

    def apply(self, axioms: list[Formula]) -> Formula:
        return axioms[self.axiom_index].subs(self.binding)

    def pad(self, n: int) -> ProofStepSpecializeAxiom:
        return ProofStepSpecializeAxiom(self.axiom_index + n, self.binding)


class Proof:
    def __init__(
        self,
        axioms: list[Formula],
        assumptions: Formula | tuple[Formula, ...],
        conclusion: Formula,
        steps: list[ProofStepApplyRule | ProofStepSpecializeAxiom],
    ) -> None:
        assert len(steps) > 0, "La cantidad de pasos debe ser positiva"
        self.axioms = axioms
        self.assumptions = (
            (assumptions,) if isinstance(assumptions, Formula) else assumptions
        )
        self.conclusion = conclusion
        self.steps = steps

    def check(self, verbose=False) -> bool:
        info = lambda s: print(s) if verbose else None
        info("Axioms:")
        info("\n".join([f"Ax {i}. {f}" for i, f in enumerate(self.axioms)]))
        info("Assumptions:")
        info("\n".join([f"{i}. {f}" for i, f in enumerate(self.assumptions)]))
        info("Steps:")
        k = len(self.assumptions)
        state = list(self.assumptions)
        for i, step in enumerate(self.steps):
            match step:
                case ProofStepSpecializeAxiom():
                    new_f = step.apply(self.axioms)
                    state.append(new_f)
                    if verbose:
                        info(f"{i+k}. {new_f} [Ax {step.axiom_index}]")
                case ProofStepApplyRule():
                    new_f = step.apply(state)
                    if new_f is None:
                        info(
                            f"{i+k}. Invalid application of {step.rule.name} to formulas {step.assumption_indices}"
                        )
                        return False
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
        return finished
