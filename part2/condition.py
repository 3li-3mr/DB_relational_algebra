class Condition:
    """Parses a condition like: (Salary > 5000 AND DeptID = 10) OR NOT Name = 'Ali'"""

    def __init__(self, text: str) -> None:
        self.tokens = self.tokenize(text)
        self.pos = 0
        self.tree = self.parse_or()
        if self.pos < len(self.tokens):
            raise ValueError("Unexpected text in condition: " + str(self.tokens[self.pos][1]))

    def tokenize(self, text: str) -> list:
        tokens = []
        i = 0
        while i < len(text):
            c = text[i]
            if c == " ":
                i += 1
            elif c == "(" or c == ")":
                tokens.append(("paren", c))
                i += 1
            elif c == "'" or c == '"':
                end = text.find(c, i + 1)
                if end == -1:
                    raise ValueError("Missing closing quote in condition")
                tokens.append(("str", text[i + 1 : end]))
                i = end + 1
            elif c in "<>=!":
                start = i
                while i < len(text) and text[i] in "<>=!":
                    i += 1
                op = text[start:i]
                if op not in ["=", "!=", "<>", "<", "<=", ">", ">="]:
                    raise ValueError("Unknown operator: " + op)
                tokens.append(("op", op))
            else:
                start = i
                while i < len(text) and text[i] not in " ()'\"<>=!":
                    i += 1
                word = text[start:i]
                if word.upper() in ["AND", "OR", "NOT"]:
                    tokens.append(("kw", word.upper()))
                else:
                    number = self.to_number(word)
                    if number is None:
                        tokens.append(("word", word))
                    else:
                        tokens.append(("num", number))
        return tokens

    def to_number(self, word: str):
        try:
            return int(word)
        except ValueError:
            pass
        try:
            return float(word)
        except ValueError:
            return None

    def peek(self):
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return (None, None)

    def next_token(self):
        if self.pos >= len(self.tokens):
            raise ValueError("Condition ended unexpectedly")
        token = self.tokens[self.pos]
        self.pos += 1
        return token

    def parse_or(self):
        left = self.parse_and()
        while self.peek() == ("kw", "OR"):
            self.next_token()
            right = self.parse_and()
            left = ("or", left, right)
        return left

    def parse_and(self):
        left = self.parse_not()
        while self.peek() == ("kw", "AND"):
            self.next_token()
            right = self.parse_not()
            left = ("and", left, right)
        return left

    def parse_not(self):
        if self.peek() == ("kw", "NOT"):
            self.next_token()
            return ("not", self.parse_not())
        return self.parse_primary()

    def parse_primary(self):
        if self.peek() == ("paren", "("):
            self.next_token()
            node = self.parse_or()
            if self.next_token() != ("paren", ")"):
                raise ValueError("Expected ')' in condition")
            return node
        left = self.parse_operand()
        kind, op = self.next_token()
        if kind != "op":
            raise ValueError("Expected a comparison operator, found " + str(op))
        right = self.parse_operand()
        return ("cmp", left, op, right)

    def parse_operand(self):
        kind, value = self.next_token()
        if kind == "word":
            return ("col", value)
        if kind == "num" or kind == "str":
            return ("value", value)
        raise ValueError("Expected a column or a value, found " + str(value))

    def matches(self, row: dict) -> bool:
        return self.evaluate(self.tree, row)

    def evaluate(self, node, row: dict) -> bool:
        kind = node[0]
        if kind == "or":
            return self.evaluate(node[1], row) or self.evaluate(node[2], row)
        if kind == "and":
            return self.evaluate(node[1], row) and self.evaluate(node[2], row)
        if kind == "not":
            return not self.evaluate(node[1], row)

        left = self.get_value(node[1], row)
        right = self.get_value(node[3], row)
        op = node[2]
        if op == "=":
            return left == right
        if op == "!=" or op == "<>":
            return left != right
        if left is None or right is None:
            return False
        try:
            if op == "<":
                return left < right
            if op == "<=":
                return left <= right
            if op == ">":
                return left > right
            return left >= right
        except TypeError:
            return False
    def get_value(self, operand, row: dict):
        kind, value = operand
        if kind == "value":
            return value
        if value in row:
            return row[value]
        if "." in value:
            short = value.split(".")[-1]
            if short in row:
                return row[short]
        raise ValueError("Unknown or ambiguous column: " + value)