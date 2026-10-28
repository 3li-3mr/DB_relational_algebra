from part2.condition import Condition
from part2.models import Database, QueryNode, Relation


class QueryExecutor:
    def __init__(self, database: Database) -> None:
        self.database = database
        self.operations = {
            "SELECT": self._select,
            "PROJECT": self._project,
            "JOIN": self._join,
            "UNION": self._union,
            "INTERSECT": self._intersect,
            "DIFFERENCE": self._difference,
            "AGGREGATE": self._aggregate,
        }

    def execute(self, node: QueryNode) -> Relation:
        if node.operation == "RELATION":
            if node.arguments not in self.database.tables:
                raise ValueError("Unknown table: " + str(node.arguments))
            return self.database.tables[node.arguments]

        inputs = []
        for child in node.children:
            inputs.append(self.execute(child))
        if node.arguments is not None:
            inputs.append(node.arguments)
        return self.operations[node.operation](*inputs)
    
    def _find_column(self, relation: Relation, name: str) -> str:
        if name in relation.columns:
            return name
        if "." in name:
            short = name.split(".")[-1]
            if short in relation.columns:
                return short
        raise ValueError("Unknown column: " + name)

    def _row_key(self, row: dict, columns: list) -> tuple:
        values = []
        for col in columns:
            values.append(row.get(col))
        return tuple(values)

    def _normalize_set_operands(self, left: Relation, right: Relation) -> tuple[list[str], list[dict]]:
        if len(left.columns) != len(right.columns):
            raise ValueError("Relations must have the same number of columns for set operations")

        columns = list(left.columns)
        if set(left.columns) == set(right.columns):
            right_rows = [{col: row.get(col) for col in columns} for row in right.rows]
        else:
            right_rows = [
                {columns[i]: row.get(right.columns[i]) for i in range(len(columns))}
                for row in right.rows
            ]
        return columns, right_rows

    def _select(self, relation: Relation, condition: str) -> Relation:
        cond = Condition(condition)
        rows = []
        for row in relation.rows:
            if cond.matches(row):
                rows.append(dict(row))
        return Relation(name=relation.name, columns=list(relation.columns), rows=rows)

    def _project(self, relation: Relation, columns_str: str) -> Relation:
        columns = []
        for name in columns_str.split(","):
            columns.append(self._find_column(relation, name.strip()))

        rows = []
        seen = set()
        for row in relation.rows:
            key = self._row_key(row, columns)
            if key in seen:
                continue
            seen.add(key)
            new_row = {}
            for col in columns:
                new_row[col] = row.get(col)
            rows.append(new_row)
        return Relation(name=relation.name, columns=columns, rows=rows)

    def _join(self, left: Relation, right: Relation, condition: str = None) -> Relation:
        if condition is None:
            return self._natural_join(left, right)
        return self._theta_join(left, right, condition)

    def _natural_join(self, left: Relation, right: Relation) -> Relation:
        common = []
        for col in left.columns:
            if col in right.columns:
                common.append(col)

        columns = list(left.columns)
        for col in right.columns:
            if col not in common:
                columns.append(col)

        rows = []
        for l_row in left.rows:
            for r_row in right.rows:
                match = True
                for col in common:
                    if l_row.get(col) != r_row.get(col):
                        match = False
                        break
                if match:
                    new_row = dict(l_row)
                    for col in right.columns:
                        if col not in common:
                            new_row[col] = r_row.get(col)
                    rows.append(new_row)
        return Relation(name="", columns=columns, rows=rows)

    def _theta_join(self, left: Relation, right: Relation, condition: str) -> Relation:
        cond = Condition(condition)
        left_name = left.name or "left"
        right_name = right.name or "right"
        if left_name == right_name:
            left_name = left_name + "_1"
            right_name = right_name + "_2"

        left_out = []
        for col in left.columns:
            if col in right.columns:
                left_out.append(left_name + "." + col)
            else:
                left_out.append(col)
        right_out = []
        for col in right.columns:
            if col in left.columns:
                right_out.append(right_name + "." + col)
            else:
                right_out.append(col)
        columns = left_out + right_out

        rows = []
        for l_row in left.rows:
            for r_row in right.rows:
                new_row = {}
                lookup = {}
                for i in range(len(left.columns)):
                    value = l_row.get(left.columns[i])
                    new_row[left_out[i]] = value
                    lookup[left_out[i]] = value
                    lookup[left_name + "." + left.columns[i]] = value
                for i in range(len(right.columns)):
                    value = r_row.get(right.columns[i])
                    new_row[right_out[i]] = value
                    lookup[right_out[i]] = value
                    lookup[right_name + "." + right.columns[i]] = value
                if cond.matches(lookup):
                    rows.append(new_row)
        return Relation(name="", columns=columns, rows=rows)

    def _union(self, left: Relation, right: Relation) -> Relation:
        columns, right_rows = self._normalize_set_operands(left, right)
        rows = []
        seen = set()
        for row in left.rows + right_rows:
            key = self._row_key(row, columns)
            if key not in seen:
                seen.add(key)
                new_row = {col: row.get(col) for col in columns}
                rows.append(new_row)
        return Relation(name="", columns=columns, rows=rows)

    def _intersect(self, left: Relation, right: Relation) -> Relation:
        columns, right_rows = self._normalize_set_operands(left, right)
        right_keys = {self._row_key(row, columns) for row in right_rows}

        rows = []
        seen = set()
        for row in left.rows:
            key = self._row_key(row, columns)
            if key in right_keys and key not in seen:
                seen.add(key)
                rows.append({col: row.get(col) for col in columns})
        return Relation(name="", columns=columns, rows=rows)

    def _difference(self, left: Relation, right: Relation) -> Relation:
        columns, right_rows = self._normalize_set_operands(left, right)
        right_keys = {self._row_key(row, columns) for row in right_rows}

        rows = []
        seen = set()
        for row in left.rows:
            key = self._row_key(row, columns)
            if key not in right_keys and key not in seen:
                seen.add(key)
                rows.append({col: row.get(col) for col in columns})
        return Relation(name="", columns=columns, rows=rows)

    def _aggregate(self, relation: Relation, spec: str) -> Relation:
        if ";" in spec:
            group_part, agg_part = spec.split(";", 1)
        else:
            group_part, agg_part = "", spec

        group_cols = []
        for name in group_part.split(","):
            if name.strip() != "":
                group_cols.append(self._find_column(relation, name.strip()))

        aggregates = []
        for item in agg_part.split(","):
            item = item.strip()
            open_pos = item.find("(")
            if open_pos == -1 or not item.endswith(")"):
                raise ValueError("Bad aggregate: " + item)
            func = item[:open_pos].strip().upper()
            arg = item[open_pos + 1 : -1].strip()
            if func not in ["SUM", "AVG", "MIN", "MAX", "COUNT"]:
                raise ValueError("Unknown aggregate function: " + func)
            if arg != "*":
                arg = self._find_column(relation, arg)
            aggregates.append((func, arg, func + "(" + arg + ")"))

        groups = {}
        for row in relation.rows:
            key = self._row_key(row, group_cols)
            if key not in groups:
                groups[key] = []
            groups[key].append(row)
        if len(group_cols) == 0 and len(groups) == 0:
            groups[()] = []

        columns = list(group_cols)
        for agg in aggregates:
            columns.append(agg[2])

        rows = []
        for key in groups:
            group_rows = groups[key]
            new_row = {}
            for i in range(len(group_cols)):
                new_row[group_cols[i]] = key[i]
            for func, arg, label in aggregates:
                new_row[label] = self._compute(func, arg, group_rows)
            rows.append(new_row)
        return Relation(name="", columns=columns, rows=rows)

    def _compute(self, func: str, arg: str, rows: list):
        if func == "COUNT" and arg == "*":
            return len(rows)
        if arg == "*":
            raise ValueError(func + "(*) is not allowed")

        values = []
        for row in rows:
            if row.get(arg) is not None:
                values.append(row[arg])

        if func == "COUNT":
            return len(values)
        if len(values) == 0:
            return None
        if func == "SUM":
            return sum(values)
        if func == "AVG":
            return sum(values) / len(values)
        if func == "MIN":
            return min(values)
        return max(values)