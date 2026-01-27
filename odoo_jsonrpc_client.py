"""
Unified Odoo 18 JSON-RPC Client for all test scripts.

This module provides a single, consistent JSON-RPC client that all
test scripts and utilities can use. It enforces field whitelisting
to ensure only specified fields are fetched.

Author: Rightechs Solutions
"""

import json
from typing import Dict, List, Any, Optional
from urllib.request import Request, build_opener, HTTPCookieProcessor
from urllib.error import URLError, HTTPError
from http.cookiejar import CookieJar


class OdooJSONRPCClient:
    """
    Professional JSON-RPC client for Odoo 18 API interactions.
    
    This class handles all low-level JSON-RPC communication including
    authentication, session management, and model method calls with
    strict field control (whitelist only).
    """
    
    def __init__(self, url: str, db: str, username: str, password: str):
        """
        Initialize the JSON-RPC client with connection parameters.
        
        Args:
            url: Odoo server URL (e.g., http://localhost:8018)
            db: Database name
            username: Odoo username
            password: Odoo password
        """
        self.url = url.rstrip('/')
        self.db = db
        self.username = username
        self.password = password
        self.session_id = None
        self.uid = None
        
        # Initialize cookie jar for session management
        # Odoo 18 requires cookies to maintain session between requests
        self.cookie_jar = CookieJar()
        self.opener = build_opener(HTTPCookieProcessor(self.cookie_jar))
    
    def _make_request(self, endpoint: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Make a JSON-RPC request to the specified endpoint.
        
        This method uses cookie-based session management which is required
        for Odoo 18 JSON-RPC API to maintain authentication between requests.
        
        Args:
            endpoint: API endpoint path
            params: JSON-RPC parameters
            
        Returns:
            Response data as dictionary
            
        Raises:
            URLError: If connection fails
            HTTPError: If HTTP error occurs
            ValueError: If response contains error
        """
        url = f"{self.url}{endpoint}"
        payload = {
            "jsonrpc": "2.0",
            "method": "call",
            "params": params,
            "id": 1
        }
        
        data = json.dumps(payload).encode('utf-8')
        request = Request(
            url,
            data=data,
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
        )
        
        try:
            # Use opener with cookie handler to maintain session
            response = self.opener.open(request, timeout=30)
            result = json.loads(response.read().decode('utf-8'))
            
            # Check for JSON-RPC errors
            if 'error' in result:
                error_data = result['error']
                error_msg = error_data.get('message', 'Unknown error')
                error_debug = error_data.get('data', {})
                
                # If session expired, try to re-authenticate automatically
                if 'Session expired' in error_msg or 'Session expired' in str(error_debug):
                    if self.authenticate():
                        # Retry the request after re-authentication
                        response = self.opener.open(request, timeout=30)
                        result = json.loads(response.read().decode('utf-8'))
                        if 'error' in result:
                            error_data = result['error']
                            raise ValueError(
                                f"JSON-RPC Error after re-auth: {error_data.get('message', 'Unknown error')} - "
                                f"{error_data.get('data', {})}"
                            )
                    else:
                        raise ValueError(f"JSON-RPC Error: {error_msg} - Failed to re-authenticate")
                else:
                    raise ValueError(f"JSON-RPC Error: {error_msg} - {error_debug}")
            
            return result.get('result', {})
        except HTTPError as e:
            error_body = e.read().decode('utf-8') if hasattr(e, 'read') else ''
            raise HTTPError(e.url, e.code, f"HTTP Error: {e.reason} - {error_body}", e.headers, e.fp)
        except URLError as e:
            raise URLError(f"Connection Error: {e.reason}")
    
    def authenticate(self) -> bool:
        """
        Authenticate with Odoo and establish a session.
        
        Returns:
            True if authentication successful, False otherwise
            
        Raises:
            ValueError: If authentication fails
        """
        params = {
            "db": self.db,
            "login": self.username,
            "password": self.password
        }
        
        result = self._make_request("/web/session/authenticate", params)
        
        # Extract session information
        if result and 'uid' in result:
            self.uid = result['uid']
            self.session_id = result.get('session_id')
            return True
        
        raise ValueError("Authentication failed: No UID returned")
    
    def call_kw(self, model: str, method: str, args: List, kwargs: Dict[str, Any]) -> Any:
        """
        Call a model method using call_kw endpoint.
        
        In Odoo 18, session is maintained via cookies, not through context.
        The cookie jar automatically handles session cookies.
        
        Args:
            model: Model name (e.g., 'stock.picking')
            method: Method name (e.g., 'read', 'write', 'search')
            args: Positional arguments
            kwargs: Keyword arguments
            
        Returns:
            Method result
        """
        if not self.uid:
            raise ValueError("Not authenticated. Call authenticate() first.")
        
        params = {
            "model": model,
            "method": method,
            "args": args,
            "kwargs": kwargs,
            "context": {}
        }
        
        result = self._make_request("/web/dataset/call_kw", params)
        return result
    
    def read_record(self, model: str, record_id: int, fields: List[str]) -> Dict[str, Any]:
        """
        Read a single record with ONLY specified fields (whitelist required).
        
        Args:
            model: Model name
            record_id: Record ID
            fields: List of field names to read (REQUIRED - no default)
            
        Returns:
            Record data as dictionary with only whitelisted fields
        """
        if not fields:
            raise ValueError("Fields list is required. No default fields will be fetched.")
        
        result = self.call_kw(model, "read", [[record_id]], {"fields": fields})
        
        if result and len(result) > 0:
            return result[0]
        
        raise ValueError(f"Record {record_id} not found in model {model}")
    
    def search_read(self, model: str, domain: List, fields: List[str]) -> List[Dict[str, Any]]:
        """
        Search and read records matching the domain with ONLY specified fields (whitelist required).
        
        Args:
            model: Model name
            domain: Search domain (e.g., [('id', 'in', [1, 2, 3])])
            fields: List of field names to read (REQUIRED - no default)
            
        Returns:
            List of record dictionaries with only whitelisted fields
        """
        if not fields:
            raise ValueError("Fields list is required. No default fields will be fetched.")
        
        result = self.call_kw(model, "search_read", [domain], {"fields": fields})
        return result if result else []
    
    def get_fields(self, model: str) -> Dict[str, Any]:
        """
        Get all field definitions for a model.
        
        This method dynamically retrieves all available fields, which ensures
        compatibility with Odoo 18 field name changes.
        
        Args:
            model: Model name
            
        Returns:
            Dictionary of field definitions
        """
        return self.call_kw(model, "fields_get", [], {})
    
    def read_all_records(self, model: str, fields: List[str], domain: Optional[List] = None) -> List[Dict[str, Any]]:
        """
        Read all records from a model with ONLY specified fields (whitelist required).
        
        This method searches for all records matching the domain (or all records
        if no domain is provided) and reads them with ONLY the specified fields.
        
        Args:
            model: Model name (e.g., 'salla.order.status')
            fields: List of field names to read (REQUIRED - whitelist only)
            domain: Search domain (None = all records)
            
        Returns:
            List of record dictionaries with only whitelisted fields
        """
        if not fields:
            raise ValueError("Fields list is required. No default fields will be fetched.")
        
        # If no domain provided, get all records
        if domain is None:
            domain = []
        
        # Use search_read to get all records with ONLY whitelisted fields
        result = self.call_kw(model, "search_read", [domain], {"fields": fields})
        return result if result else []
    
    def read_record_all_fields(self, model: str, record_id: int) -> Dict[str, Any]:
        """
        Read a single record with ALL available fields.
        
        This is a convenience method for tests that need all fields.
        For production use, prefer read_record() with explicit field whitelist.
        
        Args:
            model: Model name
            record_id: Record ID
            
        Returns:
            Record data as dictionary with all fields
        """
        # Get all fields dynamically
        fields_info = self.get_fields(model)
        fields = list(fields_info.keys())
        
        return self.read_record(model, record_id, fields)
    
    def search_read_all_fields(self, model: str, domain: List) -> List[Dict[str, Any]]:
        """
        Search and read records matching the domain with ALL available fields.
        
        This is a convenience method for tests that need all fields.
        For production use, prefer search_read() with explicit field whitelist.
        
        Args:
            model: Model name
            domain: Search domain (e.g., [('picking_id', '=', 1)])
            
        Returns:
            List of record dictionaries with all fields
        """
        # Get all fields dynamically
        fields_info = self.get_fields(model)
        fields = list(fields_info.keys())
        
        return self.search_read(model, domain, fields)
    
    def write_record(self, model: str, record_id: int, values: Dict[str, Any]) -> bool:
        """
        Update a record with new values.
        
        Args:
            model: Model name
            record_id: Record ID
            values: Dictionary of field:value pairs to update
            
        Returns:
            True if update successful
        """
        result = self.call_kw(model, "write", [[record_id], values], {})
        return result is True
