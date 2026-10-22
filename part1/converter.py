from part1.models import ERDiagram, RelationalSchema


class ERToRelationalConverter:
    def __init__(self, er_diagram: ERDiagram):
        self.er_diagram = er_diagram
        self.schema = RelationalSchema()

    def convert(self) -> RelationalSchema:
        self._map_strong_entities()
        self._map_weak_entities()
        self._map_binary_1_to_1()
        self._map_binary_1_to_n()
        self._map_binary_m_to_n()
        self._map_multivalued_attributes()
        self._map_nary_relationships()
        return self.schema

    def _map_strong_entities(self) -> None:
        pass

    def _map_weak_entities(self) -> None:
        pass

    def _map_binary_1_to_1(self) -> None:
        pass

    def _map_binary_1_to_n(self) -> None:
        pass

    def _map_binary_m_to_n(self) -> None:
        pass

    def _map_multivalued_attributes(self) -> None:
        pass

    def _map_nary_relationships(self) -> None:
        pass