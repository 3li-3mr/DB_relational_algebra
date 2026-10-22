import argparse
import json
from pathlib import Path
from part1.models import ERDiagram
from part1.converter import ERToRelationalConverter
from part1.renderer import SchemaRenderer


def load_er_json(filepath: Path) -> ERDiagram:
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
    return ERDiagram.model_validate(data)


def main() -> None:
    parser = argparse.ArgumentParser(description="Part 1: ERD-to-Relational Model Visual Converter")
    parser.add_argument("input", type=Path, help="Path to input ERD JSON file")
    parser.add_argument("-o", "--output", type=str, default="relational_schema", help="Output filename without extension")
    args = parser.parse_args()

    er_diagram = load_er_json(args.input)

    converter = ERToRelationalConverter(er_diagram)
    relational_schema = converter.convert()

    renderer = SchemaRenderer(relational_schema)
    renderer.render(args.output)


if __name__ == "__main__":
    main()