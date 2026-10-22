from typing import Any, List, Optional
from pydantic import BaseModel, ConfigDict, Field, model_validator


class Attribute(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    name: str
    is_primary_key: bool = Field(default=False, alias="isPrimaryKey")
    is_partial_key: bool = Field(default=False, alias="isPartialKey")
    is_multivalued: bool = Field(default=False, alias="isMultiValued")
    is_derived: bool = Field(default=False, alias="isDerived")
    composite: Optional[List[str]] = None


class Entity(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    name: str
    is_weak: bool = Field(default=False, alias="isWeak")
    attributes: List[Attribute] = Field(default_factory=list)


class Participant(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    entity: str
    cardinality: str = "1"
    participation: str = "partial"


class Relationship(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    name: str
    is_identifying: bool = Field(default=False, alias="isIdentifying")
    participants: List[Participant] = Field(default_factory=list)
    attributes: List[Attribute] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def normalize_binary_and_nary(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if str(data.get("type", "")).lower() == "identifying":
                data["isIdentifying"] = True

            if "entity1" in data and "entity2" in data and not data.get("participants"):
                card = data.get("cardinality", "1:1")
                card_parts = [p.strip() for p in card.split(":")]
                c1 = card_parts[0] if len(card_parts) > 0 else "1"
                c2 = card_parts[1] if len(card_parts) > 1 else "1"

                p1 = data.get("entity1Participation", "partial")
                p2 = data.get("entity2Participation", "partial")

                data["participants"] = [
                    {"entity": data["entity1"], "cardinality": c1, "participation": p1},
                    {"entity": data["entity2"], "cardinality": c2, "participation": p2},
                ]
        return data


class ERDiagram(BaseModel):
    entities: List[Entity] = Field(default_factory=list)
    relationships: List[Relationship] = Field(default_factory=list)


class ForeignKey(BaseModel):
    column_name: str
    referenced_table: str
    referenced_column: str


class Column(BaseModel):
    name: str
    is_primary_key: bool = False
    is_foreign_key: bool = False


class Table(BaseModel):
    name: str
    columns: List[Column] = Field(default_factory=list)
    foreign_keys: List[ForeignKey] = Field(default_factory=list)


class RelationalSchema(BaseModel):
    tables: List[Table] = Field(default_factory=list)