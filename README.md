# Odoo 18 JSON-RPC Integration Suite

A professional, production-ready Python integration suite for Odoo 18 that provides clean, efficient data extraction and update capabilities using JSON-RPC API. This project enables seamless integration between external systems and Odoo 18, focusing on stock management operations and order status tracking.

## Overview

This project serves as a robust integration layer for Odoo 18, enabling external systems to interact with Odoo's stock management and order processing modules through a standardized JSON-RPC interface. The suite is designed with enterprise-grade principles, emphasizing maintainability, scalability, and clean architecture.

### Purpose

The integration suite addresses common enterprise needs:

- **Data Synchronization**: Extract stock picking and related movement data from Odoo for external system integration
- **Automated Updates**: Update Odoo records programmatically using structured JSON data
- **Reference Data Management**: Fetch and maintain reference data such as order statuses for mapping and validation
- **Custom Method Invocation**: Call custom Odoo model methods via JSON-RPC API
- **Integration Testing**: Provide a reliable foundation for testing Odoo integrations
- **API-First Approach**: Enable external systems to interact with Odoo without direct database access

### Typical Use Cases

- **ERP Integration**: Synchronize stock movements between Odoo and external warehouse management systems
- **Order Processing**: Update order statuses and delivery information from external order management platforms
- **Reporting & Analytics**: Extract structured data for business intelligence and reporting systems
- **Automation Workflows**: Automate repetitive data entry and status updates
- **Data Migration**: Facilitate data migration and bulk updates during system transitions

## Project Architecture

The project follows a clean, modular architecture that separates concerns and promotes reusability:

```
┌─────────────────────────────────────────────────────────────┐
│                    External Systems                          │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│              Python Integration Scripts                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │ fetch_data.py│  │update_data.py│  │fetch_status.py│    │
│  │              │  │update_picking_│  │              │    │
│  │              │  │status.py      │  │              │    │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘    │
│         │                  │                  │             │
│  ┌──────┴───────┐  ┌──────┴───────┐                        │
│  │call_update_  │  │              │                        │
│  │salla.py      │  │              │                        │
│  └──────┬───────┘  └──────┬───────┘                        │
│         │                  │                  │             │
│         └──────────────────┼──────────────────┘             │
│                            │                                │
│                            ▼                                │
│              ┌─────────────────────────┐                   │
│              │ odoo_jsonrpc_client.py   │                   │
│              │  (Unified Client)       │                   │
│              └─────────────┬───────────┘                   │
└────────────────────────────┼────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────┐
│                    Odoo 18 Server                           │
│              (JSON-RPC API Endpoints)                       │
└─────────────────────────────────────────────────────────────┘
```

### Core Principles

1. **Unified Client Architecture**: All JSON-RPC communication flows through a single, well-tested client module
2. **Field Whitelisting**: Only specified fields are fetched, reducing payload size and improving performance
3. **Separation of Concerns**: Each script has a single, well-defined responsibility
4. **Configuration-Driven**: All connection parameters and update rules are centralized in configuration
5. **JSON as Data Contract**: Structured JSON files serve as both output and input, enabling replay scenarios

## File Responsibilities

### `config.py`

**Purpose**: Central configuration management for the entire integration suite.

**Responsibilities**:
- Stores Odoo server connection parameters (URL, database, credentials)
- Defines record IDs and test data identifiers
- Configures bulk update operations and field mappings
- Centralizes all environment-specific settings

**Why It Exists**: Centralizing configuration eliminates hardcoded values scattered across multiple files, making the system easier to maintain, deploy across environments, and secure (credentials can be externalized).

**Interactions**: All other modules import configuration values from this file, ensuring consistency across the entire suite.

**Key Configuration Sections**:
- Odoo server connection settings
- Stock picking record identifiers
- Bulk update specifications for stock.move records
- Stock picking field update configurations

---

### `odoo_jsonrpc_client.py`

**Purpose**: Core JSON-RPC client abstraction layer providing unified communication with Odoo 18.

