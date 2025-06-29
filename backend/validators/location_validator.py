import re
from typing import Dict, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

class LocationValidator:
    """Validates location data to ensure accuracy and prevent cross-state assignment errors."""
    
    # Colorado geographic bounds
    COLORADO_BOUNDS = {
        'min_lat': 36.0,
        'max_lat': 42.0,
        'min_lon': -109.5,
        'max_lon': -102.0
    }
    
    # State keywords and their common abbreviations
    STATE_KEYWORDS = {
        'alabama': ['alabama', 'ala'],
        'alaska': ['alaska'],
        'arizona': ['arizona', 'ariz'],
        'arkansas': ['arkansas', 'ark'],
        'california': ['california', 'calif', 'cal'],
        'colorado': ['colorado', 'colo'],
        'connecticut': ['connecticut', 'conn'],
        'delaware': ['delaware', 'del'],
        'florida': ['florida', 'fla'],
        'georgia': ['georgia'],
        'hawaii': ['hawaii'],
        'idaho': ['idaho', 'ida'],
        'illinois': ['illinois', 'ill'],
        'indiana': ['indiana', 'ind'],
        'iowa': ['iowa'],
        'kansas': ['kansas', 'kan'],
        'kentucky': ['kentucky'],
        'louisiana': ['louisiana'],
        'maine': ['maine'],
        'maryland': ['maryland'],
        'massachusetts': ['massachusetts', 'mass', 'mass.'],
        'michigan': ['michigan', 'mich'],
        'minnesota': ['minnesota', 'minn'],
        'mississippi': ['mississippi', 'miss'],
        'missouri': ['missouri'],
        'montana': ['montana', 'mont'],
        'nebraska': ['nebraska', 'neb', 'nebr'],
        'nevada': ['nevada', 'nev'],
        'new hampshire': ['new hampshire', 'n.h.'],
        'new jersey': ['new jersey', 'n.j.'],
        'new mexico': ['new mexico', 'n.m.', 'n. mex'],
        'new york': ['new york', 'n.y.'],
        'north carolina': ['north carolina', 'n.c.'],
        'north dakota': ['north dakota', 'n.d.', 'n. dak'],
        'ohio': ['ohio'],
        'oklahoma': ['oklahoma', 'okla'],
        'oregon': ['oregon', 'ore'],
        'pennsylvania': ['pennsylvania', 'penn'],
        'rhode island': ['rhode island', 'r.i.'],
        'south carolina': ['south carolina', 's.c.'],
        'south dakota': ['south dakota', 's.d.', 's. dak'],
        'tennessee': ['tennessee', 'tenn'],
        'texas': ['texas', 'tex'],
        'utah': ['utah'],
        'vermont': ['vermont'],
        'virginia': ['virginia'],
        'washington': ['washington', 'wash'],
        'west virginia': ['west virginia', 'w.v.', 'w. va'],
        'wisconsin': ['wisconsin', 'wis', 'wisc'],
        'wyoming': ['wyoming', 'wyo']
    }
    
    # Common two-letter state abbreviations that need special handling
    STATE_ABBREVIATIONS = {
        'al': 'alabama', 'ak': 'alaska', 'az': 'arizona', 'ar': 'arkansas',
        'ca': 'california', 'co': 'colorado', 'ct': 'connecticut', 'de': 'delaware',
        'fl': 'florida', 'ga': 'georgia', 'hi': 'hawaii', 'id': 'idaho',
        'il': 'illinois', 'in': 'indiana', 'ia': 'iowa', 'ks': 'kansas',
        'ky': 'kentucky', 'la': 'louisiana', 'me': 'maine', 'md': 'maryland',
        'ma': 'massachusetts', 'mi': 'michigan', 'mn': 'minnesota', 'ms': 'mississippi',
        'mo': 'missouri', 'mt': 'montana', 'ne': 'nebraska', 'nv': 'nevada',
        'nh': 'new hampshire', 'nj': 'new jersey', 'nm': 'new mexico', 'ny': 'new york',
        'nc': 'north carolina', 'nd': 'north dakota', 'oh': 'ohio', 'ok': 'oklahoma',
        'or': 'oregon', 'pa': 'pennsylvania', 'ri': 'rhode island', 'sc': 'south carolina',
        'sd': 'south dakota', 'tn': 'tennessee', 'tx': 'texas', 'ut': 'utah',
        'vt': 'vermont', 'va': 'virginia', 'wa': 'washington', 'wv': 'west virginia',
        'wi': 'wisconsin', 'wy': 'wyoming'
    }
    
    @classmethod
    def extract_mentioned_states(cls, text: str) -> List[str]:
        """Extract all states mentioned in the text."""
        if not text:
            return []
            
        text_lower = text.lower()
        mentioned_states = []
        
        # First check for two-letter abbreviations with proper boundaries
        # Pattern: whitespace or punctuation, then abbreviation, then whitespace/punctuation/comma/period
        abbrev_pattern = r'(?:^|[\s,\.\!:\-\(])([A-Z]{2})(?:[\s,\.\!:\-\)]|$)'
        for match in re.finditer(abbrev_pattern, text):  # Use original case for abbreviations
            abbr = match.group(1).lower()
            if abbr in cls.STATE_ABBREVIATIONS:
                mentioned_states.append(cls.STATE_ABBREVIATIONS[abbr])
        
        # Then check for full state names and longer abbreviations
        for state, keywords in cls.STATE_KEYWORDS.items():
            for keyword in keywords:
                # For abbreviations with periods, we need special handling
                if '.' in keyword:
                    # Just use the escaped pattern without word boundaries
                    pattern = re.escape(keyword)
                else:
                    # Normal word boundary pattern
                    pattern = r'\b' + re.escape(keyword) + r'\b'
                    
                if re.search(pattern, text_lower):
                    mentioned_states.append(state)
                    break
        
        return list(set(mentioned_states))  # Remove duplicates
    
    @classmethod
    def is_coordinate_in_colorado(cls, lat: float, lon: float) -> bool:
        """Check if coordinates fall within Colorado bounds."""
        return (cls.COLORADO_BOUNDS['min_lat'] <= lat <= cls.COLORADO_BOUNDS['max_lat'] and
                cls.COLORADO_BOUNDS['min_lon'] <= lon <= cls.COLORADO_BOUNDS['max_lon'])
    
    @classmethod
    def validate_location_assignment(cls, text: str, lat: Optional[float], lon: Optional[float], 
                                   gmu: Optional[str]) -> Dict[str, any]:
        """
        Validate that location assignment is accurate and consistent.
        
        Returns a dictionary with:
        - is_valid: bool - whether the assignment appears valid
        - confidence: float - confidence score (0-1)
        - issues: List[str] - list of identified issues
        - recommendation: str - what to do with this entry
        """
        issues = []
        confidence = 1.0
        
        # Extract mentioned states
        mentioned_states = cls.extract_mentioned_states(text)
        
        # Check if non-Colorado states are mentioned
        non_colorado_states = [s for s in mentioned_states if s != 'colorado']
        
        if non_colorado_states:
            # Strong indicator this is not a Colorado sighting
            issues.append(f"Text mentions non-Colorado state(s): {', '.join(non_colorado_states)}")
            confidence *= 0.1
            
            # If coordinates are provided and in Colorado, this is likely an error
            if lat and lon and cls.is_coordinate_in_colorado(lat, lon):
                issues.append("Coordinates are in Colorado but text mentions other state(s)")
                confidence *= 0.1
        
        # Check if coordinates are outside Colorado
        if lat and lon and not cls.is_coordinate_in_colorado(lat, lon):
            issues.append(f"Coordinates ({lat}, {lon}) are outside Colorado bounds")
            confidence *= 0.2
            
            # If GMU is assigned, this is definitely wrong
            if gmu:
                issues.append("GMU assigned to coordinates outside Colorado")
                confidence = 0.0
        
        # If GMU is assigned but no Colorado mention and other states mentioned
        if gmu and non_colorado_states and 'colorado' not in mentioned_states:
            issues.append("GMU assigned but only non-Colorado states mentioned")
            confidence = 0.0
        
        # Determine recommendation
        if confidence >= 0.8:
            recommendation = "keep"
        elif confidence >= 0.5:
            recommendation = "review"
        elif confidence >= 0.2:
            recommendation = "flag_suspicious"
        else:
            recommendation = "reject"
        
        return {
            'is_valid': confidence >= 0.5,
            'confidence': confidence,
            'issues': issues,
            'recommendation': recommendation,
            'mentioned_states': mentioned_states,
            'is_colorado_sighting': 'colorado' in mentioned_states or (not non_colorado_states and confidence >= 0.8)
        }
    
    @classmethod
    def get_validation_prompt_addition(cls) -> str:
        """Get additional prompt text for LLM to improve location accuracy."""
        return """
IMPORTANT LOCATION VALIDATION RULES:
1. ONLY assign coordinates for locations that are explicitly in Colorado
2. If the text mentions any other state (Virginia, Massachusetts, etc.), return None for coordinates
3. Look for state names or abbreviations in the text
4. Common out-of-state indicators: "I live in [state]", "camera is in [state]", state abbreviations
5. If location is ambiguous or could be in multiple states, return None for coordinates
6. Only assign GMU if you are certain the location is in Colorado

Examples of when to return None:
- "I live in Mass. and the camera is in Virginia" -> None (not in Colorado)
- "Bear Creek Trail" (without state context) -> None (ambiguous, exists in many states)
- "Saw elk in Wyoming" -> None (not in Colorado)
"""
    
    @classmethod
    def create_validation_report(cls, sightings: List[Dict]) -> Dict[str, any]:
        """Create a validation report for a batch of sightings."""
        report = {
            'total': len(sightings),
            'valid': 0,
            'suspicious': 0,
            'rejected': 0,
            'issues_found': [],
            'state_distribution': {}
        }
        
        for sighting in sightings:
            validation = cls.validate_location_assignment(
                sighting.get('description', ''),
                sighting.get('latitude'),
                sighting.get('longitude'),
                sighting.get('gmu_unit')
            )
            
            if validation['recommendation'] == 'keep':
                report['valid'] += 1
            elif validation['recommendation'] in ['review', 'flag_suspicious']:
                report['suspicious'] += 1
            else:
                report['rejected'] += 1
            
            if validation['issues']:
                report['issues_found'].extend([
                    {
                        'id': sighting.get('id'),
                        'issues': validation['issues'],
                        'confidence': validation['confidence']
                    }
                ])
            
            # Track state distribution
            for state in validation['mentioned_states']:
                report['state_distribution'][state] = report['state_distribution'].get(state, 0) + 1
        
        return report