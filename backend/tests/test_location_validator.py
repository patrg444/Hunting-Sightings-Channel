import pytest
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from validators.location_validator import LocationValidator

class TestLocationValidator:
    """Test cases for location validation."""
    
    def test_extract_mentioned_states(self):
        """Test state extraction from text."""
        # Test various state mentions
        test_cases = [
            ("I saw a bear in Colorado near Denver", ["colorado"]),
            ("My first bear I live in Mass. and the camera is in Virginia", ["massachusetts", "virginia"]),
            ("Hunting in WY near the CO border", ["wyoming", "colorado"]),
            ("Spotted elk in New Mexico", ["new mexico"]),
            ("Trail cam in N.H. captured moose", ["new hampshire"]),
            ("Bear sighting", []),  # No state mentioned
            ("Saw deer in CA, OR, and WA", ["california", "oregon", "washington"]),
            ("I'm in Texas", ["texas"])  # 'in' should not match Indiana
        ]
        
        for text, expected in test_cases:
            result = LocationValidator.extract_mentioned_states(text)
            assert set(result) == set(expected), f"Failed for text: {text}"
    
    def test_is_coordinate_in_colorado(self):
        """Test Colorado boundary checking."""
        # Colorado coordinates
        assert LocationValidator.is_coordinate_in_colorado(39.7392, -104.9903)  # Denver
        assert LocationValidator.is_coordinate_in_colorado(40.0150, -105.2705)  # Boulder
        
        # Outside Colorado
        assert not LocationValidator.is_coordinate_in_colorado(42.3601, -71.0589)  # Boston, MA
        assert not LocationValidator.is_coordinate_in_colorado(37.0902, -95.7129)  # Kansas
        assert not LocationValidator.is_coordinate_in_colorado(33.4484, -112.0740)  # Phoenix, AZ
    
    def test_validate_location_assignment(self):
        """Test complete location validation."""
        # Valid Colorado sighting
        validation = LocationValidator.validate_location_assignment(
            text="Saw 6 elk near Estes Park in Colorado",
            lat=40.3775,
            lon=-105.5253,
            gmu="20"
        )
        assert validation['is_valid']
        assert validation['confidence'] >= 0.8
        assert len(validation['issues']) == 0
        
        # Invalid: Virginia text with Colorado coordinates
        validation = LocationValidator.validate_location_assignment(
            text="My first bear I live in Mass. and the camera is in Virginia",
            lat=39.7392,
            lon=-104.9903,
            gmu="46"
        )
        assert not validation['is_valid']
        assert validation['confidence'] < 0.2
        assert "Text mentions non-Colorado state(s)" in str(validation['issues'])
        assert validation['recommendation'] == 'reject'
        
        # Invalid: Coordinates outside Colorado with GMU
        validation = LocationValidator.validate_location_assignment(
            text="Bear sighting",
            lat=42.3601,
            lon=-71.0589,
            gmu="12"
        )
        assert not validation['is_valid']
        assert validation['confidence'] == 0.0
        assert "GMU assigned to coordinates outside Colorado" in str(validation['issues'])
    
    def test_validation_prompt_addition(self):
        """Test the LLM prompt addition."""
        prompt = LocationValidator.get_validation_prompt_addition()
        assert "ONLY assign coordinates for locations that are explicitly in Colorado" in prompt
        assert "Virginia" in prompt
        assert "Massachusetts" in prompt
    
    def test_create_validation_report(self):
        """Test validation report generation."""
        sightings = [
            {
                'id': 1,
                'description': 'Saw elk in Colorado',
                'latitude': 39.7392,
                'longitude': -104.9903,
                'gmu_unit': '23'
            },
            {
                'id': 2,
                'description': 'Camera in Virginia captured bear',
                'latitude': 39.0,
                'longitude': -105.0,
                'gmu_unit': '46'
            }
        ]
        
        report = LocationValidator.create_validation_report(sightings)
        assert report['total'] == 2
        assert report['valid'] >= 1
        assert report['rejected'] >= 1
        assert 'virginia' in report['state_distribution']
    
    def test_edge_cases(self):
        """Test edge cases."""
        # Empty text
        validation = LocationValidator.validate_location_assignment("", None, None, None)
        assert validation['confidence'] == 1.0  # No issues if no claims made
        
        # Text with state abbreviation in word
        validation = LocationValidator.validate_location_assignment(
            "Scoring system for hunting",  # Contains "or" but not Oregon
            39.7392,
            -104.9903,
            "23"
        )
        assert validation['is_valid']
        assert 'oregon' not in validation['mentioned_states']

if __name__ == "__main__":
    pytest.main([__file__, "-v"])