from functools import cached_property
from .formula import Formula, Const

class InferenceRule:
    def __init__(
        self, assumptions: Formula | tuple[Formula, ...], conclusion: Formula
    ) -> None:
        self.assumptions = (
            (assumptions,) if isinstance(assumptions, Formula) else assumptions
        )
        self.conclusion = conclusion

    @cached_property
    def is_sound(self) -> bool:
        f = Const.TRUE
        for assumption in self.assumptions:
            f = f & assumption
        f = f >> self.conclusion
        return f.is_tauto
