#!/usr/bin/env python3
"""
Validate stock picking script for Odoo 18 JSON-RPC API.

This script calls the button_validate method on stock.picking records
with context parameters (skip_sms=True, cancel_backorder=True) via JSON-RPC API.

The button_validate method validates/confirms a stock picking operation.
With the context parameters:
- skip_sms: Skip sending SMS notifications
- cancel_backorder: Cancel any backorder that would be created

Author: Rightechs Solutions
"""

import sys
import argparse
from odoo_jsonrpc_client import OdooJSONRPCClient
from config import (
    ODOO_URL, DB_NAME, USERNAME, PASSWORD, PICKING_ID
)


def validate_picking(
    client: OdooJSONRPCClient,
    picking_id: int,
    skip_sms: bool = True,
    cancel_backorder: bool = True
) -> dict:
    """
    Call the button_validate method on stock.picking record with context.
    
    This method validates/confirms a stock picking operation. It's a record
    method (not @api.model), so it must be called on a specific record.
    
    Equivalent to Odoo code:
    picking.with_context(skip_sms=True, cancel_backorder=True).button_validate()
    
    Args:
        client: Authenticated OdooJSONRPCClient instance
        picking_id: The picking record ID to validate
        skip_sms: Skip sending SMS notifications (default: True)
        cancel_backorder: Cancel backorder if created (default: True)
        
    Returns:
        Dictionary with method call results
    """
    try:
        # Prepare context parameters
        # In Odoo, to validate without backorder, we use 'skip_backorder' in context
        context_params = {
            "skip_sms": skip_sms,
            "skip_backorder": cancel_backorder,  # True = no backorder
            "cancel_backorder": cancel_backorder  # Compatibility
        }
        
        # Try button_validate first
        result = client.call_kw(
            model="stock.picking",
            method="button_validate",
            args=[[picking_id]],  # List of record IDs (recordset)
            kwargs={},
            context=context_params
        )
        
        # Check if result is an action (wizard opened)
        # If button_validate returns an action dict, it means wizard was opened
        if isinstance(result, dict) and result.get('type') == 'ir.actions.act_window':
            # Wizard was opened, we need to handle it
            wizard_model = result.get('res_model', '')
            
            if wizard_model == 'stock.backorder.confirmation':
                # Backorder confirmation wizard opened
                # Get picking IDs from wizard context
                wizard_context = result.get('context', {})
                pick_ids = wizard_context.get('default_pick_ids', [picking_id])
                
                # Create wizard record and process without backorder
                wizard_id = client.call_kw(
                    model="stock.backorder.confirmation",
                    method="create",
                    args=[{
                        "pick_ids": [(6, 0, pick_ids)]
                    }],
                    kwargs={},
                    context=context_params
                )
                
                # Process without creating backorder
                result = client.call_kw(
                    model="stock.backorder.confirmation",
                    method="process_cancel_backorder",
                    args=[[wizard_id]],
                    kwargs={},
                    context=context_params
                )
            else:
                # Unknown wizard or other action, try _action_done directly
                print(f"   ⚠️  Wizard opened ({wizard_model}), trying _action_done directly...")
                result = client.call_kw(
                    model="stock.picking",
                    method="_action_done",
                    args=[[picking_id]],
                    kwargs={},
                    context=context_params
                )
        
        return {
            "success": True,
            "picking_id": picking_id,
            "result": result,
            "context": {
                "skip_sms": skip_sms,
                "cancel_backorder": cancel_backorder
            },
            "message": f"Successfully validated picking {picking_id}"
        }
    
    except Exception as e:
        return {
            "success": False,
            "picking_id": picking_id,
            "error": str(e),
            "context": {
                "skip_sms": skip_sms,
                "cancel_backorder": cancel_backorder
            },
            "message": f"Failed to validate picking {picking_id}: {str(e)}"
        }


def main():
    """
    Main function to validate stock picking.
    
    Supports command-line arguments:
    python3 validate_picking.py [picking_id] [--skip-sms] [--no-cancel-backorder]
    """
    # Parse command-line arguments
    parser = argparse.ArgumentParser(
        description="Validate stock.picking record with button_validate method"
    )
    parser.add_argument(
        "picking_id",
        type=int,
        nargs="?",
        default=PICKING_ID,
        help=f"Picking ID to validate (default: {PICKING_ID} from config)"
    )
    parser.add_argument(
        "--skip-sms",
        action="store_true",
        default=True,
        help="Skip sending SMS notifications (default: True)"
    )
    parser.add_argument(
        "--no-skip-sms",
        action="store_false",
        dest="skip_sms",
        help="Send SMS notifications"
    )
    parser.add_argument(
        "--cancel-backorder",
        action="store_true",
        default=True,
        help="Cancel backorder if created (default: True)"
    )
    parser.add_argument(
        "--no-cancel-backorder",
        action="store_false",
        dest="cancel_backorder",
        help="Allow backorder creation"
    )
    args = parser.parse_args()
    
    picking_id = args.picking_id
    skip_sms = args.skip_sms
    cancel_backorder = args.cancel_backorder
    
    print("=" * 60)
    print("Odoo 18 Validate Stock Picking")
    print("=" * 60)
    print()
    
    print("📋 Configuration:")
    print(f"   Model: stock.picking")
    print(f"   Method: button_validate")
    print(f"   Picking ID: {picking_id}")
    print(f"   Context:")
    print(f"      skip_sms: {skip_sms}")
    print(f"      cancel_backorder: {cancel_backorder}")
    print()
    
    # Initialize client
    client = OdooJSONRPCClient(ODOO_URL, DB_NAME, USERNAME, PASSWORD)
    
    # Authenticate
    print("🔐 Authenticating...")
    try:
        auth_result = client.authenticate()
        if not auth_result:
            print("❌ Authentication failed")
            sys.exit(1)
        print("✅ Authentication successful")
        print()
    except Exception as e:
        print(f"❌ Fatal error: {str(e)}")
        sys.exit(1)
    
    # Validate picking
    print("🔄 Validating stock picking...")
    print(f"   Calling: button_validate() with context")
    print(f"   Context: skip_sms={skip_sms}, cancel_backorder={cancel_backorder}")
    print()
    
    result = validate_picking(client, picking_id, skip_sms, cancel_backorder)
    
    if result["success"]:
        print(f"✅ {result['message']}")
        print()
        print("📊 Validation Results:")
        print(f"   Picking ID: {result['picking_id']}")
        print(f"   Result: {result.get('result', 'No return value')}")
        print(f"   Context Applied:")
        print(f"      skip_sms: {result['context']['skip_sms']}")
        print(f"      cancel_backorder: {result['context']['cancel_backorder']}")
    else:
        print(f"❌ {result['message']}")
        print()
        print("📊 Error Details:")
        print(f"   Error: {result.get('error', 'Unknown error')}")
        print(f"   Context Attempted:")
        print(f"      skip_sms: {result['context']['skip_sms']}")
        print(f"      cancel_backorder: {result['context']['cancel_backorder']}")
        sys.exit(1)
    
    print()
    print("=" * 60)
    print("✅ Stock picking validation completed!")
    print("=" * 60)


if __name__ == "__main__":
    main()
