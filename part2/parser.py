from part2.models import QueryNode


class QueryParser:
    def __init__(self) -> None:
        pass

    def tokenize(self, query: str) -> list[str]:
        pass

    def parse(self, query: str) -> QueryNode:
        pass