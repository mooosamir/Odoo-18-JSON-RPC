#!/usr/bin/env python3
"""
Update Odoo records script for Odoo 18 JSON-RPC API.

This script handles updates for:
- stock.move records (bulk update)
- stock.picking records (field updates)

Author: Rightechs Solutions
"""

import json
import sys
from typing import List, Dict, Any
from odoo_jsonrpc_client import OdooJSONRPCClient
from config import (
    ODOO_URL, DB_NAME, USERNAME, PASSWORD,
    BULK_UPDATE_MODEL, BULK_UPDATE_RECORDS,
    STOCK_PICKING_UPDATE_FIELDS, STOCK_PICKING_IDS
)


def normalize_updates(updates: List[Dict[str, Any]], model: str) -> List[Dict[str, Any]]:
    """
    Normalize updates to handle field mappings and automatic field updates.
    
    For stock.move model:
    - If 'quantity' is updated, also update 'product_uom_qty' with the same value
    
    Args:
        updates: List of update dictionaries
        model: Model name
        
    Returns:
        Normalized list of updates
    """
    normalized = []
    
    for update in updates:
        normalized_update = update.copy()
        field_updates = {k: v for k, v in update.items() if k != 'id'}
        
        # For stock.move model, if quantity is updated, also update product_uom_qty
        if model == "stock.move" and "quantity" in field_updates:
            quantity_value = field_updates["quantity"]
            normalized_update["product_uom_qty"] = quantity_value
            print(f"   ℹ️  Auto-mapping: quantity={quantity_value} → product_uom_qty={quantity_value}")
        
        normalized.append(normalized_update)
    
    return normalized


