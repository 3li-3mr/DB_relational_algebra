from part2.models import QueryNode

CHILD_COUNT = {
    "SELECT": 1,
    "PROJECT": 1,
    "AGGREGATE": 1,
    "JOIN": 2,
    "UNION": 2,
    "INTERSECT": 2,
    "DIFFERENCE": 2,
}

NEEDS_ARGUMENTS = ["SELECT", "PROJECT", "AGGREGATE", "JOIN"]


class QueryParser:
    def __init__(self) -> None:
        self.tokens = []
        self.pos = 0

    def tokenize(self, query: str) -> list[str]:
        tokens = []
        i = 0
        while i < len(query):
            c = query[i]
            if c == " ":
                i += 1
            elif c in "(),":
                tokens.append(c)
                i += 1
            elif c == "[":
                end = query.find("]", i)
                if end == -1:
                    raise ValueError("Missing closing ']'")
                tokens.append(query[i : end + 1])
                i = end + 1
            else:
                start = i
                while i < len(query) and query[i] not in "()[], ":
                    i += 1
                tokens.append(query[start:i])
        return tokens

    def parse(self, query: str) -> QueryNode:
        self.tokens = self.tokenize(query)
        self.pos = 0
        if len(self.tokens) == 0:
            raise ValueError("Empty query")
        node = self.parse_node()
        if self.pos < len(self.tokens):
            raise ValueError("Unexpected extra text: " + self.tokens[self.pos])
        return node

    def peek(self) -> str:
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return ""

    def next_token(self) -> str:
        if self.pos >= len(self.tokens):
            raise ValueError("Query ended unexpectedly")
        token = self.tokens[self.pos]
        self.pos += 1
        return token

    def parse_node(self) -> QueryNode:
        name = self.next_token()
        if name in ["(", ")", ","] or name.startswith("["):
            raise ValueError("Expected a name but found " + name)

        arguments = None
        if self.peek().startswith("["):
            text = self.next_token()
            arguments = text[1:-1].strip()

        if self.peek() != "(":
            if arguments is not None:
                raise ValueError("Unexpected [...] after " + name)
            return QueryNode(operation="RELATION", arguments=name)

        operation = name.upper()
        if operation not in CHILD_COUNT:
            raise ValueError("Unknown operation: " + name)

        self.next_token()
        children = [self.parse_node()]
        while self.peek() == ",":
            self.next_token()
            children.append(self.parse_node())
        if self.next_token() != ")":
            raise ValueError("Expected ')' in " + operation)

        if len(children) != CHILD_COUNT[operation]:
            raise ValueError(operation + " needs " + str(CHILD_COUNT[operation]) + " table(s)")
        if operation in NEEDS_ARGUMENTS and not arguments:
            raise ValueError(operation + " needs arguments in [...]")

        return QueryNode(operation=operation, arguments=arguments, children=children)