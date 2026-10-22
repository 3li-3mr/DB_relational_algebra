import argparse
import json
from pathlib import Path
from part1.models import ERDiagram
from part1.converter import ERToRelationalConverter
from part1.renderer import SchemaRenderer
from part2.models import Database
from part2.parser import QueryParser
from part2.executor import QueryExecutor
from part2.formatter import TableFormatter


def load_er_json(filepath: Path) -> ERDiagram:
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
    return ERDiagram.model_validate(data)


def load_dataset_json(filepath: Path) -> Database:
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
    return Database.from_dict(data)


def run_part1(input_path: Path, output_path: str) -> None:
    er_diagram = load_er_json(input_path)
    converter = ERToRelationalConverter(er_diagram)
    relational_schema = converter.convert()
    renderer = SchemaRenderer(relational_schema)
    renderer.render(output_path)


def run_part2(data_path: Path, query_str: str) -> None:
    database = load_dataset_json(data_path)
    parser = QueryParser()
    ast = parser.parse(query_str)
    executor = QueryExecutor(database)
    result_relation = executor.execute(ast)
    formatter = TableFormatter()
    print(formatter.format(result_relation))


def main() -> None:
    parser = argparse.ArgumentParser(description="Database Systems Lab 2")
    subparsers = parser.add_subparsers(dest="part", required=True)

    p1_parser = subparsers.add_parser("part1")
    p1_parser.add_argument("input", type=Path)
    p1_parser.add_argument("-o", "--output", type=str, default="relational_schema")

    p2_parser = subparsers.add_parser("part2")
    p2_parser.add_argument("dataset", type=Path)
    p2_parser.add_argument("query", type=str)

    args = parser.parse_args()

    if args.part == "part1":
        run_part1(args.input, args.output)
    elif args.part == "part2":
        run_part2(args.dataset, args.query)


if __name__ == "__main__":
    main()