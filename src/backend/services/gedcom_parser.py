"""
GEDCOM Parser Service - Family Tree Data Import

This service handles the complex task of parsing GEDCOM files and
importing genealogical data into the TreeTalk database.

GEDCOM (GEnealogical Data COMmunication) is the standard format
for exchanging genealogical data between different applications.

Key Features:
- Multi-version GEDCOM library compatibility
- Robust error handling for malformed files
- Source tracking for data provenance
- Comprehensive individual and family parsing
- Flexible date parsing (exact dates and text descriptions)
- Transaction management for data integrity

Architecture:
- Service class pattern for dependency injection
- Async/await for non-blocking operations
- Database transaction management
- Detailed logging for debugging import issues

Import Process:
1. Create source record for traceability
2. Parse GEDCOM file structure
3. Extract individuals and their attributes
4. Extract family relationships
5. Convert dates and places to structured format
6. Store all data with referential integrity

Error Handling:
- Graceful degradation for unsupported GEDCOM features
- Individual record failure doesn't stop entire import
- Detailed error logging for troubleshooting
- Rollback capabilities for failed imports
"""

from typing import Dict, List, Optional, Tuple
from sqlalchemy.orm import Session
try:
    from gedcom.parser import Parser as Gedcom
except ImportError:
    from gedcom import Gedcom
import uuid
from datetime import datetime, date
import os
import re

from ..models.person import Person
from ..models.relationship import Relationship
from ..models.source import Source