**Responsibilities**:
- Handles JSON-RPC protocol communication
- Manages authentication and session lifecycle
- Implements cookie-based session management (required for Odoo 18)
- Provides field-whitelisted data access methods
- Handles automatic session re-authentication on expiration
- Abstracts low-level HTTP and JSON-RPC details

**Why It Exists**: This abstraction layer ensures that all Odoo interactions follow the same patterns, use consistent error handling, and maintain sessions correctly. It eliminates code duplication and provides a single point of maintenance for API communication logic.

**Key Features**:
- **Strict Field Control**: All read operations require explicit field whitelists, preventing accidental over-fetching
- **Session Management**: Automatic cookie handling and session persistence
- **Error Recovery**: Automatic re-authentication on session expiration
- **Type Safety**: Clear method signatures with required parameters

**Methods Provided**:
- `authenticate()`: Establishes authenticated session with Odoo
- `read_record()`: Fetches single record with whitelisted fields only
- `search_read()`: Searches and reads multiple records with whitelisted fields
- `read_all_records()`: Fetches all records matching criteria with whitelisted fields
- `read_record_all_fields()`: Convenience method for fetching all fields (testing scenarios)
- `write_record()`: Updates a single record
- `call_kw()`: Generic method caller for custom Odoo model methods

---

### `fetch_data.py`

**Purpose**: Data extraction script for stock picking operations.

**Responsibilities**:
- Fetches stock.picking records with only whitelisted fields
- Retrieves related stock.move records linked to the picking
- Constructs clean, structured JSON output
- Saves data to local JSON files for later use
- Validates data structure and completeness

**Why It Exists**: This script serves as the primary data extraction layer, enabling external systems to obtain structured snapshots of Odoo stock picking data. The whitelist approach ensures minimal data transfer and clear data contracts.

**Data Flow**:
1. Authenticates with Odoo using the unified client
2. Fetches stock.picking record with 14 whitelisted fields
3. Extracts move IDs from `move_ids_without_package` field
4. Fetches related stock.move records with 9 whitelisted fields
5. Constructs hierarchical JSON structure
6. Serializes and saves to `stock_picking_<id>.json`

**Output Structure**:
- Clean JSON with only specified fields
- Hierarchical structure: picking → moves
- Ready for consumption by external systems or update operations

**Field Whitelists**:
- **Stock Picking**: 14 fields including id, name, origin, state, locations, partner, sale order, and status
- **Stock Move**: 9 fields including id, product, quantities, UOM, and template references

---

### `fetch_status.py`

**Purpose**: Reference data extraction for auxiliary Odoo models.

**Responsibilities**:
- Fetches salla.order.status records (or other reference models)
- Applies strict field whitelisting
- Generates clean JSON reference datasets
- Provides lookup data for mapping and validation

**Why It Exists**: Reference data such as order statuses, product categories, or custom status definitions are often needed for data mapping, validation, and business logic. This script provides a clean way to extract and maintain such reference datasets.

**Use Cases**:
- Status code mapping between external systems and Odoo
- Validation of status transitions
- Building dropdown lists or selection interfaces
- Data migration reference tables

**Output**: `salla_order_status_all.json` containing all status records with only essential fields (id, salla_status_id, name, type, slug).

---

### `update_picking_status.py`

**Purpose**: Specialized script for updating stock.picking status fields.

**Responsibilities**:
- Updates stock.picking records with status-related fields
- Specifically designed for order status and delivery information updates
- Provides focused functionality for status management workflows
- Includes verification logic to confirm updates were applied correctly

**Why It Exists**: While `update_data.py` handles general updates for multiple models, this script provides a dedicated, focused solution for stock.picking status updates. It simplifies the workflow when only status updates are needed, reducing complexity and improving maintainability.

**Key Features**:
- **Status-Focused**: Designed specifically for updating status-related fields (e.g., `salla_order_status_id`, `x_studio_delivered`)
- **Batch Updates**: Updates multiple picking records in a single operation
- **Verification**: Automatically verifies that updates were applied correctly
- **Clear Reporting**: Provides detailed success/failure reporting for each update

