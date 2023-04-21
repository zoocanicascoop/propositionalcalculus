from . import *
from random import choice


def random_variable():
    return Var(choice("ABCDEGHIJKLMNOPQRSVWXYZ").upper())


def random_variables(n: int):
    vars = set()
    while len(vars) < n:
        vars.add(random_variable())
    return vars


def random_formula(n_vars: int, n_iters: int):
    formulas = random_variables(n_vars)
    current_formula = None
    for _ in range(n_iters):
        option = choice(["unary", "binary"])
        if option == "unary":
            Op = choice(unary_operators)
            f = choice(list(formulas))
            current_formula = Op(f)
        elif option == "binary":
            Op = choice(binary_operators)
            f1 = choice(list(formulas))
            f2 = choice(list(formulas))
            current_formula = Op(f1, f2)
        # print(current_formula)
        formulas.add(current_formula)
    return current_formula


def main():
    A = Var("A")
    B = Var("B")
    C = Var("C")
    M = Var("M")
    V = Var("V")
    H = Var("H")

    f = (B & ~((A >> V) >> (A & B))) >> Const.FALSE

    print(f)
    table = Table(f)
    print(table)
    print(pretty_print_CNF_list_of_sets(CNF_list_of_sets(f)))
    print(detect_tauto(f))


if __name__ == "__main__":
    # for _ in range(1000):
    #     f = simp_double_neg(random_formula(10, 100))
    #     print(f"{f = }")
    #     print(f"{is_tauto(f) = }")
    #     print(f"{CNF(f) = }")
    #     print(f"{pretty_print_CNF_list_of_sets(CNF_list_of_sets(f)) = }")
    #     print(f"{detect_tauto(f) = }")
    #     assert is_tauto(f) == detect_tauto(f), f"{f}"
    #     input("\n\n\n")
    # fCNF = CNF(f)
    # print(CNF(f))
    # table_CNF = Table(fCNF)
    # print(table_CNF)
    main()
