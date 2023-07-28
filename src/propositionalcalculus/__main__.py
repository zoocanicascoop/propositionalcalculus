from tree_sitter import Parser
from .parser import TSLANG, parse_rules, parse_formulas


def main():
    parser = Parser()
    parser.set_language(TSLANG)

    for f in parse_formulas(parser, "../../grammar/examples/example.txt"):
        print(f)
    # for rule in parse_rules(parser, "../../grammar/examples/MP.rule"):
    #     print(rule)
    # for f in parse_formulas(parser, "../../grammar/examples/absurd.proof"):
    #     print(f)


if __name__ == "__main__":
    main()