**Configuration**:
- Uses `STOCK_PICKING_UPDATE_FIELDS` from `config.py` for field values
- Uses `STOCK_PICKING_IDS` from `config.py` for record selection
- Supports updating multiple pickings with the same field values

**Workflow**:
1. Authenticates with Odoo
2. Reads configuration from `config.py`
3. Updates all specified picking records in a single batch operation
4. Verifies each update by reading back the records
5. Reports success/failure for each record

**Use Cases**:
- Updating order status from external order management systems
- Marking deliveries as completed
- Synchronizing status changes between systems
- Bulk status updates during order processing workflows

---

### `update_data.py`

**Purpose**: Unified update orchestration for multiple Odoo models.

**Responsibilities**:
- Updates stock.move records in bulk operations
- Updates stock.picking records with field modifications
- Handles field mapping and normalization (e.g., quantity → product_uom_qty)
- Groups updates efficiently to minimize API calls
- Provides comprehensive update reporting

**Why It Exists**: This script consolidates update operations for multiple models, enabling efficient batch processing and consistent update patterns. It handles the complexity of field mappings and business rule validations.

**Update Capabilities**:

1. **Stock Move Bulk Updates**:
   - Updates multiple stock.move records simultaneously
   - Automatic field mapping (quantity → product_uom_qty)
   - Groups records with identical update values for efficiency

2. **Stock Picking Updates**:
   - Updates status fields and custom fields
   - Handles Many2one field relationships correctly
   - Supports multiple picking records in a single operation

**Configuration-Driven**: All update operations are defined in `config.py`, making it easy to modify update rules without code changes.

---

### `call_update_salla.py`

**Purpose**: Script for invoking custom Odoo model methods via JSON-RPC API.

**Responsibilities**:
- Calls custom `@api.model` methods in Odoo models
- Specifically designed to invoke `update_salla` method in `stock.picking` model
- Provides flexible command-line interface for method invocation
- Handles method call errors and provides detailed reporting
- Demonstrates pattern for calling any custom Odoo model method

**Why It Exists**: Odoo customizations often include custom model methods that encapsulate business logic. This script provides a clean, reusable pattern for invoking such methods from external systems via JSON-RPC, enabling integration with custom Odoo workflows and business processes.

**Key Features**:
- **Custom Method Invocation**: Calls `@api.model` decorated methods directly on models
- **Flexible Input**: Supports picking ID from configuration or command-line argument
- **Error Handling**: Comprehensive error handling with detailed error messages
- **Reusable Pattern**: Demonstrates how to call any custom Odoo method via JSON-RPC

**Method Signature**:
The script calls the `update_salla` method in `stock.picking` model:
```python
@api.model
def update_salla(self, picking_id):
    # Custom business logic
```

**Usage**:
- **From Config**: Uses `PICKING_ID` from `config.py` by default
- **Command Line**: Accepts picking ID as command-line argument
  ```bash
  python3 call_update_salla.py 108080
  ```

**Workflow**:
1. Authenticates with Odoo using the unified client
2. Calls `update_salla` method on `stock.picking` model via `call_kw()`
3. Passes picking ID as method argument
4. Returns and displays method execution result
5. Reports success or failure with detailed information

**Use Cases**:
- Triggering custom business logic workflows from external systems
- Invoking automated processing methods for order fulfillment
- Calling custom validation or synchronization methods
- Integrating with custom Odoo modules and workflows
- Automating complex business processes via API

**Extension Pattern**:
This script serves as a template for calling any custom Odoo method:
1. Replace `update_salla` with target method name
2. Adjust method arguments as needed
3. Update model name if calling different model
4. Modify error handling for method-specific requirements

---

### `stock_picking_<id>.json`

**Purpose**: Generated data snapshot file representing a complete stock picking record.

**Structure**: Hierarchical JSON containing:
- Stock picking record with 14 whitelisted fields
- Array of related stock.move records, each with 9 whitelisted fields
- Move IDs array for reference

**Usage Scenarios**:
- **Data Replay**: Load JSON and update Odoo records with modified values
- **Data Export**: Transfer Odoo data to external systems
- **Audit Trail**: Maintain snapshots of picking states at specific points in time
- **Testing**: Use as test fixtures for integration testing

