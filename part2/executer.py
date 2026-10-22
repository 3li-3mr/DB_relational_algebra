from part2.models import Database, QueryNode, Relation


class QueryExecutor:
    def __init__(self, database: Database) -> None:
        self.database = database

    def execute(self, node: QueryNode) -> Relation:
        pass

    def _select(self, relation: Relation, condition: str) -> Relation:
        pass

    def _project(self, relation: Relation, columns_str: str) -> Relation:
        pass

    def _join(self, left: Relation, right: Relation, condition: str) -> Relation:
        pass

    def _union(self, left: Relation, right: Relation) -> Relation:
        pass

    def _intersect(self, left: Relation, right: Relation) -> Relation:
        pass

    def _difference(self, left: Relation, right: Relation) -> Relation:
        pass

    def _aggregate(self, relation: Relation, spec: str) -> Relation:
        pass