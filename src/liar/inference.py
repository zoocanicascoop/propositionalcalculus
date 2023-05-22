from __future__ import annotations
from functools import cached_property


from .rule import pattern_match
from .formula import Binding, Formula, Const, Var
from .proof import Proof, RuleApplication


def merge_bindings(a: Binding, b: Binding) -> Binding | None:
    for key in a.keys():
        if key in b and a[key] != b[key]:
            return None
    return a | b


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
            proof.check_and_state()
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

    def __call__(self, *assumption_indices: int) -> RuleApplication:
        return RuleApplication(self, assumption_indices)

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