def bulk_update_records(
    client: OdooJSONRPCClient,
    model: str,
    updates: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Update multiple records in a single batch operation.
    
    Args:
        client: Authenticated OdooJSONRPCClient instance
        model: Model name (e.g., 'stock.move')
        updates: List of dictionaries with 'id' and field updates
        
    Returns:
        Dictionary with update results and statistics
    """
    if not updates:
        return {
            "success": False,
            "message": "No records to update",
            "updated": 0,
            "failed": 0
        }
    
    # Normalize updates (handle field mappings)
    normalized_updates = normalize_updates(updates, model)
    
    results = {
        "success": True,
        "updated": 0,
        "failed": 0,
        "errors": []
    }
    
    # Group records by update values (same values = same batch)
    value_groups = {}
    
    for update in normalized_updates:
        record_id = update.get('id')
        if not record_id:
            results["errors"].append(f"Missing 'id' in update: {update}")
            results["failed"] += 1
            continue
        
        # Extract field updates (everything except 'id')
        field_updates = {k: v for k, v in update.items() if k != 'id'}
        
        if not field_updates:
            results["errors"].append(f"No fields to update for record {record_id}")
            results["failed"] += 1
            continue
        
        # Create a key from the field updates for grouping
        update_key = json.dumps(field_updates, sort_keys=True)
        
        if update_key not in value_groups:
            value_groups[update_key] = {
                "values": field_updates,
                "ids": []
            }
        
        value_groups[update_key]["ids"].append(record_id)
    
    # Update records in batches
    for update_key, group in value_groups.items():
        record_ids = group["ids"]
        values = group["values"]
        
        try:
            # Use write() with list of IDs to update multiple records at once
            result = client.call_kw(
                model,
                "write",
                [record_ids, values],
                {}
            )
            
            if result is True:
                results["updated"] += len(record_ids)
                print(f"✅ Successfully updated {len(record_ids)} record(s) with values: {values}")
            else:
                results["failed"] += len(record_ids)
                results["errors"].append(f"Update returned False for IDs: {record_ids}")
                print(f"❌ Failed to update {len(record_ids)} record(s)")
                
        except Exception as e:
            results["failed"] += len(record_ids)
            error_msg = f"Error updating IDs {record_ids}: {str(e)}"
            results["errors"].append(error_msg)
            print(f"❌ {error_msg}")
    
    if results["failed"] > 0:
        results["success"] = False
    
    return results


def update_stock_pickings(
    client: OdooJSONRPCClient,
    field_updates: Dict[str, Any],
    picking_ids: List[int]
) -> Dict[str, Any]:
    """
    Update stock.picking records with specified field values.
    
    Args:
        client: Authenticated OdooJSONRPCClient instance
        field_updates: Dictionary of field:value pairs to update
        picking_ids: List of picking IDs to update
        
    Returns:
        Dictionary with update results
    """
    if not field_updates:
        return {
            "success": False,
            "message": "No fields to update",
            "updated": 0,
            "failed": 0
        }
    
    if not picking_ids:
        return {
            "success": False,
            "message": "No picking IDs provided",
            "updated": 0,
            "failed": 0
        }
    
    results = {
        "success": True,
        "updated": 0,
        "failed": 0,
        "errors": []
    }
    
    try:
        print(f"🔄 Updating {len(picking_ids)} picking record(s) with fields: {field_updates}")
        result = client.call_kw(
            "stock.picking",
            "write",
            [picking_ids, field_updates],
            {}
        )
        
        if result is True:
            results["updated"] = len(picking_ids)
            print(f"✅ Successfully updated {len(picking_ids)} picking record(s)")
        else:
            results["failed"] = len(picking_ids)
            results["success"] = False
            results["errors"].append(f"Update returned False for IDs: {picking_ids}")
            print(f"❌ Failed to update picking records")
            
    except Exception as e:
        results["failed"] = len(picking_ids)
        results["success"] = False
        error_msg = f"Error updating pickings: {str(e)}"
        results["errors"].append(error_msg)
        print(f"❌ {error_msg}")
    
    return results


def main():
    """
    Main function to execute updates.
    """
    print("=" * 60)
    print("Odoo 18 Update Records Script")
    print("=" * 60)
    
    # Initialize client
    print(f"\n🔐 Authenticating...")
    client = OdooJSONRPCClient(ODOO_URL, DB_NAME, USERNAME, PASSWORD)
    
    try:
        auth_result = client.authenticate()
        if not auth_result:
            print("❌ Authentication failed")
            sys.exit(1)
        print("✅ Authentication successful")
        
        # Update stock.move records if configured
        if BULK_UPDATE_RECORDS:
            print(f"\n📦 Updating stock.move records...")
            print(f"   Records: {len(BULK_UPDATE_RECORDS)}")
            update_results = bulk_update_records(
                client,
                BULK_UPDATE_MODEL,
                BULK_UPDATE_RECORDS
            )
            
            print(f"\n📊 Stock Move Update Results:")
            print(f"   Updated: {update_results['updated']}")
            print(f"   Failed: {update_results['failed']}")
            if update_results['errors']:
                for error in update_results['errors']:
                    print(f"   ❌ {error}")
        
        # Update stock.picking records if configured
        if STOCK_PICKING_IDS and STOCK_PICKING_UPDATE_FIELDS:
            print(f"\n📦 Updating stock.picking records...")
            print(f"   Picking IDs: {STOCK_PICKING_IDS}")
            print(f"   Fields: {STOCK_PICKING_UPDATE_FIELDS}")
            picking_results = update_stock_pickings(
                client,
                STOCK_PICKING_UPDATE_FIELDS,
                STOCK_PICKING_IDS
            )
            
            print(f"\n📊 Stock Picking Update Results:")
            print(f"   Updated: {picking_results['updated']}")
            print(f"   Failed: {picking_results['failed']}")
            if picking_results['errors']:
                for error in picking_results['errors']:
                    print(f"   ❌ {error}")
        
        print(f"\n{'=' * 60}")
        print("✅ Update completed!")
        print(f"{'=' * 60}\n")
        
    except Exception as e:
        print(f"\n❌ Fatal error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
