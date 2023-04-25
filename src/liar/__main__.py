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
    # print(f.str_polish)
    # print(Table(f))
    # print(Formula.print_CNF_structured(f.CNF_structured))
    graph = f._graph_rec()
    graph.render('./tmp-graph.gv', view=True)
    # print(pretty_print_CNF_list_of_sets(CNF_list_of_sets(f)))
    # print(detect_tauto(f))

def main2():
    for _ in range(1000):
        f = Formula.random(10, 100)
        assert isinstance(f, Formula)
        f = f.simp_double_neg
        print(f"{f = }")
        # print(f"{is_tauto(f) = }")
        # print(f"CNF(f): {Formula.print_CNF_structured(f.CNF_structured)}")
        # print(f"{f.is_tauto = }")
        print(f"{f.str_polish = }")
        # print(f"{Formula.parse_polish_rec(f.str_polish) = }")
        # assert is_tauto(f) == f.is_tauto, f"{f}"
        graph = f.render_graph()
        input("\n")

def main3():
    A = Var("A")
    f = ~~(A | ~~ A)
    print(f)
    print(f.simp_double_neg)
    print(len(f))
    print(f.vars)


if __name__ == "__main__":
    # main()
    # fCNF = CNF(f)
    # print(CNF(f))
    # table_CNF = Table(fCNF)
    # print(table_CNF)
    # main()

    # main3()

    A = Var("A")
    B = Var("B")
    C = Var("C")
    V = Var("V")
    # f = A & ~(B >> (A >> Const.TRUE))
    # f = (B | ~((A | V) | (A | B))) | C
    f = ~((A >> V) >> (A & B))
    # f = A | (B >> Const.FALSE)
    for _ in range(1000):
        f = Formula.random(10, 100)
        # f.render_graph()
        f.CNF.render_graph()
        if f.push_neg == f.push_neg_old:
            continue
        print(f"{f              = }")
        print(f"{f.push_neg     = }")
        print(f"{f.push_neg_old = }")
        input()
    # # .render('./tmp-graph.gv', view=True)
