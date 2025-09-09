"""
GEDCOM Parser Service - Import and Process GEDCOM Files

This service handles parsing GEDCOM files and importing the genealogical data
into the TreeTalk PostgreSQL database. It processes individuals, families,
relationships, events, and places from GEDCOM format.

Key Features:
- GEDCOM file validation and parsing
- Data normalization and cleaning
- Duplicate detection and prevention
- Relationship mapping and validation
- Import progress tracking and error handling
"""

from gedcom.parser import Parser
from gedcom.element.individual import IndividualElement
from gedcom.element.family import FamilyElement
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import hashlib
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import uuid
import tempfile
import os

from models.source import Source
from models.person import Person
from models.relationship import Relationship
from models.event import Event
from models.place import Place

logger = logging.getLogger(__name__)


class GedcomParserService:
    """
    Service class for parsing GEDCOM files and importing data into database.
    
    This service handles the complete import workflow:
    1. File validation and hash checking
    2. GEDCOM parsing and data extraction
    3. Data normalization and cleaning
    4. Database import with relationship mapping
    5. Statistics calculation and error reporting
    """
    
    def __init__(self, db_session: AsyncSession):
        """
        Initialize the GEDCOM parser service.
        
        Args:
            db_session (AsyncSession): Database session for import operations
        """
        self.db = db_session
        self.gedcom_parser = None
        self.source_record = None
        self.person_map = {}  # Maps GEDCOM IDs to Person objects
        self.place_cache = {}  # Cache for place lookups
        
    async def parse_and_import_file(self, file_content: bytes, filename: str, 
                                  source_name: str = None) -> Tuple[Source, Dict]:
        """
        Parse GEDCOM file content and import into database.
        
        Args:
            file_content (bytes): Raw GEDCOM file content
            filename (str): Original filename
            source_name (str, optional): Human-readable source name
            
        Returns:
            Tuple[Source, Dict]: Created source record and import statistics
            
        Raises:
            ValueError: If file is invalid or already imported
            Exception: For parsing or database errors
        """
        try:
            # Step 1: Validate file and check for duplicates
            file_hash = self._calculate_file_hash(file_content)
            await self._check_duplicate_import(file_hash)
            
            # Step 2: Create source record
            self.source_record = await self._create_source_record(
                filename, source_name or filename, file_hash, len(file_content)
            )
            
            # Step 3: Parse GEDCOM file
            logger.info(f"Starting GEDCOM parse for {filename}")
            
            # Save content to temporary file for parsing
            with tempfile.NamedTemporaryFile(mode='wb', suffix='.ged', delete=False) as temp_file:
                temp_file.write(file_content)
                temp_file_path = temp_file.name
            
            try:
                self.gedcom_parser = Parser()
                self.gedcom_parser.parse_file(temp_file_path)
            finally:
                # Clean up temporary file
                os.unlink(temp_file_path)
            
            # Step 4: Extract and import data
            stats = await self._import_gedcom_data()
            
            # Step 5: Finalize import
            await self._finalize_import(stats)
            
            logger.info(f"✅ GEDCOM import completed: {stats}")
            return self.source_record, stats
            
        except Exception as e:
            if self.source_record:
                self.source_record.mark_error(str(e))
                await self.db.commit()
            logger.error(f"❌ GEDCOM import failed: {e}")
            raise
    
    def _calculate_file_hash(self, content: bytes) -> str:
        """Calculate SHA-256 hash of file content."""
        return hashlib.sha256(content).hexdigest()
    
    async def _check_duplicate_import(self, file_hash: str):
        """Check if file has already been imported."""
        result = await self.db.execute(
            select(Source).where(Source.file_hash == file_hash)
        )
        existing_source = result.scalar_one_or_none()
        
        if existing_source:
            raise ValueError(f"File already imported: {existing_source.name}")
    
    async def _create_source_record(self, filename: str, name: str, 
                                  file_hash: str, file_size: int) -> Source:
        """Create initial source record in database."""
        source = Source(
            name=name,
            filename=filename,
            source_type="gedcom",
            file_size=file_size,
            file_hash=file_hash,
            status="processing"
        )
        
        self.db.add(source)
        await self.db.commit()
        await self.db.refresh(source)
        
        logger.info(f"Created source record: {source.id}")
        return source
    
    async def _import_gedcom_data(self) -> Dict:
        """Import all GEDCOM data into database."""
        stats = {
            "persons_imported": 0,
            "relationships_imported": 0,
            "events_imported": 0,
            "places_imported": 0,
            "errors": []
        }
        
        try:
            # Import individuals (persons)
            individuals = self.gedcom_parser.get_element_list()
            individual_elements = [elem for elem in individuals if isinstance(elem, IndividualElement)]
            
            logger.info(f"Importing {len(individual_elements)} persons...")
            for individual in individual_elements:
                try:
                    person = await self._import_individual(individual)
                    if person:
                        stats["persons_imported"] += 1
                except Exception as e:
                    stats["errors"].append(f"Person import error: {e}")
                    logger.error(f"Failed to import individual {individual.get_pointer()}: {e}")
            
            # Import families (relationships)  
            all_elements = self.gedcom_parser.get_element_list()
            family_elements = [elem for elem in all_elements if isinstance(elem, FamilyElement)]
            
            logger.info(f"Importing {len(family_elements)} families...")
            for family in family_elements:
                try:
                    relationships = await self._import_family(family)
                    stats["relationships_imported"] += len(relationships)
                except Exception as e:
                    stats["errors"].append(f"Family import error: {e}")
                    logger.error(f"Failed to import family {family.get_pointer()}: {e}")
            
            # Count created places
            stats["places_imported"] = len(self.place_cache)
            
            # Commit all changes
            await self.db.commit()
            
        except Exception as e:
            await self.db.rollback()
            raise
        
        return stats
    
    async def _import_individual(self, individual: IndividualElement) -> Optional[Person]:
        """
        Import individual person from GEDCOM element.
        
        Args:
            individual (IndividualElement): GEDCOM individual element
            
        Returns:
            Optional[Person]: Created person record or None if failed
        """
        try:
            # Extract information from child elements
            given_names = None
            surname = None
            gender = None
            birth_date = None
            death_date = None
            birth_place = None
            death_place = None
            
            for child_elem in individual.get_child_elements():
                tag = child_elem.get_tag()
                value = child_elem.get_value()
                
                if tag == "NAME":
                    if value:
                        name_parts = value.split('/')
                        given_names = name_parts[0].strip() if name_parts else None
                        surname = name_parts[1].strip() if len(name_parts) > 1 else None
                elif tag == "SEX":
                    gender = value.upper()[:1] if value else None  # M, F, or first letter
                elif tag == "BIRT":
                    # Parse birth event
                    for birth_child in child_elem.get_child_elements():
                        if birth_child.get_tag() == "DATE":
                            birth_date = self._parse_date([birth_child])
                        elif birth_child.get_tag() == "PLAC":
                            birth_place = birth_child.get_value()
                elif tag == "DEAT":
                    # Parse death event
                    for death_child in child_elem.get_child_elements():
                        if death_child.get_tag() == "DATE":
                            death_date = self._parse_date([death_child])
                        elif death_child.get_tag() == "PLAC":
                            death_place = death_child.get_value()
            
            is_living = death_date is None
            
            # Create person record
            person = Person(
                source_id=self.source_record.id,
                gedcom_id=individual.get_pointer(),
                given_names=given_names,
                surname=surname,
                gender=gender,
                birth_date=birth_date,
                death_date=death_date,
                is_living=is_living
            )
            
            self.db.add(person)
            await self.db.flush()  # Get ID without committing
            
            # Cache for relationship mapping
            self.person_map[individual.get_pointer()] = person
            
            # Import events for this person (including places)
            await self._import_person_events(individual, person, birth_place, death_place)
            
            return person
            
        except Exception as e:
            logger.error(f"Failed to import individual {individual.get_pointer()}: {e}")
            return None
    
    async def _import_family(self, family: FamilyElement) -> List[Relationship]:
        """
        Import family relationships from GEDCOM family element.
        
        Args:
            family (FamilyElement): GEDCOM family element
            
        Returns:
            List[Relationship]: Created relationship records
        """
        relationships = []
        
        try:
            # Parse family child elements to find HUSB, WIFE, CHIL
            husband_id = None
            wife_id = None
            children_ids = []
            marriage_date = None
            
            for child_elem in family.get_child_elements():
                tag = child_elem.get_tag()
                value = child_elem.get_value()
                
                if tag == "HUSB":
                    husband_id = value
                elif tag == "WIFE":
                    wife_id = value
                elif tag == "CHIL":
                    children_ids.append(value)
                elif tag == "MARR":
                    # Look for marriage date in MARR child elements
                    for marr_child in child_elem.get_child_elements():
                        if marr_child.get_tag() == "DATE":
                            marriage_date = self._parse_date([marr_child])
            
            # Create spouse relationship if both husband and wife exist
            if husband_id and wife_id:
                husband_person = self.person_map.get(husband_id)
                wife_person = self.person_map.get(wife_id)
                
                if husband_person and wife_person:
                    spouse_rel = Relationship(
                        source_id=self.source_record.id,
                        person1_id=husband_person.id,
                        person2_id=wife_person.id,
                        relationship_type="spouse",
                        is_primary=True,
                        is_current=True
                    )
                    
                    if marriage_date:
                        spouse_rel.marriage_date = marriage_date
                    
                    self.db.add(spouse_rel)
                    relationships.append(spouse_rel)
            
            # Create parent-child relationships
            parents = []
            if husband_id and husband_id in self.person_map:
                parents.append(self.person_map[husband_id])
            if wife_id and wife_id in self.person_map:
                parents.append(self.person_map[wife_id])
            
            for child_id in children_ids:
                child_person = self.person_map.get(child_id)
                if child_person:
                    for parent in parents:
                        parent_child_rel = Relationship(
                            source_id=self.source_record.id,
                            person1_id=parent.id,
                            person2_id=child_person.id,
                            relationship_type="parent-child",
                            relationship_subtype="biological",
                            is_primary=True
                        )
                        
                        self.db.add(parent_child_rel)
                        relationships.append(parent_child_rel)
            
            return relationships
            
        except Exception as e:
            logger.error(f"Failed to import family {family.get_pointer()}: {e}")
            return []
    
    async def _get_or_create_place(self, place_name: str) -> Optional[Place]:
        """Get or create a place record."""
        if not place_name:
            return None
            
        # Check cache first
        if place_name in self.place_cache:
            return self.place_cache[place_name]
        
        # Check if place already exists in database
        result = await self.db.execute(
            select(Place).where(Place.name == place_name)
        )
        place = result.scalar_one_or_none()
        
        if not place:
            # Create new place
            place = Place(
                source_id=self.source_record.id,
                name=place_name,
                place_type="unknown"
            )
            self.db.add(place)
            await self.db.flush()  # Get ID without committing
        
        # Cache the place
        self.place_cache[place_name] = place
        return place

    async def _import_person_events(self, individual: IndividualElement, person: Person, birth_place: str = None, death_place: str = None):
        """Import events for a person from GEDCOM individual element."""
        try:
            # Birth event
            if person.birth_date or birth_place:
                birth_place_obj = await self._get_or_create_place(birth_place) if birth_place else None
                birth_event = Event(
                    source_id=self.source_record.id,
                    person_id=person.id,
                    event_type="birth",
                    event_date=person.birth_date,
                    place_id=birth_place_obj.id if birth_place_obj else None,
                    is_primary=True
                )
                self.db.add(birth_event)
            
            # Death event
            if person.death_date or death_place:
                death_place_obj = await self._get_or_create_place(death_place) if death_place else None
                death_event = Event(
                    source_id=self.source_record.id,
                    person_id=person.id,
                    event_type="death",
                    event_date=person.death_date,
                    place_id=death_place_obj.id if death_place_obj else None,
                    is_primary=True
                )
                self.db.add(death_event)
            
            # Parse additional events from individual child elements
            await self._import_additional_events(individual, person)
                
        except Exception as e:
            logger.error(f"Failed to import events for person {person.id}: {e}")
    
    async def _import_additional_events(self, individual: IndividualElement, person: Person):
        """Import additional events like residence, occupation, marriage, etc."""
        try:
            for child_elem in individual.get_child_elements():
                tag = child_elem.get_tag()
                
                # Skip already handled events
                if tag in ["NAME", "SEX", "BIRT", "DEAT"]:
                    continue
                
                event_type = None
                event_date = None
                event_place = None
                event_description = None
                
                # Map GEDCOM tags to event types
                if tag == "RESI":
                    event_type = "residence"
                elif tag == "OCCU":
                    event_type = "occupation"
                    event_description = child_elem.get_value()
                elif tag == "MARR":
                    event_type = "marriage"
                elif tag == "BAPM" or tag == "CHR":
                    event_type = "baptism"
                elif tag == "BURI":
                    event_type = "burial"
                elif tag == "EDUC":
                    event_type = "education"
                    event_description = child_elem.get_value()
                elif tag == "EMIG":
                    event_type = "emigration"
                elif tag == "IMMI":
                    event_type = "immigration"
                elif tag == "NATU":
                    event_type = "naturalization"
                else:
                    continue  # Skip unknown event types
                
                # Parse event details from child elements
                for event_child in child_elem.get_child_elements():
                    if event_child.get_tag() == "DATE":
                        event_date = self._parse_date([event_child])
                    elif event_child.get_tag() == "PLAC":
                        event_place = event_child.get_value()
                    elif event_child.get_tag() == "NOTE":
                        if not event_description:
                            event_description = event_child.get_value()
                
                # Create event record
                if event_type:
                    place_obj = await self._get_or_create_place(event_place) if event_place else None
                    event = Event(
                        source_id=self.source_record.id,
                        person_id=person.id,
                        event_type=event_type,
                        event_date=event_date,
                        place_id=place_obj.id if place_obj else None,
                        description=event_description,
                        is_primary=False
                    )
                    self.db.add(event)
                    
        except Exception as e:
            logger.error(f"Failed to import additional events for person {person.id}: {e}")
    
    def _parse_date(self, date_data) -> Optional[datetime.date]:
        """Parse GEDCOM date data to Python date object."""
        if not date_data:
            return None
        
        try:
            # Extract the date string from the GEDCOM data
            date_str = self._extract_date_string(date_data)
            if not date_str:
                return None
            
            # Clean and normalize the date string
            date_str = self._normalize_date_string(date_str)
            
            # Try to parse with various date formats
            return self._parse_date_formats(date_str)
            
        except Exception as e:
            logger.debug(f"Failed to parse date: {date_data} - {e}")
            return None
    
    def _extract_date_string(self, date_data) -> Optional[str]:
        """Extract date string from GEDCOM date data structure."""
        if not date_data:
            return None
        
        try:
            # Handle different date_data structures
            if isinstance(date_data, list):
                if len(date_data) > 0:
                    # Get the first element which should contain the date
                    first_element = date_data[0]
                    
                    # If it's a GEDCOM element, try to get its value
                    if hasattr(first_element, 'get_value'):
                        return first_element.get_value()
                    elif hasattr(first_element, 'value'):
                        return first_element.value
                    else:
                        return str(first_element)
            elif hasattr(date_data, 'get_value'):
                return date_data.get_value()
            elif hasattr(date_data, 'value'):
                return date_data.value
            else:
                return str(date_data)
                
        except Exception:
            return None
    
    def _normalize_date_string(self, date_str: str) -> str:
        """Clean and normalize GEDCOM date string."""
        if not date_str:
            return ""
        
        # Convert to uppercase for consistent handling
        date_str = date_str.upper().strip()
        
        # Remove GEDCOM date modifiers/qualifiers
        qualifiers = ['ABT', 'ABOUT', 'EST', 'CAL', 'CALCULATED', 'BEF', 'BEFORE', 'AFT', 'AFTER']
        for qualifier in qualifiers:
            if date_str.startswith(qualifier + ' '):
                date_str = date_str[len(qualifier):].strip()
                break
        
        # Handle date ranges (take the first date)
        if ' TO ' in date_str:
            date_str = date_str.split(' TO ')[0].strip()
        elif ' - ' in date_str:
            date_str = date_str.split(' - ')[0].strip()
        elif 'BET ' in date_str and ' AND ' in date_str:
            # Handle "BET date AND date" format
            date_str = date_str.replace('BET ', '').split(' AND ')[0].strip()
        
        return date_str
    
    def _parse_date_formats(self, date_str: str) -> Optional[datetime.date]:
        """Try to parse date string with various formats."""
        if not date_str:
            return None
        
        # Log the raw date string for debugging
        logger.info(f"Attempting to parse date string: '{date_str}'")
        
        # Common date formats used in GEDCOM files
        date_formats = [
            # Full dates with day/month/year
            '%d %b %Y',     # 13 FEB 2013
            '%d %B %Y',     # 13 FEBRUARY 2013
            '%b %d %Y',     # FEB 13 2013
            '%B %d %Y',     # FEBRUARY 13 2013
            '%d/%m/%Y',     # 13/02/2013
            '%m/%d/%Y',     # 02/13/2013
            '%Y-%m-%d',     # 2013-02-13
            '%d-%m-%Y',     # 13-02-2013
            '%m-%d-%Y',     # 02-13-2013
            '%d.%m.%Y',     # 13.02.2013 (European format)
            '%d %m %Y',     # 13 02 2013
            
            # Additional common GEDCOM formats
            '%d %b, %Y',    # 13 FEB, 2013
            '%b %d, %Y',    # FEB 13, 2013
            '%d-%b-%Y',     # 13-FEB-2013
            '%b-%d-%Y',     # FEB-13-2013
            '%d %b %y',     # 13 FEB 13 (2-digit year)
            '%m/%d/%y',     # 02/13/13 (2-digit year)
            '%d/%m/%y',     # 13/02/13 (2-digit year)
            '%Y.%m.%d',     # 2013.02.13 (ISO-like with dots)
            '%d.%m.%y',     # 13.02.13 (2-digit year with dots)
            
            # Year and month only
            '%b %Y',        # FEB 2013
            '%B %Y',        # FEBRUARY 2013
            '%m/%Y',        # 02/2013
            '%Y-%m',        # 2013-02
            '%m %Y',        # 02 2013
            '%b %y',        # FEB 13 (2-digit year)
            '%m/%y',        # 02/13 (2-digit year)
            
            # Year only (should only be used as last resort)
            '%Y',           # 2013
            '%y',           # 13 (2-digit year)
        ]
        
        for fmt in date_formats:
            try:
                parsed_date = datetime.strptime(date_str, fmt).date()
                logger.info(f"Successfully parsed date '{date_str}' using format '{fmt}' -> {parsed_date}")
                return parsed_date
            except ValueError:
                continue
        
        # Try more complex parsing for partial dates with regex
        import re
        
        # Try to extract day, month name, and year
        day_month_year_pattern = r'(\d{1,2})\s+(JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC|JANUARY|FEBRUARY|MARCH|APRIL|MAY|JUNE|JULY|AUGUST|SEPTEMBER|OCTOBER|NOVEMBER|DECEMBER)\s+(\d{4})'
        match = re.search(day_month_year_pattern, date_str, re.IGNORECASE)
        if match:
            day, month_name, year = match.groups()
            try:
                # Convert month name to number
                month_names = {
                    'JAN': 1, 'JANUARY': 1,
                    'FEB': 2, 'FEBRUARY': 2,
                    'MAR': 3, 'MARCH': 3,
                    'APR': 4, 'APRIL': 4,
                    'MAY': 5,
                    'JUN': 6, 'JUNE': 6,
                    'JUL': 7, 'JULY': 7,
                    'AUG': 8, 'AUGUST': 8,
                    'SEP': 9, 'SEPTEMBER': 9,
                    'OCT': 10, 'OCTOBER': 10,
                    'NOV': 11, 'NOVEMBER': 11,
                    'DEC': 12, 'DECEMBER': 12
                }
                month_num = month_names.get(month_name.upper())
                if month_num:
                    parsed_date = datetime(int(year), month_num, int(day)).date()
                    logger.info(f"Parsed date using regex: '{date_str}' -> {parsed_date}")
                    return parsed_date
            except (ValueError, KeyError):
                pass
        
        # Try to extract month name and year only
        month_year_pattern = r'(JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC|JANUARY|FEBRUARY|MARCH|APRIL|MAY|JUNE|JULY|AUGUST|SEPTEMBER|OCTOBER|NOVEMBER|DECEMBER)\s+(\d{4})'
        match = re.search(month_year_pattern, date_str, re.IGNORECASE)
        if match:
            month_name, year = match.groups()
            try:
                month_names = {
                    'JAN': 1, 'JANUARY': 1, 'FEB': 2, 'FEBRUARY': 2, 'MAR': 3, 'MARCH': 3,
                    'APR': 4, 'APRIL': 4, 'MAY': 5, 'JUN': 6, 'JUNE': 6, 'JUL': 7, 'JULY': 7,
                    'AUG': 8, 'AUGUST': 8, 'SEP': 9, 'SEPTEMBER': 9, 'OCT': 10, 'OCTOBER': 10,
                    'NOV': 11, 'NOVEMBER': 11, 'DEC': 12, 'DECEMBER': 12
                }
                month_num = month_names.get(month_name.upper())
                if month_num:
                    parsed_date = datetime(int(year), month_num, 1).date()
                    logger.info(f"Parsed month/year using regex: '{date_str}' -> {parsed_date}")
                    return parsed_date
            except (ValueError, KeyError):
                pass
        
        # Try to extract just the year as last resort
        year_match = re.search(r'\b(1[5-9]\d{2}|20\d{2})\b', date_str)
        if year_match:
            year = int(year_match.group(1))
            parsed_date = datetime(year, 1, 1).date()
            logger.warning(f"Only extracted year {year} from '{date_str}' - defaulting to January 1st: {parsed_date}")
            return parsed_date
        
        logger.warning(f"Could not parse date: '{date_str}'")
        return None
    
    async def _finalize_import(self, stats: Dict):
        """Finalize import by updating source record with statistics."""
        try:
            self.source_record.mark_completed(
                persons_count=stats["persons_imported"],
                families_count=stats["relationships_imported"]
            )
            
            if stats["errors"]:
                error_summary = f"{len(stats['errors'])} errors occurred during import"
                self.source_record.notes = error_summary
            
            await self.db.commit()
            
        except Exception as e:
            logger.error(f"Failed to finalize import: {e}")
            raise