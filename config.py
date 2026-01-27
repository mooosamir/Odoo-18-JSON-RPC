"""
Configuration module for Odoo 18 JSON-RPC API tests.

This module contains all configurable variables for connecting to Odoo
and specifying which records to test.
"""

# Odoo Server Configuration
ODOO_URL = "http://localhost:8018"
DB_NAME = "18_odoo"
USERNAME = "admin"
PASSWORD = "admin"

# Test Record Configuration
PICKING_ID = 108080  # The stock.picking record ID to fetch and test

# JSON-RPC Endpoints
ENDPOINT_AUTH = "/web/session/authenticate"
ENDPOINT_CALL_KW = "/web/dataset/call_kw"

# Request Headers
JSON_HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json"
}

# Timeout settings (in seconds)
REQUEST_TIMEOUT = 30

# Bulk Update Configuration
# List of records to update in bulk
# Format: [{"id": record_id, "field_name": value}, ...]
BULK_UPDATE_RECORDS = [
    {
        "id": 299986,
        "quantity": 99,
    },
    {
        "id": 299987,
        "quantity": 99,
    },
]

# Model name for bulk updates
BULK_UPDATE_MODEL = "stock.move"

# Stock Picking Update Configuration
# Fields to update in stock.picking records
STOCK_PICKING_UPDATE_FIELDS = {
    "salla_order_status_id": 2,
    "x_studio_delivered": True,
}

# List of stock.picking record IDs to update
# Specify IDs: [108080, 108081, ...]
# Example: STOCK_PICKING_IDS = [108080]
STOCK_PICKING_IDS = [108080]  # List of picking IDs to update