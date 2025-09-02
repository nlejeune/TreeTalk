from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime

@dataclass
class Person:
    id: str
    first_name: str
    last_name: str
    birth_date: Optional[str] = None
    death_date: Optional[str] = None
    birth_place: Optional[str] = None
    death_place: Optional[str] = None
    gender: Optional[str] = None
    parents: List[str] = None
    spouse: Optional[str] = None
    children: List[str] = None
    source: str = "demo"
    
    def __post_init__(self):
        if self.parents is None:
            self.parents = []
        if self.children is None:
            self.children = []
    
    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"
    
    @property
    def is_alive(self) -> bool:
        return self.death_date is None
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "firstName": self.first_name,
            "lastName": self.last_name,
            "fullName": self.full_name,
            "birthDate": self.birth_date,
            "deathDate": self.death_date,
            "birthPlace": self.birth_place,
            "deathPlace": self.death_place,
            "gender": self.gender,
            "parents": self.parents,
            "spouse": self.spouse,
            "children": self.children,
            "source": self.source,
            "isAlive": self.is_alive
        }