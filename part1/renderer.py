from typing import Optional
import graphviz
from part1.models import RelationalSchema, Table


class SchemaRenderer:
    def __init__(self, schema: RelationalSchema):
        self.schema = schema
        self.dot = graphviz.Digraph(format="png")

    def _build_horizontal_table_node(self, table: Table) -> None:
        pass

    def _build_foreign_key_edges(self, table: Table) -> None:
        pass

    def render(self, output_path: str) -> Optional[str]:
        pass