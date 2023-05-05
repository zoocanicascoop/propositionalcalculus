from __future__ import annotations
from functools import cached_property

from .rule import pattern_match
from .formula import Formula, Const, Var

Binding = dict[Var, Formula]

def merge_bindings(a:Binding, b:Binding) -> Binding | None:
    for key in a.keys():
        if key in b and a[key] != b[key]:
            return None
    return a | b

class InferenceRule:
    def __init__(
        self, assumptions: Formula | tuple[Formula, ...], conclusion: Formula
    ) -> None:
        self.assumptions = (
            (assumptions,) if isinstance(assumptions, Formula) else assumptions
        )
        self.conclusion = conclusion


    def __str__(self)-> str:
        assumptions = ", ".join(map(str, self.assumptions))
        conclusion = str(self.conclusion)
        bar = "—"*max(len(assumptions), len(conclusion))
        return f"{assumptions}\n{bar}\n{conclusion}"

    @cached_property
    def is_sound(self) -> bool:
        f = Const.TRUE
        for assumption in self.assumptions:
            f = f & assumption
        f = f >> self.conclusion
        return f.is_tauto

    def apply(self, assumptions: Formula | tuple[Formula,...]) -> Formula | None:
        assumptions = ( (assumptions, ) if isinstance(assumptions, Formula) else assumptions)
        if len(self.assumptions) != len(self.assumptions):
            return None
        global_binding = {}
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
        return InferenceRule(assumptions, conclusion)

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


class Proof():
    def __init__(self, assumptions: list[Formula], conclusion: Formula, steps: list[tuple[InferenceRule, int]]) -> None:
        self.assumptions = assumptions
        self.conclusion = conclusion
        self.steps = steps

    def check(self, verbose = False) -> bool:
        state = self.assumptions
        i = len(state)
        if verbose:
            print("Assumptions: ")
            for k in range(i):
                print(f"{k}. {state[k]}")

        for rule, index in self.steps:
            f = rule.apply(state[index])
            if f is None:
                return False
            else:
                if verbose:
                    print(f"{i}. {state[i]}")
                state.append(f)
            i += 1
        return len(state) > 0 and state[-1] == self.conclusion
