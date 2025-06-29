#!/usr/bin/env python3
"""
Script to validate existing sighting locations and identify/fix cross-state assignment errors.
"""

import os
import sys
import json
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
import logging

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from validators.location_validator import LocationValidator

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def get_db_connection():
    """Create database connection."""
    try:
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            port=os.getenv('DB_PORT', 5432),
            database=os.getenv('DB_NAME', 'wildlife_sightings'),
            user=os.getenv('DB_USER', 'postgres'),
            password=os.getenv('DB_PASSWORD')
        )
        return conn
    except Exception as e:
        logger.error(f"Failed to connect to database: {e}")
        raise

def validate_all_sightings(fix_issues=False):
    """Validate all sightings and optionally fix issues."""
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        # Get all sightings with location data
        cur.execute("""
            SELECT id, source, description, latitude, longitude, gmu_unit, 
                   location_name, location_description, created_at
            FROM wildlife_sightings
            WHERE latitude IS NOT NULL OR gmu_unit IS NOT NULL
            ORDER BY created_at DESC
        """)
        
        sightings = cur.fetchall()
        logger.info(f"Found {len(sightings)} sightings to validate")
        
        # Validate each sighting
        issues_found = []
        fixed_count = 0
        
        for sighting in sightings:
            validation = LocationValidator.validate_location_assignment(
                text=sighting['description'] or '',
                lat=sighting['latitude'],
                lon=sighting['longitude'],
                gmu=sighting['gmu_unit']
            )
            
            if not validation['is_valid'] or validation['confidence'] < 0.5:
                issue = {
                    'id': sighting['id'],
                    'source': sighting['source'],
                    'gmu': sighting['gmu_unit'],
                    'lat': sighting['latitude'],
                    'lon': sighting['longitude'],
                    'location_name': sighting['location_name'],
                    'confidence': validation['confidence'],
                    'issues': validation['issues'],
                    'mentioned_states': validation['mentioned_states'],
                    'recommendation': validation['recommendation'],
                    'description_snippet': sighting['description'][:200] if sighting['description'] else None
                }
                issues_found.append(issue)
                
                # Log specific case we're looking for
                if sighting['description'] and ('virginia' in sighting['description'].lower() or 
                                               'massachusetts' in sighting['description'].lower() or
                                               'mass.' in sighting['description'].lower()):
                    logger.warning(f"Found problematic sighting ID {sighting['id']}: {issue}")
                
                # Fix severe issues if requested
                if fix_issues and validation['confidence'] < 0.2:
                    logger.info(f"Fixing sighting {sighting['id']} - clearing invalid location data")
                    cur.execute("""
                        UPDATE wildlife_sightings
                        SET latitude = NULL, longitude = NULL, gmu_unit = NULL,
                            location_validation_confidence = %s,
                            location_validation_issues = %s
                        WHERE id = %s
                    """, (validation['confidence'], json.dumps(validation['issues']), sighting['id']))
                    fixed_count += 1
        
        if fix_issues:
            conn.commit()
            logger.info(f"Fixed {fixed_count} sightings with severe location issues")
        
        # Generate report
        report = LocationValidator.create_validation_report([
            {'id': s['id'], 'description': s['description'], 
             'latitude': s['latitude'], 'longitude': s['longitude'], 
             'gmu_unit': s['gmu_unit']}
            for s in sightings
        ])
        
        # Save detailed issues report
        report_file = f'location_validation_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        with open(report_file, 'w') as f:
            json.dump({
                'summary': report,
                'issues': issues_found,
                'timestamp': datetime.now().isoformat()
            }, f, indent=2)
        
        logger.info(f"Report saved to {report_file}")
        
        # Print summary
        print("\n=== Location Validation Report ===")
        print(f"Total sightings: {report['total']}")
        print(f"Valid: {report['valid']}")
        print(f"Suspicious: {report['suspicious']}")
        print(f"Rejected: {report['rejected']}")
        print(f"\nState distribution: {report['state_distribution']}")
        print(f"\nFound {len(issues_found)} sightings with location issues")
        
        # Show some example issues
        if issues_found:
            print("\n=== Example Issues ===")
            for issue in issues_found[:5]:
                print(f"\nID: {issue['id']} (Source: {issue['source']})")
                print(f"GMU: {issue['gmu']}, Coordinates: ({issue['lat']}, {issue['lon']})")
                print(f"Confidence: {issue['confidence']:.2f}")
                print(f"Issues: {', '.join(issue['issues'])}")
                print(f"States mentioned: {issue['mentioned_states']}")
                if issue['description_snippet']:
                    print(f"Text: {issue['description_snippet'][:100]}...")
        
        return issues_found
        
    except Exception as e:
        logger.error(f"Error during validation: {e}")
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()

def find_specific_sighting():
    """Find the specific Virginia/Massachusetts sighting."""
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        # Search for sightings mentioning Virginia or Massachusetts
        cur.execute("""
            SELECT id, source, description, latitude, longitude, gmu_unit, 
                   location_name, created_at
            FROM wildlife_sightings
            WHERE (description ILIKE '%virginia%' OR 
                   description ILIKE '%massachusetts%' OR
                   description ILIKE '%mass.%') 
            AND gmu_unit IS NOT NULL
            ORDER BY created_at DESC
        """)
        
        results = cur.fetchall()
        logger.info(f"Found {len(results)} sightings mentioning Virginia/Massachusetts with GMU assigned")
        
        for sighting in results:
            print(f"\n=== Sighting ID: {sighting['id']} ===")
            print(f"Source: {sighting['source']}")
            print(f"GMU: {sighting['gmu_unit']}")
            print(f"Coordinates: ({sighting['latitude']}, {sighting['longitude']})")
            print(f"Location: {sighting['location_name']}")
            print(f"Description: {sighting['description'][:300]}...")
            
            # Validate this sighting
            validation = LocationValidator.validate_location_assignment(
                text=sighting['description'],
                lat=sighting['latitude'],
                lon=sighting['longitude'],
                gmu=sighting['gmu_unit']
            )
            print(f"Validation confidence: {validation['confidence']}")
            print(f"Issues: {validation['issues']}")
        
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Validate sighting locations')
    parser.add_argument('--fix', action='store_true', help='Fix severe location issues')
    parser.add_argument('--find-specific', action='store_true', 
                       help='Find specific Virginia/Massachusetts sighting')
    args = parser.parse_args()
    
    if args.find_specific:
        find_specific_sighting()
    else:
        validate_all_sightings(fix_issues=args.fix)