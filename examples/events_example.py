import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import argparse
import logging
import urllib3
import json
from zvma import ZVMAClient
from datetime import datetime, timedelta

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def main():
    parser = argparse.ArgumentParser(description="Zerto Events Example")
    parser.add_argument("--zvm_address", required=True, help="ZVM address")
    parser.add_argument('--client_id', required=True, help='Keycloak client ID')
    parser.add_argument('--client_secret', required=True, help='Keycloak client secret')
    parser.add_argument("--ignore_ssl", action="store_true", help="Ignore SSL certificate verification")
    args = parser.parse_args()

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    try:
        # Connect to ZVM
        logging.info(f"Connecting to ZVM at {args.zvm_address}")
        client = ZVMAClient(
            zvm_address=args.zvm_address,
            client_id=args.client_id,
            client_secret=args.client_secret,
            verify_certificate=not args.ignore_ssl
        )

        # Get event types
        logging.info("\nFetching event types...")
        event_types = client.events.list_event_types()
        logging.info(f"Found {len(event_types)} event types:")
        logging.info(json.dumps(event_types[:3], indent=2))  # Show first 3 for brevity

        # Get event entities
        logging.info("\nFetching event entities...")
        event_entities = client.events.list_event_entities()
        logging.info(f"Found {len(event_entities)} event entities:")
        logging.info(json.dumps(event_entities[:3], indent=2))  # Show first 3 for brevity

        # Get event categories
        logging.info("\nFetching event categories...")
        event_categories = client.events.list_event_categories()
        logging.info(f"Found {len(event_categories)} event categories:")
        logging.info(json.dumps(event_categories[:3], indent=2))  # Show first 3 for brevity

        # Get events from the last 1 hour
        start_date = (datetime.utcnow() - timedelta(hours=1)).isoformat() + 'Z'
        end_date = datetime.utcnow().isoformat() + 'Z'
        
        logging.info(f"\nFetching events from {start_date} to {end_date}...")
        events = client.events.list_events(
            start_date=start_date,
            end_date=end_date
        )
        logging.info(f"Found {len(events)} events in the last 24 hours:")
        if events:
            logging.info(json.dumps(events[:3], indent=2))  # Show first 3 for brevity

        # Get events with filters
        logging.info("\nFetching filtered events...")
        filtered_events = client.events.list_events(
            start_date=start_date,
            end_date=end_date,
            event_type=18,  # Using numeric event type
            category="Events"  # Using correct category from list_event_categories
        )
        logging.info(f"Found {len(filtered_events)} filtered events:")
        if filtered_events:
            logging.info(json.dumps(filtered_events[:3], indent=2))  # Show first 3 for brevity

        # If we have any events, get details for a specific event
        if events:
            event_id = events[0].get('EventIdentifier')
            logging.info(f"\nFetching details for event {event_id}...")
            event_details = client.events.list_events(event_identifier=event_id)
            logging.info("Event details:")
            logging.info(json.dumps(event_details, indent=2))

    except Exception as e:
        logging.error(f"Error occurred: {e}")
        raise

if __name__ == "__main__":
    main() 