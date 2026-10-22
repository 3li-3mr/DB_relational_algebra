import html
from typing import Dict, List, Optional, Tuple
import graphviz
from part1.models import RelationalSchema, Table


class SchemaRenderer:
    def __init__(self, schema: RelationalSchema):
        self.schema = schema
        self.dot = graphviz.Digraph(
            name="RelationalSchema",
            engine="neato",
            format="png",
            graph_attr={
                "splines": "polyline",
                "pad": "0.6",
                "fontname": "Helvetica",
                "dpi": "150",
            },
            node_attr={
                "shape": "plaintext",
                "fontname": "Helvetica",
                "fontsize": "11",
                "margin": "0",
            },
            edge_attr={
                "fontname": "Helvetica",
                "fontsize": "9",
                "arrowhead": "normal",
                "arrowsize": "0.7",
                "color": "#1E293B",
                "penwidth": "1.1",
            },
        )
        self.table_y: Dict[str, float] = {}
        self.table_width: Dict[str, float] = {}
        self.col_center_x: Dict[Tuple[str, str], float] = {}
        self._waypoint_counter = 0

    def _estimate_col_width_pt(self, col_name: str) -> float:
        # Approximate pixel/point width for 11pt Helvetica + CELLPADDING="7"
        return max(len(col_name) * 7.2 + 20.0, 48.0)

    def _compute_geometry(self) -> float:
        row_spacing = 95.0  # Vertical distance between tables in points
        max_table_width = 0.0

        for idx, table in enumerate(self.schema.tables):
            y_center = -idx * row_spacing
            self.table_y[table.name] = y_center

            current_x = 0.0
            for col in table.columns:
                w = self._estimate_col_width_pt(col.name)
                self.col_center_x[(table.name, col.name)] = current_x + (w / 2.0)
                current_x += w

            total_w = max(current_x, 60.0)
            self.table_width[table.name] = total_w
            if total_w > max_table_width:
                max_table_width = total_w

        return max_table_width

    def _build_horizontal_table_node(self, table: Table) -> None:
        escaped_table_name = html.escape(table.name)
        col_count = max(len(table.columns), 1)

        cells = []
        for col in table.columns:
            port_name = html.escape(col.name)
            display_name = html.escape(col.name)
            col_w = int(round(self._estimate_col_width_pt(col.name)))

            if col.is_primary_key:
                display_name = f"<U>{display_name}</U>"

            bg_color = "#BAE6FD" if col.is_foreign_key else "#D9D9D9"
            cells.append(
                f'<TD PORT="{port_name}" FIXEDSIZE="TRUE" WIDTH="{col_w}" HEIGHT="24" '
                f'BGCOLOR="{bg_color}" BORDER="1" CELLPADDING="5">{display_name}</TD>'
            )

        if not cells:
            cells.append(
                '<TD FIXEDSIZE="TRUE" WIDTH="60" HEIGHT="24" BGCOLOR="#D9D9D9" '
                'BORDER="1" CELLPADDING="5"><I>(empty)</I></TD>'
            )

        columns_row = "".join(cells)

        label = (
            f'<<TABLE BORDER="0" CELLBORDER="0" CELLSPACING="0" CELLPADDING="0">'
            f'<TR><TD COLSPAN="{col_count}" ALIGN="LEFT" HEIGHT="20" VALIGN="BOTTOM">'
            f'<B>{escaped_table_name}</B></TD></TR>'
            f'<TR><TD COLSPAN="{col_count}" HEIGHT="4"></TD></TR>'
            f"<TR>{columns_row}</TR>"
            f"</TABLE>>"
        )

        # In neato, pos is in inches (72 points = 1 inch) and refers to the node center.
        # Since node height is 48pt (20 + 4 + 24), shifting x by table_width / 2 left-aligns all tables at x = 0!
        cx_inches = (self.table_width[table.name] / 2.0) / 72.0
        cy_inches = self.table_y[table.name] / 72.0

        self.dot.node(
            table.name,
            label=label,
            pos=f"{cx_inches:.4f},{cy_inches:.4f}!",
        )

    def _add_waypoint(self, x_pt: float, y_pt: float) -> str:
        self._waypoint_counter += 1
        wp_name = f"_wp_{self._waypoint_counter}"
        x_in = x_pt / 72.0
        y_in = y_pt / 72.0
        self.dot.node(
            wp_name,
            label="",
            shape="point",
            width="0",
            height="0",
            style="invis",
            pos=f"{x_in:.4f},{y_in:.4f}!",
        )
        return wp_name

    def _draw_orthogonal_chain(self, points_pt: List[Tuple[float, float]]) -> None:
        wp_names = [self._add_waypoint(x, y) for x, y in points_pt]
        for i in range(len(wp_names) - 1):
            is_last = i == len(wp_names) - 2
            self.dot.edge(
                wp_names[i],
                wp_names[i + 1],
                arrowhead="normal" if is_last else "none",
            )

    def _build_all_foreign_key_edges(self, max_table_width: float) -> None:
        table_index = {t.name: i for i, t in enumerate(self.schema.tables)}

        # Collect all FKs and count how many incoming FKs target each (table, column)
        all_fks: List[Tuple[str, str, str, str]] = []
        incoming_Map: Dict[Tuple[str, str], List[int]] = {}

        for table in self.schema.tables:
            for fk in table.foreign_keys:
                idx = len(all_fks)
                all_fks.append(
                    (table.name, fk.column_name, fk.referenced_table, fk.referenced_column)
                )
                target_key = (fk.referenced_table, fk.referenced_column)
                incoming_Map.setdefault(target_key, []).append(idx)

        # Sort incoming edges per target PK so their arrowheads don't cross
        target_x_offset: Dict[int, float] = {}
        for target_key, fk_indices in incoming_Map.items():
            count = len(fk_indices)
            spacing = 7.0
            for rank, fk_idx in enumerate(fk_indices):
                offset = (rank - (count - 1) / 2.0) * spacing
                target_x_offset[fk_idx] = offset

        # Track vertical channels on the right and horizontal tracks per table gap
        right_channel_idx = 0
        gap_track_counts: Dict[int, int] = {}

        for fk_idx, (src_table, src_col, dst_table, dst_col) in enumerate(all_fks):
            src_idx = table_index[src_table]
            dst_idx = table_index[dst_table]

            # Bottom of row cells is at y_center - 24pt
            src_x = self.col_center_x[(src_table, src_col)]
            src_bottom_y = self.table_y[src_table] - 24.0

            dst_x = self.col_center_x[(dst_table, dst_col)] + target_x_offset.get(fk_idx, 0.0)
            dst_bottom_y = self.table_y[dst_table] - 24.0

            # Allocate horizontal track below source table
            src_track_num = gap_track_counts.get(src_idx, 0)
            gap_track_counts[src_idx] = src_track_num + 1
            src_drop_y = src_bottom_y - 12.0 - (src_track_num * 8.0)

            # Case 1: Self-referencing (recursive) FK on the same table (e.g., Super_ssn -> Ssn)
            if src_idx == dst_idx:
                if abs(src_x - dst_x) < 4.0:
                    src_x += 6.0
                points = [
                    (src_x, src_bottom_y),
                    (src_x, src_drop_y),
                    (dst_x, src_drop_y),
                    (dst_x, dst_bottom_y),
                ]
                self._draw_orthogonal_chain(points)
                continue

            # Case 2: Source is directly below Target (src_idx == dst_idx + 1) and doesn't get blocked
            # Wait: if src is BELOW dst, the space between src_bottom_y and dst_bottom_y has the src table itself in the way!
            # So ANY edge going to a different table (or around the current table's row box) must route to the right of the intervening tables, UNLESS dst is directly BELOW src (dst_idx == src_idx + 1) AND no table blocks it.
            min_idx = min(src_idx, dst_idx)
            max_idx = max(src_idx, dst_idx)

            # Find max width of tables that lie vertically between src_drop_y and dst_drop_y
            # A table k's box occupies y from table_y[k] + 24 down to table_y[k] - 24.
            dst_track_num = gap_track_counts.get(dst_idx, 0)
            gap_track_counts[dst_idx] = dst_track_num + 1
            dst_drop_y = dst_bottom_y - 12.0 - (dst_track_num * 8.0)

            # Check if a direct vertical segment at dst_x (or src_x) from src_drop_y to dst_drop_y intersects any table
            # Tables between src and dst inclusive (specifically any table whose y-interval [y-24, y+24] overlaps [min(src_drop_y, dst_drop_y), max(src_drop_y, dst_drop_y)])
            y_low = min(src_drop_y, dst_drop_y)
            y_high = max(src_drop_y, dst_drop_y)

            max_blocking_width = 0.0
            for t in self.schema.tables:
                ty = self.table_y[t.name]
                if (ty - 26.0) <= y_high and (ty + 26.0) >= y_low:
                    if self.table_width[t.name] > max_blocking_width:
                        max_blocking_width = self.table_width[t.name]

            # If both src_x and dst_x are to the right of all intermediate tables, or if we use a clean right-hand channel:
            # Wait: in the textbook diagram, if a table below references a table immediately above (like DEPT_LOCATIONS -> DEPARTMENT or PROJECT -> DEPARTMENT or WORKS_ON -> PROJECT), does it go left/right or straight up?
            # Look at DEPT_LOCATIONS (Dnumber) -> DEPARTMENT (Dnumber) in image_23fdda.png:
            # Because DEPT_LOCATIONS itself sits between DEPT_LOCATIONS's bottom and DEPARTMENT's bottom, the line drops down from DEPT_LOCATIONS.Dnumber, goes right past the end of DEPT_LOCATIONS, goes UP into the gap below DEPARTMENT, goes left to DEPARTMENT.Dnumber, and points UP into DEPARTMENT.Dnumber!
            channel_x = max_blocking_width + 18.0 + (right_channel_idx * 10.0)
            right_channel_idx += 1

            points = [
                (src_x, src_bottom_y),
                (src_x, src_drop_y),
                (channel_x, src_drop_y),
                (channel_x, dst_drop_y),
                (dst_x, dst_drop_y),
                (dst_x, dst_bottom_y),
            ]
            self._draw_orthogonal_chain(points)

    def render(self, output_path: str) -> Optional[str]:
        max_w = self._compute_geometry()

        for table in self.schema.tables:
            self._build_horizontal_table_node(table)

        self._build_all_foreign_key_edges(max_w)

        return self.dot.render(filename=output_path, cleanup=True)