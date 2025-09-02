"""
Family Service - Handle family tree operations and relationship calculations
"""

from typing import Dict, List, Any, Set
from sqlalchemy.orm import Session
import uuid

from ..models.person import Person
from ..models.relationship import Relationship

# Service class for family tree operations
class FamilyService:
    """Service for family tree operations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    # Get family tree data for visualization
    async def get_family_tree(
        self, 
        person_id: uuid.UUID, 
        generations: int = 3
    ) -> Dict[str, Any]:
        """
        Get family tree data for visualization.
        
        Args:
            person_id: ID of the central person
            generations: Number of generations to include (up/down from center)
            
        Returns:
            Dict with persons and relationships for tree visualization
        """
        try:
            central_person = self.db.query(Person).filter(Person.id == person_id).first()
            if not central_person:
                return {"persons": [], "relationships": []}
            
            # Collect all persons in the tree
            persons_in_tree: Set[uuid.UUID] = set()
            persons_in_tree.add(person_id)
            
            # Get ancestors
            ancestors = await self._get_ancestors_recursive(person_id, generations, set())
            persons_in_tree.update(ancestors)
            
            # Get descendants
            descendants = await self._get_descendants_recursive(person_id, generations, set())
            persons_in_tree.update(descendants)
            
            # Get spouse relationships for all persons in tree
            for person_uuid in list(persons_in_tree):
                spouses = await self._get_spouses(person_uuid)
                persons_in_tree.update(spouses)
            
            # Fetch all person objects
            persons = self.db.query(Person).filter(Person.id.in_(persons_in_tree)).all()
            
            # Get all relationships between persons in tree
            relationships = self.db.query(Relationship).filter(
                Relationship.person1_id.in_(persons_in_tree),
                Relationship.person2_id.in_(persons_in_tree)
            ).all()
            
            # Format response
            person_data = []
            for person in persons:
                person_data.append({
                    "id": str(person.id),
                    "name": person.name,
                    "given_names": person.given_names,
                    "surname": person.surname,
                    "gender": person.gender,
                    "birth_date": person.birth_date.isoformat() if person.birth_date else None,
                    "death_date": person.death_date.isoformat() if person.death_date else None,
                    "birth_place": person.birth_place,
                    "death_place": person.death_place,
                    "is_living": person.is_living
                })
            
            relationship_data = []
            for rel in relationships:
                relationship_data.append({
                    "id": str(rel.id),
                    "person1_id": str(rel.person1_id),
                    "person2_id": str(rel.person2_id),
                    "type": rel.relationship_type,
                    "start_date": rel.start_date.isoformat() if rel.start_date else None,
                    "place": rel.place
                })
            
            return {
                "central_person_id": str(person_id),
                "persons": person_data,
                "relationships": relationship_data
            }
            
        except Exception as e:
            raise Exception(f"Error building family tree: {str(e)}")
    
    # Get ancestors of a person
    async def get_ancestors(
        self, 
        person_id: uuid.UUID, 
        generations: int = 5
    ) -> List[Dict[str, Any]]:
        """Get ancestors of a person."""
        try:
            ancestor_ids = await self._get_ancestors_recursive(person_id, generations, set())
            
            if not ancestor_ids:
                return []
            
            ancestors = self.db.query(Person).filter(Person.id.in_(ancestor_ids)).all()
            
            result = []
            for person in ancestors:
                # Calculate generation level (simple approximation)
                generation = await self._calculate_generation_level(person_id, person.id, "up")
                
                result.append({
                    "id": str(person.id),
                    "name": person.name,
                    "gender": person.gender,
                    "birth_date": person.birth_date.isoformat() if person.birth_date else None,
                    "death_date": person.death_date.isoformat() if person.death_date else None,
                    "generation_level": generation
                })
            
            return result
            
        except Exception as e:
            raise Exception(f"Error fetching ancestors: {str(e)}")
    
    # Get descendants of a person
    async def get_descendants(
        self, 
        person_id: uuid.UUID, 
        generations: int = 5
    ) -> List[Dict[str, Any]]:
        """Get descendants of a person."""
        try:
            descendant_ids = await self._get_descendants_recursive(person_id, generations, set())
            
            if not descendant_ids:
                return []
            
            descendants = self.db.query(Person).filter(Person.id.in_(descendant_ids)).all()
            
            result = []
            for person in descendants:
                # Calculate generation level
                generation = await self._calculate_generation_level(person_id, person.id, "down")
                
                result.append({
                    "id": str(person.id),
                    "name": person.name,
                    "gender": person.gender,
                    "birth_date": person.birth_date.isoformat() if person.birth_date else None,
                    "death_date": person.death_date.isoformat() if person.death_date else None,
                    "generation_level": generation
                })
            
            return result
            
        except Exception as e:
            raise Exception(f"Error fetching descendants: {str(e)}")
    
    # Helper recursive methods
    async def _get_ancestors_recursive(
        self, 
        person_id: uuid.UUID, 
        generations: int, 
        visited: Set[uuid.UUID]
    ) -> Set[uuid.UUID]:
        """Recursively get all ancestors up to specified generations."""
        if generations <= 0 or person_id in visited:
            return set()
        
        visited.add(person_id)
        ancestors = set()
        
        # Get parents
        parent_relationships = self.db.query(Relationship).filter(
            Relationship.person2_id == person_id,
            Relationship.relationship_type == "parent"
        ).all()
        
        for rel in parent_relationships:
            parent_id = rel.person1_id
            ancestors.add(parent_id)
            
            # Recursively get ancestors of parents
            parent_ancestors = await self._get_ancestors_recursive(
                parent_id, generations - 1, visited.copy()
            )
            ancestors.update(parent_ancestors)
        
        return ancestors
    
    # Get descendants recursively
    async def _get_descendants_recursive(
        self, 
        person_id: uuid.UUID, 
        generations: int, 
        visited: Set[uuid.UUID]
    ) -> Set[uuid.UUID]:
        """Recursively get all descendants down to specified generations."""
        if generations <= 0 or person_id in visited:
            return set()
        
        visited.add(person_id)
        descendants = set()
        
        # Get children
        child_relationships = self.db.query(Relationship).filter(
            Relationship.person1_id == person_id,
            Relationship.relationship_type == "parent"
        ).all()
        
        for rel in child_relationships:
            child_id = rel.person2_id
            descendants.add(child_id)
            
            # Recursively get descendants of children
            child_descendants = await self._get_descendants_recursive(
                child_id, generations - 1, visited.copy()
            )
            descendants.update(child_descendants)
        
        return descendants
    
    # Get spouses of a person
    async def _get_spouses(self, person_id: uuid.UUID) -> Set[uuid.UUID]:
        """Get all spouses of a person."""
        spouses = set()
        
        # Get spouse relationships in both directions
        spouse_rels = self.db.query(Relationship).filter(
            ((Relationship.person1_id == person_id) | (Relationship.person2_id == person_id)),
            Relationship.relationship_type.in_(["spouse", "partner"])
        ).all()
        
        for rel in spouse_rels:
            if rel.person1_id == person_id:
                spouses.add(rel.person2_id)
            else:
                spouses.add(rel.person1_id)
        
        return spouses
    
    # Calculate generation level relative to reference person
    async def _calculate_generation_level(
        self, 
        reference_person_id: uuid.UUID, 
        target_person_id: uuid.UUID, 
        direction: str
    ) -> int:
        """Calculate generation level relative to reference person."""
        # This is a simplified implementation
        # In a production system, you'd want a more sophisticated algorithm
        
        if reference_person_id == target_person_id:
            return 0
        
        # For now, return a placeholder generation level
        # This would need to be implemented with proper graph traversal
        return 1