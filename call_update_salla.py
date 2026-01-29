#!/usr/bin/env python3
"""
Call update_salla method script for Odoo 18 JSON-RPC API.

This script calls the update_salla method in stock.picking model
via JSON-RPC API.

Author: Rightechs Solutions
"""

import sys
import argparse
from odoo_jsonrpc_client import OdooJSONRPCClient
from config import (
    ODOO_URL, DB_NAME, USERNAME, PASSWORD, PICKING_ID
)


def call_update_salla(client: OdooJSONRPCClient, picking_id: int) -> dict:
    """
    Call the update_salla method in stock.picking model.
    
    This method is decorated with @api.model, so it can be called
    directly on the model without needing a record instance.
    
    Args:
        client: Authenticated OdooJSONRPCClient instance
        picking_id: The picking ID to pass to the method
        
    Returns:
        Dictionary with method call results
    """
    try:
        # Call the update_salla method on stock.picking model
        # Since it's @api.model, we call it directly on the model
        # The method signature: def update_salla(self, picking_id)
        result = client.call_kw(
            model="stock.picking",
            method="update_salla",
            args=[picking_id],
            kwargs={}
        )
        
        return {
            "success": True,
            "picking_id": picking_id,
            "result": result,
            "message": f"Successfully called update_salla for picking {picking_id}"
        }
    
    except Exception as e:
        return {
            "success": False,
            "picking_id": picking_id,
            "error": str(e),
            "message": f"Failed to call update_salla for picking {picking_id}: {str(e)}"
        }


def main():
    """
    Main function to call update_salla method.
    
    Supports command-line argument for picking_id:
    python3 call_update_salla.py [picking_id]
    """
    # Parse command-line arguments
    parser = argparse.ArgumentParser(
        description="Call update_salla method in stock.picking model"
    )
    parser.add_argument(
        "picking_id",
        type=int,
        nargs="?",
        default=PICKING_ID,
        help=f"Picking ID to pass to update_salla (default: {PICKING_ID} from config)"
    )
    args = parser.parse_args()
    
    picking_id = args.picking_id
    
    print("=" * 60)
    print("Odoo 18 Call update_salla Method")
    print("=" * 60)
    print()
    
    print("📋 Configuration:")
    print(f"   Model: stock.picking")
    print(f"   Method: update_salla")
    print(f"   Picking ID: {picking_id}")
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
    
    # Call update_salla method
    print("🔄 Calling update_salla method...")
    result = call_update_salla(client, picking_id)
    
    if result["success"]:
        print(f"✅ {result['message']}")
        print()
        print("📊 Method Call Results:")
        print(f"   Picking ID: {result['picking_id']}")
        print(f"   Result: {result.get('result', 'No return value')}")
    else:
        print(f"❌ {result['message']}")
        print()
        print("📊 Error Details:")
        print(f"   Error: {result.get('error', 'Unknown error')}")
        sys.exit(1)
    
    print()
    print("=" * 60)
    print("✅ update_salla method call completed!")
    print("=" * 60)


if __name__ == "__main__":
    main()
