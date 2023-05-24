from collections.abc import Callable
from functools import wraps
from pathlib import Path
from typing import Any

from tree_sitter import Language, Node, Parser

from .formula import (
    And,
    Const,
    Formula,
    Imp,
    Neg,
    Or,
    Var,
)

PATH = Path(__file__).parent
PARSER_LIB = "grammar/build/parser.so"

Language.build_library(PARSER_LIB, ["grammar"])

TSLANG = Language(PARSER_LIB, "propositionalcalculus")


missing_nodes = []


def traverse_tree(node: Node):
    global missing_nodes
    print(node.type)
    for n in node.children:
        if n.is_missing:
            missing_nodes.append(n)
        traverse_tree(n)


def parse_formula(node: Node) -> Formula:
    match node.type:
        case "formula":
            return parse_formula(node.children[0])
        case "var":
            return Var(node.text.decode())
        case "const":
            match node.text.decode():
                case "T":
                    return Const.TRUE
                case "F":
                    return Const.FALSE
                case _:
                    raise ValueError("Unreachable")
        case "neg":
            assert len(node.children) == 2, f"{node.children}"
            return Neg(parse_formula(node.children[1]))
        case "and":
            f1 = node.child_by_field_name("left")
            f2 = node.child_by_field_name("right")
            assert f1 is not None and f2 is not None
            return And(parse_formula(f1), parse_formula(f2))
        case "or":
            f1 = node.child_by_field_name("left")
            f2 = node.child_by_field_name("right")
            assert f1 is not None and f2 is not None
            return Or(parse_formula(f1), parse_formula(f2))
        case "imp":
            f1 = node.child_by_field_name("left")
            f2 = node.child_by_field_name("right")
            assert f1 is not None and f2 is not None
            return Imp(parse_formula(f1), parse_formula(f2))
        case "(":
            raise NotImplementedError()
        case ")":
            raise NotImplementedError()
        case _:
            raise ValueError(f"Unreachable: {node.type = }")


def parse_rule(node: Node):
    id = node.child_by_field_name("id")
    assert id is not None
    id = id.text.decode()
    assumptions = list(
        map(
            lambda n: parse_formula(n),
            filter(
                lambda n: n.type == "formula",
                node.children_by_field_name("assumptions"),
            ),
        )
    )
    conclusion = node.child_by_field_name("conclusion")
    assert conclusion is not None
    conclusion = parse_formula(conclusion)
    return (id, assumptions, conclusion)


def file_parser(fn: Callable[[list[tuple[Node, str]]], Any]):
    @wraps(fn)
    def result(parser: Parser, path: str):
        with open(PATH / path, "rb") as f:
            tree = parser.parse(f.read())
        with open(PATH / "../../grammar/queries/python-bindings.scm", "r") as f:
            query = TSLANG.query(f.read())

        captures: list[tuple[Node, str]] = query.captures(tree.root_node)
        return fn(captures)

    return result


@file_parser
def parse_formulas(captures: list[tuple[Node, str]]):
    return map(
        lambda e: (e[0], parse_formula(e[0])), filter(lambda e: e[1] == "formula", captures)
    )


@file_parser
def parse_rules(captures: list[tuple[Node, str]]):
    return map(lambda e: parse_rule(e[0]), filter(lambda e: e[1] == "rule", captures))


def main():
    global missing_nodes
    parser = Parser()
    parser.set_language(TSLANG)

    for node, f in parse_formulas(parser, "../../grammar/examples/example.txt"):
        print(f'"{node.text.decode()}"  =>  {f}')
    for rule in parse_rules(parser, "../../grammar/examples/MP.rule"):
        print(rule)


if __name__ == "__main__":
    main()
