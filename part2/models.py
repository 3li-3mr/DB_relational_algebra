from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class Relation(BaseModel):
    name: str = ""
    columns: List[str] = Field(default_factory=list)
    rows: List[Dict[str, Any]] = Field(default_factory=list)


class Database(BaseModel):
    tables: Dict[str, Relation] = Field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Dict[str, List[Dict[str, Any]]]) -> "Database":
        pass


class QueryNode(BaseModel):
    operation: str
    arguments: Optional[str] = None
    children: List["QueryNode"] = Field(default_factory=list)