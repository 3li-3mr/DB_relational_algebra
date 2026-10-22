from typing import Dict, List, Set, Tuple
from part1.models import (
    Attribute,
    Column,
    ERDiagram,
    ForeignKey,
    Relationship,
    RelationalSchema,
    Table,
)


class ERToRelationalConverter:
    def __init__(self, er_diagram: ERDiagram):
        self.er_diagram = er_diagram
        self.schema = RelationalSchema()
        self.table_map: Dict[str, Table] = {}
        self.multivalued_queue: List[Tuple[str, Attribute]] = []
        self.processed_relationships: Set[int] = set()

    def convert(self) -> RelationalSchema:
        self._map_strong_entities()
        self._map_weak_entities()
        self._map_binary_1_to_1()
        self._map_binary_1_to_n()
        self._map_binary_m_to_n()
        self._map_nary_relationships()
        self._map_multivalued_attributes()
        return self.schema

    def _register_table(self, name: str) -> Table:
        table = Table(name=name)
        self.schema.tables.append(table)
        self.table_map[name] = table
        return table

    def _get_pk_columns(self, table_name: str) -> List[Column]:
        table = self.table_map[table_name]
        return [col for col in table.columns if col.is_primary_key]

    def _add_attributes(
        self,
        table: Table,
        attributes: List[Attribute],
        use_partial_as_pk: bool = False,
    ) -> None:
        for att in attributes:
            if att.is_derived:
                continue
            if att.is_multivalued:
                self.multivalued_queue.append((table.name, att))
                continue

            is_pk = (
                (att.is_partial_key or att.is_primary_key)
                if use_partial_as_pk
                else att.is_primary_key
            )

            if att.composite:
                for sub_att_name in att.composite:
                    table.columns.append(
                        Column(
                            name=sub_att_name,
                            is_primary_key=is_pk,
                            is_foreign_key=False,
                        )
                    )
            else:
                table.columns.append(
                    Column(
                        name=att.name,
                        is_primary_key=is_pk,
                        is_foreign_key=False,
                    )
                )

    def _add_foreign_key(
        self,
        target_table: Table,
        ref_table_name: str,
        as_primary_key: bool = False,
    ) -> None:
        existing_col_names = {col.name for col in target_table.columns}
        for pk_col in self._get_pk_columns(ref_table_name):
            fk_col_name = (
                f"{ref_table_name}_{pk_col.name}"
                if pk_col.name in existing_col_names
                else pk_col.name
            )
            target_table.columns.append(
                Column(
                    name=fk_col_name,
                    is_primary_key=as_primary_key,
                    is_foreign_key=True,
                )
            )
            target_table.foreign_keys.append(
                ForeignKey(
                    column_name=fk_col_name,
                    referenced_table=ref_table_name,
                    referenced_column=pk_col.name,
                )
            )
            existing_col_names.add(fk_col_name)

    def _build_identifying_map(self) -> Dict[str, List[Tuple[str, Relationship]]]:
        weak_names = {e.name for e in self.er_diagram.entities if e.is_weak}
        identifying_map: Dict[str, List[Tuple[str, Relationship]]] = {
            name: [] for name in weak_names
        }

        for rel in self.er_diagram.relationships:
            if len(rel.participants) != 2:
                continue

            p1, p2 = rel.participants[0].entity, rel.participants[1].entity
            is_ident = rel.is_identifying or (
                (p1 in weak_names) ^ (p2 in weak_names)
            )

            if not is_ident:
                continue

            if p1 in weak_names and p2 not in weak_names:
                identifying_map[p1].append((p2, rel))
            elif p2 in weak_names and p1 not in weak_names:
                identifying_map[p2].append((p1, rel))
            elif p1 in weak_names and p2 in weak_names:
                if rel.participants[0].participation.lower() == "total":
                    identifying_map[p1].append((p2, rel))
                else:
                    identifying_map[p2].append((p1, rel))

        return identifying_map

    def _map_strong_entities(self) -> None:
        for entity in self.er_diagram.entities:
            if entity.is_weak:
                continue
            table = self._register_table(entity.name)
            self._add_attributes(table, entity.attributes, use_partial_as_pk=False)

    def _map_weak_entities(self) -> None:
        identifying_map = self._build_identifying_map()
        weak_entities = [e for e in self.er_diagram.entities if e.is_weak]

        resolved = False
        while weak_entities and not resolved:
            resolved = True
            remaining = []

            for entity in weak_entities:
                owner_rels = identifying_map.get(entity.name, [])
                if any(owner not in self.table_map for owner, _ in owner_rels):
                    remaining.append(entity)
                    resolved = False
                    continue

                table = self._register_table(entity.name)
                for owner_name, rel in owner_rels:
                    self._add_foreign_key(table, owner_name, as_primary_key=True)
                    self._add_attributes(table, rel.attributes, use_partial_as_pk=False)
                    self.processed_relationships.add(id(rel))

                self._add_attributes(table, entity.attributes, use_partial_as_pk=True)

            weak_entities = remaining

    def _map_binary_1_to_1(self) -> None:
        for rel in self.er_diagram.relationships:
            if id(rel) in self.processed_relationships: continue
            if len(rel.participants) != 2: continue
            p1 = rel.participants[0]
            p2 = rel.participants[1]
            if p2.cardinality != "1" or p1.cardinality != "1": continue
            if p1.participation.lower() == 'total':
                self._add_foreign_key(self.table_map[p1.entity], p2.entity, as_primary_key=False)
                self._add_attributes(self.table_map[p1.entity], rel.attributes, use_partial_as_pk=False)
            else:
                self._add_foreign_key(self.table_map[p2.entity], p1.entity, as_primary_key=False)
                self._add_attributes(self.table_map[p2.entity], rel.attributes, use_partial_as_pk=False)
            self.processed_relationships.add(id(rel))

    def _map_binary_1_to_n(self) -> None:
        for rel in self.er_diagram.relationships:
            if id(rel) in self.processed_relationships: continue
            if len(rel.participants) != 2: continue
            p1 = rel.participants[0]
            p2 = rel.participants[1]
            if p2.cardinality != '1' and p1.cardinality != '1': continue
            if p1.cardinality != '1':
                self._add_foreign_key(self.table_map[p1.entity], p2.entity, as_primary_key=False)
                self._add_attributes(self.table_map[p1.entity], rel.attributes, use_partial_as_pk=False)
            else:
                self._add_foreign_key(self.table_map[p2.entity], p1.entity, as_primary_key=False)
                self._add_attributes(self.table_map[p2.entity], rel.attributes, use_partial_as_pk=False)
            self.processed_relationships.add(id(rel))

    def _map_binary_m_to_n(self) -> None:
        for rel in self.er_diagram.relationships:
            if id(rel) in self.processed_relationships: continue
            if len(rel.participants) != 2: continue
            p1 = rel.participants[0]
            p2 = rel.participants[1]
            table = self._register_table(rel.name)
            self._add_foreign_key(table, p1.entity, as_primary_key=True)
            self._add_foreign_key(table, p2.entity, as_primary_key=True)
            self._add_attributes(table, rel.attributes, use_partial_as_pk=False)
            self.processed_relationships.add(id(rel))

    def _map_multivalued_attributes(self) -> None:
        for owner_table_name, att in list(self.multivalued_queue):
            table_name = f"{owner_table_name}_{att.name}"
            table = self._register_table(table_name)
            self._add_foreign_key(table, owner_table_name, as_primary_key=True)

            att_copy = att.model_copy(
                update={"is_multivalued": False, "is_primary_key": True}
            )
            self._add_attributes(table, [att_copy], use_partial_as_pk=False)

    def _map_nary_relationships(self) -> None:
        for rel in self.er_diagram.relationships:
            if id(rel) in self.processed_relationships: continue
            table = self._register_table(rel.name)
            for part in rel.participants:
                self._add_foreign_key(table, part.entity, as_primary_key=True)
            self._add_attributes(table, rel.attributes, use_partial_as_pk=False)
            