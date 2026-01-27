#!/usr/bin/env python3
"""
Fetch stock.picking data script for Odoo 18 JSON-RPC API.

This script fetches stock.picking record with related stock.move records
and saves the data to a JSON file.

Author: Rightechs Solutions
"""

import json
import sys
from odoo_jsonrpc_client import OdooJSONRPCClient
from config import (
    ODOO_URL, DB_NAME, USERNAME, PASSWORD, PICKING_ID
)

# Field whitelists - ONLY these fields will be fetched
STOCK_PICKING_WHITELIST = [
    "id",
    "name",
    "origin",
    "move_type",
    "state",
    "location_id",
    "location_dest_id",
    "move_ids_without_package",
    "picking_type_id",
    "warehouse_address_id",
    "picking_type_code",
    "partner_id",
    "sale_id",
    "salla_order_status_id"
]

STOCK_MOVE_WHITELIST = [
    "id",
    "product_id",
    "never_product_template_attribute_value_ids",
    "description_picking",
    "product_qty",
    "product_uom_qty",
    "product_uom",
    "product_uom_category_id",
    "product_tmpl_id"
]


def fetch_stock_picking_data(picking_id: int) -> dict:
    """
    Fetch stock.picking record with related moves.
    
    Args:
        picking_id: Stock picking record ID
        
    Returns:
        Complete data structure with picking and moves
    """
    # Initialize client
    client = OdooJSONRPCClient(ODOO_URL, DB_NAME, USERNAME, PASSWORD)
    client.authenticate()
    
    # Fetch picking with whitelisted fields
    picking = client.read_record("stock.picking", picking_id, STOCK_PICKING_WHITELIST)
    
    # Extract move IDs
    move_ids = picking.get('move_ids_without_package', [])
    
    # Fetch moves with whitelisted fields
    moves = []
    if move_ids:
        domain = [('id', 'in', move_ids)]
        moves = client.search_read("stock.move", domain, STOCK_MOVE_WHITELIST)
    
    # Build clean JSON structure
    complete_data = {
        "stock_picking": {
            "id": picking['id'],
            "name": picking.get('name'),
            "origin": picking.get('origin'),
            "move_type": picking.get('move_type'),
            "state": picking.get('state'),
            "location_id": picking.get('location_id'),
            "location_dest_id": picking.get('location_dest_id'),
            "picking_type_id": picking.get('picking_type_id'),
            "warehouse_address_id": picking.get('warehouse_address_id'),
            "picking_type_code": picking.get('picking_type_code'),
            "partner_id": picking.get('partner_id'),
            "sale_id": picking.get('sale_id'),
            "salla_order_status_id": picking.get('salla_order_status_id'),
            "move_ids": move_ids,
            "moves": [
                {
                    "id": move['id'],
                    "product_id": move.get('product_id'),
                    "never_product_template_attribute_value_ids": move.get('never_product_template_attribute_value_ids'),
                    "description_picking": move.get('description_picking'),
                    "product_qty": move.get('product_qty'),
                    "product_uom_qty": move.get('product_uom_qty'),
                    "product_uom": move.get('product_uom'),
                    "product_uom_category_id": move.get('product_uom_category_id'),
                    "product_tmpl_id": move.get('product_tmpl_id')
                }
                for move in moves
            ]
        }
    }
    
    return complete_data


def main():
    """
    Main function to fetch and save stock.picking data.
    """
    print("=" * 60)
    print("Odoo 18 Fetch Stock Picking Data")
    print("=" * 60)
    print(f"\n📋 Configuration:")
    print(f"   Picking ID: {PICKING_ID}")
    
    try:
        # Fetch data
        print(f"\n🔄 Fetching data...")
        data = fetch_stock_picking_data(PICKING_ID)
        
        # Save to file
        filename = f"stock_picking_{PICKING_ID}.json"
        print(f"\n💾 Saving to {filename}...")
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, default=str, indent=2, ensure_ascii=False)
        
        # Print summary
        picking = data["stock_picking"]
        print(f"\n✅ Data fetched successfully!")
        print(f"   Picking: {picking['name']}")
        print(f"   State: {picking.get('state')}")
        print(f"   Moves: {len(picking['moves'])}")
        print(f"   File: {filename}")
        print(f"\n{'=' * 60}\n")
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
