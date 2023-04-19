from . import *
from random import choice
from string import ascii_letters


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

    f = Imp(And(B, Neg(Imp(Imp(A, V), And(C, H)))), Const.FALSE)
    # f = Imp(And(Neg(M),H), Neg(V))
    # f = Or(A, B)

    # print(f)
    # table = Table(f)
    # print(table)
    # print(table.truth_list)

    # table_CNF = Table(CNF(f))
    # print(table_CNF)
    # print(table_CNF.truth_list)

    # print(table.truth_list == table_CNF.truth_list)

    print(f)
    print(CNF(f))
    print(CNF_list_of_sets(f))
    # print(format_table(table(CNF(f))))

    # print(format_table(table(f)))


if __name__ == "__main__":
    for _ in range(1000):
        f = simp_double_neg(random_formula(10, 100))
        print(f"{f = }")
        print(f"{is_tauto(f) = }")
        print(f"{CNF(f) = }")
        print(f"{pretty_print_CNF_list_of_sets(CNF_list_of_sets(f)) = }")
        print(f"{detect_tauto(f) = }")
        assert is_tauto(f) == detect_tauto(f), f"{f}"
        input("\n\n\n")
    # fCNF = CNF(f)
    # print(CNF(f))
    # table_CNF = Table(fCNF)
    # print(table_CNF)
    # main()
