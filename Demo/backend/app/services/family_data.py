from app.models.person import Person
from typing import List, Dict, Optional

class FamilyDataService:
    def __init__(self):
        self.persons = self._create_demo_family()
        self.persons_dict = {p.id: p for p in self.persons}
    
    def _create_demo_family(self) -> List[Person]:
        """Create the Dupont family demo data"""
        family = []
        
        # Grandparents (Generation 1)
        jean = Person(
            id="jean_dupont_1920",
            first_name="Jean",
            last_name="Dupont",
            birth_date="1920-03-15",
            death_date="1995-12-10",
            birth_place="Lyon, France",
            death_place="Lyon, France",
            gender="M",
            spouse="marie_durand_1925",
            children=["pierre_dupont_1950", "isabelle_dupont_1952"]
        )
        
        marie = Person(
            id="marie_durand_1925",
            first_name="Marie",
            last_name="Durand",
            birth_date="1925-07-22",
            death_date="2010-05-18",
            birth_place="Marseille, France",
            death_place="Lyon, France",
            gender="F",
            spouse="jean_dupont_1920",
            children=["pierre_dupont_1950", "isabelle_dupont_1952"]
        )
        
        # Parents (Generation 2)
        pierre = Person(
            id="pierre_dupont_1950",
            first_name="Pierre",
            last_name="Dupont",
            birth_date="1950-11-08",
            birth_place="Lyon, France",
            gender="M",
            parents=["jean_dupont_1920", "marie_durand_1925"],
            spouse="anne_martin_1952",
            children=["thomas_dupont_1975", "sophie_dupont_1978"]
        )
        
        anne = Person(
            id="anne_martin_1952",
            first_name="Anne",
            last_name="Martin",
            birth_date="1952-04-12",
            birth_place="Nice, France",
            gender="F",
            spouse="pierre_dupont_1950",
            children=["thomas_dupont_1975", "sophie_dupont_1978"]
        )
        
        isabelle = Person(
            id="isabelle_dupont_1952",
            first_name="Isabelle",
            last_name="Dupont",
            birth_date="1952-09-30",
            birth_place="Lyon, France",
            gender="F",
            parents=["jean_dupont_1920", "marie_durand_1925"],
            spouse="michel_bernard_1948",
            children=["lucas_bernard_1980", "emma_bernard_1985"]
        )
        
        michel = Person(
            id="michel_bernard_1948",
            first_name="Michel",
            last_name="Bernard",
            birth_date="1948-12-05",
            birth_place="Toulouse, France",
            gender="M",
            spouse="isabelle_dupont_1952",
            children=["lucas_bernard_1980", "emma_bernard_1985"]
        )
        
        # Children (Generation 3)
        thomas = Person(
            id="thomas_dupont_1975",
            first_name="Thomas",
            last_name="Dupont",
            birth_date="1975-06-20",
            birth_place="Lyon, France",
            gender="M",
            parents=["pierre_dupont_1950", "anne_martin_1952"]
        )
        
        sophie = Person(
            id="sophie_dupont_1978",
            first_name="Sophie",
            last_name="Dupont",
            birth_date="1978-02-14",
            birth_place="Lyon, France",
            gender="F",
            parents=["pierre_dupont_1950", "anne_martin_1952"]
        )
        
        lucas = Person(
            id="lucas_bernard_1980",
            first_name="Lucas",
            last_name="Bernard",
            birth_date="1980-10-03",
            birth_place="Toulouse, France",
            gender="M",
            parents=["michel_bernard_1948", "isabelle_dupont_1952"]
        )
        
        emma = Person(
            id="emma_bernard_1985",
            first_name="Emma",
            last_name="Bernard",
            birth_date="1985-01-28",
            birth_place="Toulouse, France",
            gender="F",
            parents=["michel_bernard_1948", "isabelle_dupont_1952"]
        )
        
        return [jean, marie, pierre, anne, isabelle, michel, thomas, sophie, lucas, emma]
    
    def get_all_persons(self) -> List[Person]:
        return self.persons
    
    def get_person_by_id(self, person_id: str) -> Optional[Person]:
        return self.persons_dict.get(person_id)
    
    def search_persons(self, query: str) -> List[Person]:
        query = query.lower()
        results = []
        for person in self.persons:
            if (query in person.first_name.lower() or 
                query in person.last_name.lower() or 
                query in person.full_name.lower()):
                results.append(person)
        return results
    
    def get_family_tree_data(self) -> Dict:
        """Return family tree data formatted for D3.js visualization"""
        nodes = []
        links = []
        
        for person in self.persons:
            nodes.append({
                "id": person.id,
                "name": person.full_name,
                "firstName": person.first_name,
                "lastName": person.last_name,
                "birthDate": person.birth_date,
                "deathDate": person.death_date,
                "gender": person.gender,
                "isAlive": person.is_alive
            })
            
            # Create parent-child relationships
            for child_id in person.children:
                links.append({
                    "source": person.id,
                    "target": child_id,
                    "type": "parent-child"
                })
            
            # Create spouse relationships
            if person.spouse and person.id < person.spouse:  # Avoid duplicates
                links.append({
                    "source": person.id,
                    "target": person.spouse,
                    "type": "spouse"
                })
        
        return {
            "nodes": nodes,
            "links": links
        }
    
    def get_ancestors(self, person_id: str) -> List[Person]:
        """Get all ancestors of a person"""
        ancestors = []
        person = self.get_person_by_id(person_id)
        if not person:
            return ancestors
        
        for parent_id in person.parents:
            parent = self.get_person_by_id(parent_id)
            if parent:
                ancestors.append(parent)
                ancestors.extend(self.get_ancestors(parent_id))
        
        return ancestors
    
    def get_descendants(self, person_id: str) -> List[Person]:
        """Get all descendants of a person"""
        descendants = []
        person = self.get_person_by_id(person_id)
        if not person:
            return descendants
        
        for child_id in person.children:
            child = self.get_person_by_id(child_id)
            if child:
                descendants.append(child)
                descendants.extend(self.get_descendants(child_id))
        
        return descendants