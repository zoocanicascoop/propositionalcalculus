from . import *


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

    print(f)
    table = Table(f)
    print(table)
    print(table.truth_list)

    table_CNF = Table(CNF(f))
    print(table_CNF)
    print(table_CNF.truth_list)

    print(table.truth_list == table_CNF.truth_list)

    # print(CNF(f))
    # print(format_table(table(CNF(f))))

    # print(format_table(table(f)))


if __name__ == "__main__":
    main()
