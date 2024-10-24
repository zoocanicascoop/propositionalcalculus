from __future__ import annotations
from functools import cached_property, reduce
from copy import copy

from rich.table import Table
from rich.padding import Padding
from rich.panel import Panel


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
    """
    Reglas de inferencia.

    Una regla de inferencia consiste de una serie de premisas de las cuales se
    puede derivar una conclusión. 
    """
    def __init__(
        self,
        name: str,
        assumptions: Formulas,
        conclusion: Formula,
    ) -> None:
        """
        Constructor de la regla de inferencia.

        :param name: Nombre de la regla.
        :param assumptions: Premisas de la regla.
        :param conclusion: Conclusión de la regla.
        """
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
        # TODO: Decide how to define equality and hash
        return (
            hash(self._name)
            + sum(hash(a) for a in self._assumptions)
            + hash(self._conclusion)
        )

    def __eq__(self, other: InferenceRule) -> bool:
        # TODO: Decide how to define equality and hash
        return (
            self._name == other._name
            and self._assumptions == other._assumptions
            and self._conclusion == other._conclusion
        )

    @cached_property
    def arity(self) -> int:
        """El número de premisas de la regla de inferencia"""
        return len(self._assumptions)

    @cached_property
    def assumptions_vars(self) -> set[Var]:
        """Conjunto de variables presentes en las premisas de la regla"""
        return set().union(*[a.vars for a in self._assumptions])

    @cached_property
    def conclusion_vars(self) -> set[Var]:
        """Cojunto de variables presentes en la conclusión de la regla"""
        return self._conclusion.vars

    @cached_property
    def is_sound(self) -> bool:
        """
        Determina si la regla de inferencia es cohrente con la semántica de 
        la lógica proposicional.
        """
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
        La aplicación de la regla consiste en, dadas unas premisas concretas con 
        la forma (mismo patrón) de las premisas abstractas de la regla, obtener 
        una conclusión concreta donde se han efectuado las sustituciones a
        partir del reconocimiento de los patrones en las premisas.

        Es decir, para aplicar la regla:

        - Para cada premisa concreta (las proporcionadas en el parámetro de
        entrada) se aplica el reconocimiento de patrones con las premisa
        abstracta (de la regla) y se obtiene un binding.
        - Se mezclan todos los bindings obtenidos en un único binding global.
        - Se aplica la sustiución del binding obtenido a la conclusión de la
          regla.

        Args:
            assumptions: Premisas concretas de la regla.
            conclusion_binding: valor inicial del binding global.

        Returns:
            Conclusión de la regla donde se han hecho las sustituciones obtenidas de las premisas.
        """
        # TODO: Devolver mensajes de error según el tipo de fallo de aplicación.

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
        """
        La aplicación de una regla es un tipo de paso de una demostración,
        codificado mediante la clase RuleApplication.

        Esta implementación de call posibilita generar el paso RuleApplication
        correspondiente a la aplicación de la regla de inferencia, sin tener que
        instanciar la clase RuleApplication directamente.
        """
        return RuleApplication(self, list(assumption_indices))

    def specialize(self, binding: dict[Var, Formula]) -> InferenceRule:
        """
        Especializar una regla de inferencia consiste en aplicar una sustitución
        a las premisas y conclusión de la regla.

        Args:
            binding: Binding de la sustitución a aplicar.

        Returns:
            Nueva regla de inferencia especializada.
        """
        assumptions = list(map(lambda a: a.subs(binding), self._assumptions))
        conclusion = self._conclusion.subs(binding)
        return InferenceRule(self._name + " specialized", assumptions, conclusion)

    def is_specialization(self, other: InferenceRule) -> bool:
        """
        Determina si la regla es la especialización de otra regla dada.

        Args:
            other: regla a comparar.

        Returns: 
            True si la regla es una especialización de la otra regla, False en caso contrario.
        """
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
    """
    Una demostración es una secuencia de pasos. 
    Cada paso es una instancia del tipo ProofStep.
    """
    def __init__(
        self,
        rules: set[InferenceRule],
        axioms: list[Formula],
        assumptions: Formulas,
        conclusion: Formula,
        steps: list[ProofStep],
    ) -> None:
        """
        Args:
            rules: Conjunto de reglas de inferencia que conforman el sistema de deducción.
            axioms: Lista de axiomas que conforman el sistema de deducción.
            assumptions: Fórmulas que se asumen como verdaderas.
            conclusion: Fórmula que se quiere demostrar.
            steps: Lista de pasos de la demostración.
        """
        assert len(steps) > 0, "The amount of steps must be positive"
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
        """
        Devuelve el conjunto de índices de los pasos de los que depende el
        paso dado por el índice.

        Args:
            index: Índice del paso.

        Returns: 
            Conjunto de índices de los pasos de los que depende el paso.
        """
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
        """
        Devuelve una subdemostración que contiene los pasos necesarios para
        demostrar la conclusión en el paso dado por el índice.

        Args:
            index: Índice del paso.
            delete_superflous_assumptions: Si es True, se eliminan las asunciones superfluas.

        Returns: 
            Subdemostración.
        """
        new_conclusion = self.state[index]
        assert new_conclusion is not None
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
            new_conclusion,
            steps,
        )

    @cached_property
    def state(self) -> list[Formula | None]:
        """
        Itera por todos los pasos de la demostración y va aplicando los pasos,
        obteniendo una lista de fórmulas que representan el estado de la
        demostración después de cada paso. Si en algún paso la aplicación
        devuelve None, se detiene la iteración y se devuelve la lista hasta
        ese paso.

        Returns:
            Lista de fórmulas que representan el estado de la demostración.
        """
        state = []
        for step in self.steps:
            match step:
                case AssumptionInclusion():
                    state.append(step.apply(self.assumptions))
                case AxiomSpecialization():
                    state.append(step.apply(self.axioms))
                case RuleApplication():
                    state.append(step.apply(state))
            if state[-1] is None:
                break
        return state

    @cached_property
    def check(self) -> bool:
        """
        Comprueba si la demostración es correcta, es decir, si la última fórmula
        de la lista de estados es la conclusión de la demostración.
        """
        return self.state[-1] == self.conclusion

    def display(self, highlight_rule: int | None = None):
        """
        Muestra la demostración en un panel de Rich.
        """
        t = Table(show_header=False, box=None)
        t.add_column("Section", vertical="middle", style="bold")
        t.add_column("Content")
        t.add_row(
            "Assumptions",
            "\n".join(map(lambda a: f"{a[0]}. {a[1]}", enumerate(self.assumptions))),
        )
        t.add_row("Conclusion", Padding(str(self.conclusion), (1, 0)))
        steps_t = Table.grid("n", "state", "step")
        error = False
        deps_highlights: set[int] = set()
        if highlight_rule and 0 <= highlight_rule < len(self.steps):
            step = self.steps[highlight_rule]
            if isinstance(step, RuleApplication):
                deps_highlights = deps_highlights.union(set(step.assumption_indices))

        for i, (step, state) in enumerate(zip(self.steps, self.state)):
            if i == highlight_rule:
                style = "[bold dark_orange]"
            elif i in deps_highlights:
                style = "[bold magenta]"
            else:
                style = ""
            if state is not None:
                steps_t.add_row(
                    f"{style}{i}. ", f"{style}{state}", f" {style}[italic]{step}"
                )
            else:
                steps_t.add_row(
                    f"{i}. ", "[bright_red]error", f" [italic bright_red]{step}"
                )
                error = True
        t.add_row("Steps", steps_t)
        if self.state[-1] != self.conclusion:
            t.add_row("", "\nUnfinished proof!")
            error = True
        return Panel(
            Padding(t, 1),
            title=f"[bold {'red' if error else 'green'}]{repr(self)}",
            expand=False,
        )

    @cached_property
    def used_assumptions(self) -> list[Formula]:
        """Lista de asunciones usadas en la demostración"""
        result = []
        for step in self.steps:
            if isinstance(step, AssumptionInclusion):
                ass = step.apply(self.assumptions)
                if ass is not None:
                    result.append(ass)
        return result

    def superflous_assumption(self, assumption: Formula) -> bool:
        """Determina si una premisa es superflua"""
        return assumption not in self.used_assumptions

    def delete_superflous_assumptions(self) -> Proof:
        """
        Devuelve una demostración equivalente en la que se han eliminado las
        premisas superfluas.
        """
        return self.step_subproof(len(self.steps) - 1, True)


def proof_mixer(proof1: Proof, proof2: Proof) -> tuple[list[Formula], list[ProofStep]]:
    """
    Función que concatena dos demostraciones, eliminando las premisas repetidas
    y reindexando los pasos de las demostraciones de forma acorde.

    Returns:
        tupla con la nueva lista de premisas y nueva lista de pasos.
    """
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
    """
    Tipo de paso de una demostración que consiste en incluir una de las premisas
    de la demostración para ser utilizada.
    """
    __match_args__ = ("index",)

    def __init__(self, index: int):
        self.index = index

    def __repr__(self):
        return f"Ass {self.index}"

    def apply(self, assumptions: list[Formula]) -> Formula | None:
        if 0 <= self.index < len(assumptions):
            return assumptions[self.index]


Ass = AssumptionInclusion


class AxiomSpecialization:
    """
    Tipo de paso de una demostración que consiste en incluir un axioma de la
    teoría en el que se ha realizado una sustitución arbitraria
    (especialización) mediante un binding.
    """
    __match_args__ = ("axiom_index", "binding")

    def __init__(self, axiom_index: int, binding: Binding) -> None:
        self.axiom_index = axiom_index
        self.binding = binding

    def __repr__(self):
        return f"Ax {self.axiom_index} {self.binding}"

    def apply(self, axioms: list[Formula]) -> Formula | None:
        if 0 <= self.axiom_index < len(axioms):
            axiom = axioms[self.axiom_index]
            if set(self.binding.keys()) == axiom.vars:
                return axiom.subs(self.binding)


AxS = AxiomSpecialization


class RuleApplication:
    """
    Tipo de paso de una demostración que consiste en aplicar una regla de
    inferencia del sistema deductivo que se esté considerando.
    """
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