**Lifecycle**: Generated by `fetch_data.py`, consumed by `update_data.py` or external systems.

---

### `salla_order_status_all.json`

**Purpose**: Reference dataset containing all order status definitions.

**Structure**: Flat array of status records, each containing:
- id, salla_status_id, name, type, slug

**Usage Scenarios**:
- Status code mapping between systems
- Validation of status transitions
- Building user interfaces with status options
- Data migration reference

**Lifecycle**: Generated by `fetch_status.py`, typically updated less frequently than operational data.

## Data Flow Diagram (Conceptual)

### Fetching Data Flow

```
1. Script Execution
   └─> fetch_data.py or fetch_status.py starts

2. Authentication
   └─> odoo_jsonrpc_client.py
       └─> POST /web/session/authenticate
           └─> Receives session cookies
               └─> Stores cookies in CookieJar

3. Data Retrieval
   └─> Client calls read_record() or search_read()
       └─> POST /web/dataset/call_kw
           └─> Odoo executes model.read() or model.search_read()
               └─> Returns only whitelisted fields

4. Data Processing
   └─> Script structures data hierarchically
       └─> Validates field presence
           └─> Builds JSON structure

5. Persistence
   └─> Serializes to JSON file
       └─> Saves to disk (stock_picking_<id>.json or salla_order_status_all.json)
```

### Update Data Flow

```
1. Script Execution
   └─> update_data.py or update_picking_status.py starts

2. Configuration Loading
   └─> Reads BULK_UPDATE_RECORDS and STOCK_PICKING_UPDATE_FIELDS from config.py

3. Field Normalization
   └─> normalize_updates() processes field mappings
       └─> Maps quantity → product_uom_qty for stock.move

4. Batch Grouping
   └─> Groups records with identical update values
       └─> Minimizes API calls

5. Authentication
   └─> odoo_jsonrpc_client.py authenticates

6. Update Execution
   └─> Client calls call_kw() with write() method
       └─> POST /web/dataset/call_kw
           └─> Odoo executes model.write()
               └─> Updates records in database

7. Result Reporting
   └─> Script reports success/failure counts
       └─> Displays detailed error messages if any
```

## Design Principles

### 1. Separation of Concerns

Each module has a single, well-defined responsibility:
- **Client Layer**: Handles all JSON-RPC communication
- **Configuration Layer**: Centralizes all settings
- **Script Layer**: Orchestrates business logic
- **Data Layer**: JSON files serve as data contracts

### 2. API-First Approach

The entire suite operates through Odoo's JSON-RPC API, never accessing the database directly. This ensures:
- Compatibility with Odoo's security model
- Respect for access rights and record rules
- Portability across different Odoo deployments
- No database schema dependencies

### 3. Minimal Data Fetching

Field whitelisting ensures that only necessary data is transferred:
- Reduces network payload
- Improves performance
- Minimizes exposure of sensitive fields
- Creates clear data contracts

### 4. Reusability

The unified client (`odoo_jsonrpc_client.py`) can be imported and used by any Python script:
- Consistent API interaction patterns
- Shared session management
- Unified error handling
- Single point of maintenance

### 5. Testability

The architecture supports testing at multiple levels:
- Unit tests can mock the JSON-RPC client
- Integration tests can use real Odoo instances
- JSON files serve as test fixtures
- Configuration can be overridden for test environments

### 6. Configuration-Driven Operations

Update operations and data extraction rules are defined in configuration, not code:
- Easy to modify without code changes
- Supports multiple environments (dev, staging, production)
- Enables non-developers to configure operations
- Facilitates deployment automation

## How to Extend This Project

### Adding New Models

To fetch data from a new Odoo model:

1. **Define Field Whitelist**:
   ```python
   NEW_MODEL_WHITELIST = ["id", "field1", "field2", ...]
   ```

2. **Create Fetch Script**:
   - Import `OdooJSONRPCClient` from `odoo_jsonrpc_client.py`
   - Use `read_record()` or `search_read()` with whitelist
   - Structure and save JSON output