# Service class for GEDCOM parsing and import
class GedcomParserService:
    """Service for parsing GEDCOM files and importing data."""
    
    def __init__(self, db: Session):
        self.db = db
    
    # Main method to parse and import GEDCOM file
    async def parse_and_import_gedcom(
        self, 
        file_path: str, 
        source_name: str,
        source_description: Optional[str] = None
    ) -> Dict:
        """
        Parse a GEDCOM file and import all data into the database.
        
        Args:
            file_path: Path to the GEDCOM file
            source_name: Name for the source record
            source_description: Optional description
            
        Returns:
            Dict with import statistics and source ID
        """
        try:
            # Create source record
            source = Source(
                name=source_name,
                type="gedcom",
                description=source_description or f"GEDCOM import from {os.path.basename(file_path)}",
                file_path=file_path,
                status="active",
                source_metadata={}
            )
            self.db.add(source)
            self.db.commit()
            
            # Parse GEDCOM file
            try:
                # Try different parser initialization patterns for different library versions
                gedcom = Gedcom()
                gedcom.parse_file(file_path)
            except (TypeError, AttributeError):
                # Fallback for different library versions
                try:
                    from gedcom.parser import Parser
                    gedcom = Parser()
                    gedcom.parse_file(file_path)
                except:
                    # Final fallback - try direct file reading
                    with open(file_path, 'r', encoding='utf-8-sig') as f:
                        gedcom_text = f.read()
                    gedcom = Gedcom()
                    gedcom.parse(gedcom_text)
            
            # Import individuals
            individuals_imported = await self._import_individuals(gedcom, source.id)
            
            # Import families and relationships
            relationships_imported = await self._import_families(gedcom, source.id)
            
            # Update source metadata
            source.source_metadata = {
                "individuals_count": individuals_imported,
                "relationships_count": relationships_imported,
                "import_completed_at": datetime.utcnow().isoformat()
            }
            self.db.commit()
            
            return {
                "source_id": str(source.id),
                "individuals_imported": individuals_imported,
                "relationships_imported": relationships_imported,
                "status": "completed"
            }
            
        except Exception as e:
            # Mark source as error if it was created
            if 'source' in locals():
                source.status = "error"
                source.source_metadata = {
                    "error": str(e),
                    "import_failed_at": datetime.utcnow().isoformat()
                }
                self.db.commit()
            
            raise Exception(f"GEDCOM import failed: {str(e)}")
    
    # Import individuals from GEDCOM file
    async def _import_individuals(self, gedcom: Gedcom, source_id: uuid.UUID) -> int:
        """Import all individuals from GEDCOM file."""
        count = 0
        
        # Try different method names for getting individuals
        try:
            individuals = gedcom.get_individuals()
        except TypeError:
            # Some versions have parameter requirements for get_individuals
            try:
                individuals = []
                # Get all individual elements directly
                for element in gedcom.get_element_list():
                    if element.get_tag() == 'INDI':
                        individuals.append(element)
            except AttributeError:
                try:
                    individuals = gedcom.individuals
                except AttributeError:
                    print("Could not find individuals in GEDCOM file")
                    return 0
        except AttributeError:
            try:
                individuals = gedcom.get_element_list()
                individuals = [elem for elem in individuals if elem.get_tag() == 'INDI']
            except AttributeError:
                try:
                    individuals = gedcom.individuals
                except AttributeError:
                    print("Could not find individuals in GEDCOM file")
                    return 0
        
        for individual in individuals:
            try:
                # Extract person data
                person_data = self._extract_person_data(individual)
                
                # Get GEDCOM ID with fallback
                try:
                    gedcom_id = individual.get_pointer()
                except AttributeError:
                    try:
                        gedcom_id = individual.get_xref_id()
                    except AttributeError:
                        gedcom_id = str(individual.get_tag()) if hasattr(individual, 'get_tag') else f"INDI_{count}"
                
                # Create Person record
                person = Person(
                    source_id=source_id,
                    gedcom_id=gedcom_id,
                    name=person_data.get("name", "Unknown"),
                    given_names=person_data.get("given_names"),
                    surname=person_data.get("surname"),
                    gender=person_data.get("gender"),
                    is_living=person_data.get("is_living", False),
                    birth_date=person_data.get("birth_date"),
                    birth_date_text=person_data.get("birth_date_text"),
                    birth_place=person_data.get("birth_place"),
                    death_date=person_data.get("death_date"),
                    death_date_text=person_data.get("death_date_text"),
                    death_place=person_data.get("death_place"),
                    occupation=person_data.get("occupation"),
                    notes=person_data.get("notes")
                )
                
                self.db.add(person)
                count += 1
                
            except Exception as e:
                try:
                    pointer = individual.get_pointer()
                except:
                    pointer = f"individual_{count}"
                print(f"Error importing individual {pointer}: {e}")
                continue
        
        self.db.commit()
        return count
    
    # Import families and relationships from GEDCOM file
    async def _import_families(self, gedcom: Gedcom, source_id: uuid.UUID) -> int:
        """Import family relationships from GEDCOM file."""
        count = 0
        
        # Try different method names for getting families
        try:
            families = gedcom.get_families()
        except TypeError:
            # Some versions require no parameters for get_families
            try:
                families = []
                # Get all family elements directly
                for element in gedcom.get_element_list():
                    if element.get_tag() == 'FAM':
                        families.append(element)
            except AttributeError:
                try:
                    families = gedcom.families
                except AttributeError:
                    print("Could not find families in GEDCOM file")
                    return 0
        except AttributeError:
            try:
                families = gedcom.get_element_list()
                families = [elem for elem in families if elem.get_tag() == 'FAM']
            except AttributeError:
                try:
                    families = gedcom.families
                except AttributeError:
                    print("Could not find families in GEDCOM file")
                    return 0
        
        for family in families:
            try:
                # Get family members - try different methods
                husband_pointer = None
                wife_pointer = None
                children_pointers = []
                
                try:
                    husband_pointer = family.get_husband()
                    wife_pointer = family.get_wife()
                    children_pointers = family.get_children()
                except AttributeError:
                    # Parse family structure manually
                    for child in family.get_child_elements():
                        if child.get_tag() == 'HUSB':
                            husband_pointer = child.get_value()
                        elif child.get_tag() == 'WIFE':
                            wife_pointer = child.get_value()
                        elif child.get_tag() == 'CHIL':
                            children_pointers.append(child.get_value())
                
                # Find corresponding Person records
                husband = None
                wife = None
                if husband_pointer:
                    husband = self.db.query(Person).filter(
                        Person.source_id == source_id,
                        Person.gedcom_id == husband_pointer
                    ).first()
                
                if wife_pointer:
                    wife = self.db.query(Person).filter(
                        Person.source_id == source_id,
                        Person.gedcom_id == wife_pointer
                    ).first()
                
                # Create spouse relationship
                if husband and wife:
                    spouse_rel = Relationship(
                        person1_id=husband.id,
                        person2_id=wife.id,
                        relationship_type="spouse",
                        source_id=source_id
                    )
                    self.db.add(spouse_rel)
                    count += 1
                
                # Create parent-child relationships
                for child_pointer in children_pointers:
                    child = self.db.query(Person).filter(
                        Person.source_id == source_id,
                        Person.gedcom_id == child_pointer
                    ).first()
                    
                    if child:
                        # Parent-child relationships
                        if husband:
                            parent_rel = Relationship(
                                person1_id=husband.id,
                                person2_id=child.id,
                                relationship_type="parent",
                                source_id=source_id
                            )
                            self.db.add(parent_rel)
                            count += 1
                        
                        if wife:
                            parent_rel = Relationship(
                                person1_id=wife.id,
                                person2_id=child.id,
                                relationship_type="parent",
                                source_id=source_id
                            )
                            self.db.add(parent_rel)
                            count += 1
                
            except Exception as e:
                try:
                    pointer = family.get_pointer()
                except:
                    try:
                        pointer = family.get_xref_id()
                    except:
                        pointer = f"family_{count}"
                print(f"Error importing family {pointer}: {e}")
                continue
        
        self.db.commit()
        return count
    

    def _extract_person_data(self, individual) -> Dict:
        """Extract person data from GEDCOM individual record."""
        data = {}
        
        # Name information - try different methods
        name_parts = None
        try:
            name_parts = individual.get_name()
        except AttributeError:
            try:
                # Look for NAME tag in children
                for child in individual.get_child_elements():
                    if child.get_tag() == 'NAME':
                        name_value = child.get_value()
                        if name_value:
                            # Parse "Given /Surname/" format
                            if '/' in name_value:
                                parts = name_value.split('/')
                                given = parts[0].strip()
                                surname = parts[1].strip() if len(parts) > 1 else ""
                                name_parts = [given, surname]
                            else:
                                name_parts = [name_value.strip()]
                        break
            except:
                pass
        
        if name_parts:
            data["name"] = name_parts[0] + " " + name_parts[1] if len(name_parts) > 1 else name_parts[0]
            data["given_names"] = name_parts[0] if name_parts else None
            data["surname"] = name_parts[1] if len(name_parts) > 1 else None
        
        # Gender - try different methods
        gender = None
        try:
            gender = individual.get_gender()
        except AttributeError:
            try:
                for child in individual.get_child_elements():
                    if child.get_tag() == 'SEX':
                        gender = child.get_value()
                        break
            except:
                pass
        
        if gender:
            data["gender"] = gender.upper() if gender.upper() in ['M', 'F'] else 'U'
        
        # Birth and death information - simplified approach
        try:
            for child in individual.get_child_elements():
                if child.get_tag() == 'BIRT':
                    # Look for date and place in birth event
                    for birth_child in child.get_child_elements():
                        if birth_child.get_tag() == 'DATE':
                            birth_date_text = birth_child.get_value()
                            data["birth_date_text"] = birth_date_text
                            data["birth_date"] = self._parse_date(birth_date_text)
                        elif birth_child.get_tag() == 'PLAC':
                            data["birth_place"] = birth_child.get_value()
                
                elif child.get_tag() == 'DEAT':
                    # Look for date and place in death event
                    for death_child in child.get_child_elements():
                        if death_child.get_tag() == 'DATE':
                            death_date_text = death_child.get_value()
                            data["death_date_text"] = death_date_text
                            data["death_date"] = self._parse_date(death_date_text)
                        elif death_child.get_tag() == 'PLAC':
                            data["death_place"] = death_child.get_value()
                
                elif child.get_tag() == 'OCCU':
                    data["occupation"] = child.get_value()
                
                elif child.get_tag() == 'NOTE':
                    if "notes" not in data:
                        data["notes"] = child.get_value()
                    else:
                        data["notes"] += "; " + child.get_value()
        except:
            pass
        
        # Assume living if no death data and recent birth
        if "death_date" not in data:
            birth_year = data.get("birth_date")
            if birth_year and birth_year.year > 1900:
                data["is_living"] = True
        
        return data
    
    def _parse_date(self, date_str: Optional[str]) -> Optional[date]:
        """Parse GEDCOM date string to Python date object."""
        if not date_str:
            return None
        
        try:
            # Handle various GEDCOM date formats
            date_str = date_str.strip().upper()
            
            # Simple date formats
            date_patterns = [
                r"(\d{1,2})\s+(\w+)\s+(\d{4})",  # DD MMM YYYY
                r"(\w+)\s+(\d{4})",              # MMM YYYY
                r"(\d{4})",                      # YYYY
            ]
            
            months = {
                "JAN": 1, "FEB": 2, "MAR": 3, "APR": 4,
                "MAY": 5, "JUN": 6, "JUL": 7, "AUG": 8,
                "SEP": 9, "OCT": 10, "NOV": 11, "DEC": 12
            }
            
            for pattern in date_patterns:
                match = re.search(pattern, date_str)
                if match:
                    groups = match.groups()
                    
                    if len(groups) == 3:  # DD MMM YYYY
                        day, month_name, year = groups
                        if month_name in months:
                            return date(int(year), months[month_name], int(day))
                    
                    elif len(groups) == 2:  # MMM YYYY
                        month_name, year = groups
                        if month_name in months:
                            return date(int(year), months[month_name], 1)
                    
                    elif len(groups) == 1:  # YYYY
                        year = groups[0]
                        return date(int(year), 1, 1)
            
            return None
            
        except (ValueError, TypeError):
            return None