#!/usr/bin/env python3
"""
Fetch salla.order.status data script for Odoo 18 JSON-RPC API.

This script fetches all salla.order.status records with whitelisted fields
and saves the data to a JSON file.

Author: Rightechs Solutions
"""

import json
import sys
from odoo_jsonrpc_client import OdooJSONRPCClient
from config import (
    ODOO_URL, DB_NAME, USERNAME, PASSWORD
)

# Whitelist of fields to fetch (ONLY these fields)
SALLA_ORDER_STATUS_WHITELIST = [
    "id",
    "salla_status_id",
    "name",
    "type",
    "slug"
]


def fetch_salla_order_status() -> dict:
    """
    Fetch all salla.order.status records with whitelisted fields.
    
    Returns:
        Complete data structure with all status records
    """
    # Initialize client
    client = OdooJSONRPCClient(ODOO_URL, DB_NAME, USERNAME, PASSWORD)
    client.authenticate()
    
    # Fetch all records with ONLY whitelisted fields
    domain = []  # Empty domain = all records
    all_records = client.search_read("salla.order.status", domain, SALLA_ORDER_STATUS_WHITELIST)
    
    # Build clean data structure
    complete_data = {
        "model": "salla.order.status",
        "total_records": len(all_records),
        "records": [
            {
                "id": record['id'],
                "salla_status_id": record.get('salla_status_id'),
                "name": record.get('name'),
                "type": record.get('type'),
                "slug": record.get('slug')
            }
            for record in all_records
        ]
    }
    
    return complete_data


def main():
    """
    Main function to fetch and save salla.order.status data.
    """
    print("=" * 60)
    print("Odoo 18 Fetch Salla Order Status")
    print("=" * 60)
    
    try:
        # Fetch data
        print(f"\n🔄 Fetching salla.order.status records...")
        data = fetch_salla_order_status()
        
        # Save to file
        filename = "salla_order_status_all.json"
        print(f"\n💾 Saving to {filename}...")
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, default=str, indent=2, ensure_ascii=False)
        
        # Print summary
        print(f"\n✅ Data fetched successfully!")
        print(f"   Total Records: {data['total_records']}")
        print(f"   File: {filename}")
        
        # Show sample record
        if data['records']:
            sample = data['records'][0]
            print(f"\n📋 Sample Record:")
            print(f"   ID: {sample['id']}")
            print(f"   Name: {sample.get('name')}")
            print(f"   Slug: {sample.get('slug')}")
        
        print(f"\n{'=' * 60}\n")
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