3. **Follow Existing Patterns**:
   - Use the same authentication flow
   - Apply field whitelisting
   - Save to descriptive JSON filenames

### Adding New Fields

To include additional fields in existing operations:

1. **Update Whitelist**:
   - Add field name to appropriate whitelist constant
   - Ensure field exists in Odoo model

2. **Update JSON Structure**:
   - Add field extraction in data building logic
   - Update JSON output structure

3. **Test**:
   - Verify field is returned by Odoo
   - Confirm JSON structure is correct

### Adding New Update Logic

To support updates for new models:

1. **Extend `update_data.py`**:
   - Add new update function following existing patterns
   - Implement field normalization if needed
   - Add configuration section in `config.py`

2. **Define Configuration**:
   - Add update records list or field mappings
   - Specify model name and update values

3. **Implement Batch Logic**:
   - Group updates efficiently
   - Handle field mappings
   - Provide error reporting

### Reusing the JSON-RPC Client

The unified client can be imported in any Python script:

```python
from odoo_jsonrpc_client import OdooJSONRPCClient
from config import ODOO_URL, DB_NAME, USERNAME, PASSWORD

# Initialize and authenticate
client = OdooJSONRPCClient(ODOO_URL, DB_NAME, USERNAME, PASSWORD)
client.authenticate()

# Use client methods
record = client.read_record("model.name", record_id, ["field1", "field2"])
records = client.search_read("model.name", domain, ["field1", "field2"])
client.write_record("model.name", record_id, {"field": "value"})

# Call custom model methods
result = client.call_kw("model.name", "custom_method", [arg1, arg2], {})
```

### Calling Custom Odoo Methods

To call custom `@api.model` methods in Odoo:

1. **Use `call_kw()` Method**:
   ```python
   result = client.call_kw(
       model="stock.picking",
       method="update_salla",
       args=[picking_id],
       kwargs={}
   )
   ```

2. **Follow the Pattern**:
   - Model name: The Odoo model containing the method
   - Method name: The method to call
   - Args: List of positional arguments
   - Kwargs: Dictionary of keyword arguments

3. **See `call_update_salla.py`** for a complete example of calling custom methods.

### Best Practices for Extension

- **Always Use Whitelists**: Never fetch all fields; define explicit whitelists
- **Handle Errors Gracefully**: Implement try-except blocks and meaningful error messages
- **Validate Data**: Check for required fields before processing
- **Document Changes**: Update this README when adding new functionality
- **Test Thoroughly**: Verify new functionality with real Odoo instances
- **Follow Naming Conventions**: Use descriptive names for scripts and configuration variables

## Configuration

All configuration is centralized in `config.py`. Key sections include:

- **Odoo Connection**: URL, database name, credentials
- **Record Identifiers**: Picking IDs and test record references
- **Update Specifications**: Bulk update records and field mappings
- **Field Whitelists**: Defined in individual scripts for clarity

## Requirements

- Python 3.8+
- Odoo 18 instance with JSON-RPC API enabled
- Network access to Odoo server
- Valid Odoo user credentials with appropriate access rights

## Usage Examples

### Fetch Stock Picking Data

```bash
python3 fetch_data.py
```

Output: `stock_picking_108080.json` containing picking and moves data.

### Fetch Order Statuses

```bash
python3 fetch_status.py
```

Output: `salla_order_status_all.json` containing all status records.

### Update Records

```bash
python3 update_data.py

### Update Stock Picking Status

Update stock.picking records with status-related fields:

```bash
python3 update_picking_status.py
```

Updates both stock.move and stock.picking records as configured in `config.py`.

### Call Custom Model Method

Call the `update_salla` method in `stock.picking` model:

```bash
# Using default picking ID from config.py
python3 call_update_salla.py

# Or specify picking ID as argument
python3 call_update_salla.py 108080
```

Invokes the custom `update_salla` method for the specified picking record.

## Author

**Rightechs Solutions**

Professional Odoo development and customization services.

Website: https://www.rightechs.net/

---

## License

This project is proprietary software developed by Rightechs Solutions for enterprise integration purposes.
