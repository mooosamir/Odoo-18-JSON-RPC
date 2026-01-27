#!/usr/bin/env python3
"""
Update stock.picking status script for Odoo 18 JSON-RPC API.

This script updates stock.picking records with status-related fields.
Specifically designed for updating order status and delivery information.

Author: Rightechs Solutions
"""

import sys
from odoo_jsonrpc_client import OdooJSONRPCClient
from config import (
    ODOO_URL, DB_NAME, USERNAME, PASSWORD,
    STOCK_PICKING_UPDATE_FIELDS, STOCK_PICKING_IDS
)


def update_stock_picking_status(
    client: OdooJSONRPCClient,
    field_updates: dict,
    picking_ids: list
) -> dict:
    """
    Update stock.picking records with status-related fields.
    
    Args:
        client: Authenticated OdooJSONRPCClient instance
        field_updates: Dictionary of field:value pairs to update
        picking_ids: List of picking IDs to update
        
    Returns:
        Dictionary with update results and statistics
    """
    if not field_updates:
        return {
            "success": False,
            "message": "No fields to update",
            "updated": 0,
            "failed": 0,
            "errors": []
        }
    
    if not picking_ids:
        return {
            "success": False,
            "message": "No picking IDs provided",
            "updated": 0,
            "failed": 0,
            "errors": []
        }
    
    results = {
        "success": True,
        "updated": 0,
        "failed": 0,
        "errors": [],
        "picking_ids": []
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
            results["picking_ids"] = picking_ids
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


def verify_picking_updates(
    client: OdooJSONRPCClient,
    picking_ids: list,
    expected_fields: dict
) -> dict:
    """
    Verify that picking updates were applied correctly.
    
    Args:
        client: Authenticated OdooJSONRPCClient instance
        picking_ids: List of picking IDs to verify
        expected_fields: Dictionary of expected field values
        
    Returns:
        Dictionary with verification results
    """
    verification_results = {
        "verified": 0,
        "failed": 0,
        "errors": []
    }
    
    if not picking_ids:
        return verification_results
    
    # Read pickings to verify
    fields_to_read = list(expected_fields.keys())
    
    try:
        domain = [('id', 'in', picking_ids)]
        records = client.search_read("stock.picking", domain, fields_to_read)
        
        # Create a map of ID to record
        records_map = {record['id']: record for record in records}
        
        # Verify each picking
        for picking_id in picking_ids:
            record = records_map.get(picking_id)
            if not record:
                verification_results["failed"] += 1
                verification_results["errors"].append(f"Picking {picking_id} not found")
                continue
            
            # Check each field
            all_match = True
            for field, expected_value in expected_fields.items():
                actual_value = record.get(field)
                
                # Handle boolean comparison
                if isinstance(expected_value, bool):
                    actual_bool = bool(actual_value) if actual_value is not None else False
                    if actual_bool != expected_value:
                        all_match = False
                        error_msg = f"Picking {picking_id}: {field} = {actual_bool} (expected {expected_value})"
                        verification_results["errors"].append(error_msg)
                # Handle Many2one fields (returned as [id, name] tuple)
                elif isinstance(actual_value, list) and len(actual_value) >= 1:
                    # Many2one field: compare ID only
                    actual_id = actual_value[0] if actual_value else None
                    if actual_id != expected_value:
                        all_match = False
                        error_msg = f"Picking {picking_id}: {field} = {actual_id} (expected {expected_value})"
                        verification_results["errors"].append(error_msg)
                else:
                    # Direct value comparison
                    if actual_value != expected_value:
                        all_match = False
                        error_msg = f"Picking {picking_id}: {field} = {actual_value} (expected {expected_value})"
                        verification_results["errors"].append(error_msg)
            
            if all_match:
                verification_results["verified"] += 1
                print(f"✅ Verified picking {picking_id}")
            else:
                verification_results["failed"] += 1
                print(f"❌ Verification failed for picking {picking_id}")
                
    except Exception as e:
        verification_results["errors"].append(f"Verification error: {str(e)}")
        print(f"❌ Verification error: {str(e)}")
    
    return verification_results


def main():
    """
    Main function to execute stock.picking status updates.
    """
    print("=" * 60)
    print("Odoo 18 Stock Picking Status Update")
    print("=" * 60)
    print(f"\n📋 Configuration:")
    print(f"   Model: stock.picking")
    print(f"   Fields to update: {STOCK_PICKING_UPDATE_FIELDS}")
    print(f"   Picking IDs: {STOCK_PICKING_IDS}")
    
    if not STOCK_PICKING_IDS:
        print("\n⚠️  No picking IDs specified in config.py")
        print("   Please set STOCK_PICKING_IDS in config.py")
        print("   Example: STOCK_PICKING_IDS = [108080, 108081]")
        sys.exit(1)
    
    # Initialize client
    print(f"\n🔐 Authenticating...")
    client = OdooJSONRPCClient(ODOO_URL, DB_NAME, USERNAME, PASSWORD)
    
    try:
        auth_result = client.authenticate()
        if not auth_result:
            print("❌ Authentication failed")
            sys.exit(1)
        print("✅ Authentication successful")
        
        # Update stock.picking records
        print(f"\n🔄 Updating stock.picking records...")
        update_results = update_stock_picking_status(
            client,
            STOCK_PICKING_UPDATE_FIELDS,
            STOCK_PICKING_IDS
        )
        
        # Print results
        print(f"\n📊 Update Results:")
        print(f"   Success: {update_results['success']}")
        print(f"   Updated: {update_results['updated']}")
        print(f"   Failed: {update_results['failed']}")
        
        if update_results.get('picking_ids'):
            print(f"   Updated IDs: {update_results['picking_ids']}")
        
        if update_results['errors']:
            print(f"\n❌ Errors:")
            for error in update_results['errors']:
                print(f"   - {error}")
        
        # Verify updates
        if update_results['success'] and update_results['updated'] > 0:
            print(f"\n🔍 Verifying updates...")
            verification_results = verify_picking_updates(
                client,
                update_results['picking_ids'],
                STOCK_PICKING_UPDATE_FIELDS
            )
            
            print(f"\n✅ Verification Results:")
            print(f"   Verified: {verification_results['verified']}")
            print(f"   Failed: {verification_results['failed']}")
            
            if verification_results['errors']:
                print(f"\n⚠️  Verification Errors:")
                for error in verification_results['errors']:
                    print(f"   - {error}")
        
        # Final status
        print(f"\n{'=' * 60}")
        if update_results['success'] and update_results['updated'] > 0:
            print("✅ Stock picking status update completed successfully!")
        else:
            print("❌ Stock picking status update completed with errors")
        print(f"{'=' * 60}\n")
        
    except Exception as e:
        print(f"\n❌ Fatal error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
