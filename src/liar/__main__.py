from . import *
from random import choice
from string import ascii_letters



def random_variable():
    return Var(choice("ABCDEGHIJKLMNOPQRSVWXYZ").upper())

def random_variables(n: int):
    vars = set()
    while len(vars)<n:
        vars.add(random_variable())
    return vars

def random_formula(formulas: set[Formula]=set()):
    if formulas == set():
        option = choice(['var', 'const' ])

    option = choice(['unary', 'binary' ])
    if option == 'unary':
        op = choice(unary_operators)
    elif option == 'binary':
        op = choice(binary_operators)



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
    # main()
    print(random_variables(10))
