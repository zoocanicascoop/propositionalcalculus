from tree_sitter import Parser
from .parser import TSLANG, parse_rules, parse_formulas


def main():
    parser = Parser()
    parser.set_language(TSLANG)

    for node, f in parse_formulas(parser, "../../grammar/examples/example.txt"):
        print(f'"{node.text.decode()}"  =>  {f}')
    for rule in parse_rules(parser, "../../grammar/examples/MP.rule"):
        print(rule)


if __name__ == "__main__":
    main()
