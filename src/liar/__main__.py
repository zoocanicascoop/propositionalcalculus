from . import *
from random import choice


def main():
    A = Var("A")
    B = Var("B")
    C = Var("C")
    M = Var("M")
    V = Var("V")
    H = Var("H")

    f = (B & ~((A >> V) >> (A & B))) >> Const.FALSE

    print(f)
    print(f.vars)
    print(len(A))
    # table = Table(f)
    # print(table)
    print(f.CNF)
    print(f.CNF_structured)
    # print(pretty_print_CNF_list_of_sets(CNF_list_of_sets(f)))
    # print(detect_tauto(f))


if __name__ == "__main__":
    for _ in range(1000):
        f = Formula.random(10, 100)
        assert isinstance(f, Formula)
        f = f.simp_double_neg
        print(f"{f = }")
        print(f"{is_tauto(f) = }")
        print(f"CNF(f): {Formula.print_CNF_structured(f.CNF_structured)}")
        print(f"{f.is_tauto = }")
        assert is_tauto(f) == f.is_tauto, f"{f}"
        input("\n\n\n")
    # fCNF = CNF(f)
    # print(CNF(f))
    # table_CNF = Table(fCNF)
    # print(table_CNF)
    # main()
