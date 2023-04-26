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

    f = ~~Const.TRUE
    f = f.subs_imp
    print(f)
    f = f.push_neg
    print(f)
    f = f.distribute_or
    print(f)
    f = f.simp_const
    print(f)


if __name__ == "__main__":
    main()
