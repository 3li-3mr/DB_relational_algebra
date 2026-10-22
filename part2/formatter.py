from part2.models import Relation


class TableFormatter:
    def __init__(self) -> None:
        pass

    def to_text(self, value) -> str:
        if value is None:
            return "NULL"
        return str(value)

    def format(self, relation: Relation) -> str:
        columns = relation.columns
        if len(columns) == 0:
            return "(empty relation)"

        widths = []
        for col in columns:
            width = len(col)
            for row in relation.rows:
                text = self.to_text(row.get(col))
                if len(text) > width:
                    width = len(text)
            widths.append(width)

        lines = []

        header = []
        separator = []
        for i in range(len(columns)):
            header.append(columns[i].ljust(widths[i]))
            separator.append("-" * widths[i])
        lines.append(" | ".join(header))
        lines.append("-+-".join(separator))

        for row in relation.rows:
            cells = []
            for i in range(len(columns)):
                text = self.to_text(row.get(columns[i]))
                cells.append(text.ljust(widths[i]))
            lines.append(" | ".join(cells))

        lines.append("(" + str(len(relation.rows)) + " rows)")
        return "\n".join(lines)