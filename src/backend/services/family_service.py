"""
Family Service - Family Tree Operations and Relationship Queries

This service provides family tree traversal, relationship analysis, and
genealogical query functionality for the TreeTalk application.

Key Features:
- Family tree data retrieval with configurable depth
- Relationship path finding and analysis
- Person search and filtering
- Family statistics and insights
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, and_, text, func
from sqlalchemy.orm import selectinload, joinedload
from typing import Dict, List, Optional, Set, Tuple, Any
import logging
from uuid import UUID

from models.person import Person
from models.relationship import Relationship
from models.source import Source
from models.event import Event

logger = logging.getLogger(__name__)


class FamilyService:
    """
    Service class for family tree operations and genealogical queries.
    
    This service handles:
    - Family tree data retrieval for visualization
    - Person search and filtering
    - Relationship analysis and path finding
    - Genealogical statistics and insights
    """
    
    def __init__(self, db_session: AsyncSession):
        """
        Initialize the family service.
        
        Args:
            db_session (AsyncSession): Database session for queries
        """
        self.db = db_session
    
    async def get_family_tree(self, focal_person_id: UUID, max_generations: int = 4, 
                            source_id: Optional[UUID] = None) -> Dict[str, Any]:
        """
        Get family tree data centered on a focal person.
        
        Args:
            focal_person_id (UUID): ID of the person to center the tree on
            max_generations (int): Maximum generations to include (default 4)
            source_id (UUID, optional): Limit to specific source
            
        Returns:
            Dict[str, Any]: Family tree data with persons and relationships
        """
        try:
            # Get focal person
            focal_person = await self._get_person_by_id(focal_person_id, source_id)
            if not focal_person:
                raise ValueError(f"Person not found: {focal_person_id}")
            
            # Collect all related persons within generation limit
            related_persons = await self._get_related_persons(
                focal_person_id, max_generations, source_id
            )
            
            # Get all relationships between these persons
            person_ids = {p.id for p in related_persons}
            relationships = await self._get_relationships_between_persons(
                person_ids, source_id
            )
            
            # Format data for visualization
            tree_data = {
                "focal_person": focal_person.to_dict(),
                "persons": [p.to_dict() for p in related_persons],
                "relationships": [r.to_dict() for r in relationships],
                "metadata": {
                    "total_persons": len(related_persons),
                    "total_relationships": len(relationships),
                    "max_generations": max_generations,
                    "source_id": str(source_id) if source_id else None
                }
            }
            
            logger.info(f"Retrieved family tree: {len(related_persons)} persons, "
                       f"{len(relationships)} relationships")
            
            return tree_data
            
        except Exception as e:
            logger.error(f"Failed to get family tree for {focal_person_id}: {e}")
            raise
    
    async def search_persons(self, query: str, source_id: Optional[UUID] = None, 
                           limit: int = 50) -> List[Dict[str, Any]]:
        """
        Search for persons by name or other criteria.
        
        Args:
            query (str): Search query (name, partial name, etc.)
            source_id (UUID, optional): Limit search to specific source
            limit (int): Maximum number of results to return
            
        Returns:
            List[Dict[str, Any]]: List of matching persons
        """
        try:
            # Build search query
            search_conditions = []
            
            if query.strip():
                # Full-text search on names
                search_term = f"%{query.strip()}%"
                search_conditions.append(
                    or_(
                        Person.given_names.ilike(search_term),
                        Person.surname.ilike(search_term),
                        Person.nickname.ilike(search_term),
                        func.concat(
                            func.coalesce(Person.given_names, ''), 
                            ' ', 
                            func.coalesce(Person.surname, '')
                        ).ilike(search_term)
                    )
                )
            
            if source_id:
                search_conditions.append(Person.source_id == source_id)
            
            # Execute search
            query_obj = select(Person).where(and_(*search_conditions)).limit(limit)
            
            result = await self.db.execute(query_obj)
            persons = result.scalars().all()
            
            # Convert to dict format with additional search metadata
            person_data = []
            for person in persons:
                person_dict = person.to_dict()
                person_dict["search_relevance"] = self._calculate_search_relevance(person, query)
                person_data.append(person_dict)
            
            # Sort by relevance
            person_data.sort(key=lambda x: x["search_relevance"], reverse=True)
            
            logger.info(f"Person search '{query}' returned {len(person_data)} results")
            return person_data
            
        except Exception as e:
            logger.error(f"Person search failed for '{query}': {e}")
            raise
    
    async def get_person_details(self, person_id: UUID, include_events: bool = True, 
                               include_relationships: bool = True) -> Dict[str, Any]:
        """
        Get detailed information about a specific person.
        
        Args:
            person_id (UUID): ID of the person
            include_events (bool): Whether to include life events
            include_relationships (bool): Whether to include relationships
            
        Returns:
            Dict[str, Any]: Detailed person information
        """
        try:
            # Base query with person data
            query = select(Person).where(Person.id == person_id)
            
            if include_events:
                query = query.options(selectinload(Person.events))
            
            result = await self.db.execute(query)
            person = result.scalar_one_or_none()
            
            if not person:
                raise ValueError(f"Person not found: {person_id}")
            
            person_data = person.to_dict()
            
            # Add events if requested
            if include_events and person.events:
                person_data["events"] = [event.to_dict() for event in person.events]
            
            # Add relationships if requested
            if include_relationships:
                relationships = await self._get_person_relationships(person_id)
                person_data["relationships"] = relationships
            
            return person_data
            
        except Exception as e:
            logger.error(f"Failed to get person details for {person_id}: {e}")
            raise
    
    async def get_relationship_path(self, person1_id: UUID, person2_id: UUID, 
                                  max_depth: int = 6) -> Optional[List[Dict[str, Any]]]:
        """
        Find the relationship path between two persons.
        
        Args:
            person1_id (UUID): First person ID
            person2_id (UUID): Second person ID
            max_depth (int): Maximum path length to search
            
        Returns:
            Optional[List[Dict[str, Any]]]: Relationship path or None if no connection
        """
        try:
            # Use recursive CTE to find shortest path
            cte_query = text("""
                WITH RECURSIVE relationship_path AS (
                    -- Base case: direct relationships
                    SELECT 
                        person1_id,
                        person2_id,
                        relationship_type,
                        1 as depth,
                        ARRAY[person1_id, person2_id] as path,
                        ARRAY[relationship_type] as rel_types
                    FROM relationships 
                    WHERE person1_id = :start_person OR person2_id = :start_person
                    
                    UNION ALL
                    
                    -- Recursive case: extend path
                    SELECT 
                        rp.person1_id,
                        r.person2_id,
                        r.relationship_type,
                        rp.depth + 1,
                        rp.path || r.person2_id,
                        rp.rel_types || r.relationship_type
                    FROM relationship_path rp
                    JOIN relationships r ON (
                        (rp.person2_id = r.person1_id AND r.person2_id != ALL(rp.path)) OR
                        (rp.person2_id = r.person2_id AND r.person1_id != ALL(rp.path))
                    )
                    WHERE rp.depth < :max_depth
                      AND NOT (r.person2_id = ANY(rp.path) OR r.person1_id = ANY(rp.path))
                )
                SELECT * FROM relationship_path 
                WHERE person2_id = :end_person OR person1_id = :end_person
                ORDER BY depth
                LIMIT 1
            """)
            
            result = await self.db.execute(cte_query, {
                "start_person": person1_id,
                "end_person": person2_id,
                "max_depth": max_depth
            })
            
            path_row = result.fetchone()
            
            if path_row:
                # Convert path to detailed information
                path_details = await self._build_relationship_path_details(path_row)
                return path_details
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to find relationship path between {person1_id} and {person2_id}: {e}")
            return None
    
    async def _get_person_by_id(self, person_id: UUID, source_id: Optional[UUID] = None) -> Optional[Person]:
        """Get person by ID with optional source filtering."""
        conditions = [Person.id == person_id]
        if source_id:
            conditions.append(Person.source_id == source_id)
        
        result = await self.db.execute(
            select(Person).where(and_(*conditions))
        )
        return result.scalar_one_or_none()
    
    async def _get_related_persons(self, focal_person_id: UUID, max_generations: int, 
                                 source_id: Optional[UUID] = None) -> List[Person]:
        """Get all persons related to focal person within generation limit."""
        visited_persons = set()
        current_generation = {focal_person_id}
        all_persons = []
        
        for generation in range(max_generations):
            if not current_generation:
                break
                
            # Get persons for current generation
            conditions = [Person.id.in_(current_generation)]
            if source_id:
                conditions.append(Person.source_id == source_id)
            
            result = await self.db.execute(
                select(Person).where(and_(*conditions))
            )
            generation_persons = result.scalars().all()
            
            # Add to results
            all_persons.extend(generation_persons)
            visited_persons.update(current_generation)
            
            # Find next generation through relationships
            next_generation = set()
            
            # Get all relationships involving current generation persons
            relationships_result = await self.db.execute(
                select(Relationship).where(
                    or_(
                        Relationship.person1_id.in_(current_generation),
                        Relationship.person2_id.in_(current_generation)
                    )
                ).options(
                    joinedload(Relationship.person1),
                    joinedload(Relationship.person2)
                )
            )
            relationships = relationships_result.scalars().all()
            
            # Collect related person IDs
            for rel in relationships:
                for person_id in current_generation:
                    other_id = rel.get_other_person_id(person_id)
                    if other_id and other_id not in visited_persons:
                        # Apply source filter if specified
                        if source_id:
                            other_person_result = await self.db.execute(
                                select(Person).where(
                                    and_(
                                        Person.id == other_id,
                                        Person.source_id == source_id
                                    )
                                )
                            )
                            if other_person_result.scalar_one_or_none():
                                next_generation.add(other_id)
                        else:
                            next_generation.add(other_id)
            
            current_generation = next_generation
        
        return all_persons
    
    async def _get_relationships_between_persons(self, person_ids: Set[UUID], 
                                               source_id: Optional[UUID] = None) -> List[Relationship]:
        """Get all relationships between a set of persons."""
        conditions = [
            Relationship.person1_id.in_(person_ids),
            Relationship.person2_id.in_(person_ids)
        ]
        
        if source_id:
            conditions.append(Relationship.source_id == source_id)
        
        result = await self.db.execute(
            select(Relationship)
            .where(and_(*conditions))
            .options(
                joinedload(Relationship.person1),
                joinedload(Relationship.person2)
            )
        )
        
        return result.scalars().all()
    
    async def _get_person_relationships(self, person_id: UUID) -> List[Dict[str, Any]]:
        """Get all relationships for a specific person."""
        result = await self.db.execute(
            select(Relationship)
            .where(
                or_(
                    Relationship.person1_id == person_id,
                    Relationship.person2_id == person_id
                )
            )
            .options(
                joinedload(Relationship.person1),
                joinedload(Relationship.person2)
            )
        )
        
        relationships = result.scalars().all()
        
        relationship_data = []
        for rel in relationships:
            rel_dict = rel.to_dict()
            rel_dict["description"] = rel.get_relationship_description(person_id)
            rel_dict["other_person"] = (
                rel.person2.to_dict() if str(rel.person1_id) == str(person_id) 
                else rel.person1.to_dict()
            )
            relationship_data.append(rel_dict)
        
        return relationship_data
    
    def _calculate_search_relevance(self, person: Person, query: str) -> float:
        """Calculate search relevance score for ranking results."""
        if not query.strip():
            return 0.0
        
        score = 0.0
        query_lower = query.lower().strip()
        
        # Exact name matches get highest score
        full_name = person.get_full_name().lower()
        if query_lower == full_name:
            score += 10.0
        elif query_lower in full_name:
            score += 5.0
        
        # Given name matches
        if person.given_names and query_lower in person.given_names.lower():
            score += 3.0
        
        # Surname matches
        if person.surname and query_lower in person.surname.lower():
            score += 3.0
        
        # Nickname matches
        if person.nickname and query_lower in person.nickname.lower():
            score += 2.0
        
        # Boost for more complete records
        if person.birth_date:
            score += 0.5
        if person.death_date or person.is_living:
            score += 0.5
        
        return score
    
    async def _build_relationship_path_details(self, path_row) -> List[Dict[str, Any]]:
        """Build detailed relationship path information."""
        # This would be implemented to provide detailed path information
        # For now, return basic structure
        return [
            {
                "person_id": str(path_row[0]),
                "relationship_type": path_row[2],
                "depth": path_row[3]
            }
        ]