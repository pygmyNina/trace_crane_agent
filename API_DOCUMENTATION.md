# TRACE API Documentation

**For PWA Frontend Development**

## Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Start API Server
```bash
python3 api.py
```

Server runs at: `http://localhost:8000`

API Documentation (auto-generated): `http://localhost:8000/docs`

### 3. Test Endpoints
```bash
# Health check
curl http://localhost:8000/api/health

# Get all parts
curl http://localhost:8000/api/parts

# Search for transformer
curl http://localhost:8000/api/parts/search?q=transformer
```

---

## Base URL

**Development:** `http://localhost:8000`
**Production:** TBD

---

## API Endpoints Reference

### Health & Info

#### `GET /`
Root endpoint - health check
```json
{
  "name": "TRACE API",
  "version": "0.3.0",
  "status": "operational"
}
```

#### `GET /api/health`
Detailed health status
```json
{
  "status": "healthy",
  "services": {
    "parts_manager": "ready",
    "search": "ready",
    "validator": "ready"
  }
}
```

---

## Parts Endpoints

### `GET /api/parts`
Get all parts in a section

**Query Parameters:**
- `section` (optional) - Section to query (default: "electrical")
- `limit` (optional) - Limit number of results

**Example:**
```bash
GET /api/parts?section=electrical&limit=50
```

**Response:**
```json
[
  {
    "symbol": "-TR1",
    "quantity": "1",
    "description": "transformer 480/120V AC, 5000VA",
    "identification": "MT5000A Siemens",
    "sheet_section": "=11/16.2",
    "location": "+E13",
    "remarks": "",
    "source_section": "electrical",
    "source_pdf": "11_parts.pdf"
  }
]
```

---

### `GET /api/parts/{symbol}`
Get specific part by symbol

**Path Parameters:**
- `symbol` - Component symbol (e.g., -TR1, -CB1)

**Example:**
```bash
GET /api/parts/-TR1
```

**Response:**
```json
{
  "symbol": "-TR1",
  "quantity": "1",
  "description": "transformator 3000VA 480/230V",
  "identification": "TA83223 ACME",
  "sheet_section": "=11/7.7",
  "location": "+E11",
  "remarks": "",
  "source_section": "electrical",
  "source_pdf": "11_parts.pdf"
}
```

**Error Response (404):**
```json
{
  "detail": "Part -TR99 not found"
}
```

---

### `GET /api/parts/search`
Search parts with multiple filters

**Query Parameters:**
- `q` (optional) - Search in description/manufacturer
- `symbol` (optional) - Exact symbol match
- `sheet` (optional) - Sheet reference (can be partial)
- `location` (optional) - Location code
- `section` (optional) - Section to search (default: "electrical")

**Examples:**
```bash
# Search by description
GET /api/parts/search?q=transformer

# Find by exact symbol
GET /api/parts/search?symbol=-TR1

# Find all parts on a sheet
GET /api/parts/search?sheet==11/7.7

# Find all parts at a location
GET /api/parts/search?location=+E11

# Combined filters
GET /api/parts/search?q=breaker&location=+E11
```

**Response:** Array of matching parts (same format as GET /api/parts)

---

### `GET /api/parts/stats`
Get parts statistics

**Query Parameters:**
- `section` (optional) - Section to analyze (default: "electrical")

**Example:**
```bash
GET /api/parts/stats?section=electrical
```

**Response:**
```json
{
  "total_parts": 274,
  "unique_symbols": 264,
  "unique_sheets": 45,
  "unique_locations": 28,
  "section": "electrical"
}
```

---

### `GET /api/parts/by-sheet/{sheet_ref}`
Get all parts on a specific sheet

**Path Parameters:**
- `sheet_ref` - Sheet reference (e.g., =11/7.7)

**Query Parameters:**
- `section` (optional) - Section (default: "electrical")

**Example:**
```bash
GET /api/parts/by-sheet/=11/7.7
```

**Response:** Array of parts on that sheet

---

### `GET /api/parts/by-location/{location}`
Get all parts at a specific location

**Path Parameters:**
- `location` - Location code (e.g., +E11, +GDW)

**Query Parameters:**
- `section` (optional) - Section (default: "electrical")

**Example:**
```bash
GET /api/parts/by-location/+E11
```

**Response:** Array of parts at that location

---

## Schematic/Sheet Endpoints

### `GET /api/sheets/search`
Search schematic index

**Query Parameters:**
- `q` (required) - Search query
- `section` (optional) - Limit to section

**Example:**
```bash
GET /api/sheets/search?q=transformer&section=electrical
```

**Response:**
```json
[
  {
    "section": "electrical",
    "pdf": "11.pdf",
    "page": 16,
    "sheet_number": "16",
    "system_group": "=11",
    "location": "+E13",
    "summary": "Transformer and power distribution schematic...",
    "matches": [
      "Component: -TR20 transformer",
      "Component: -TR30 transformer"
    ],
    "references": ["=11/16.2", "=11/16.3"],
    "components": ["-TR20", "-TR30", "-MSP19"],
    "connections": ["TR20 supplies 120V AC to panel"]
  }
]
```

---

### `GET /api/sheets/{sheet_number}`
Find specific sheet by number

**Path Parameters:**
- `sheet_number` - Sheet number to find

**Query Parameters:**
- `section` (optional) - Limit to section

**Example:**
```bash
GET /api/sheets/102
```

**Response:**
```json
{
  "section": "electrical",
  "pdf": "10.pdf",
  "page": 2,
  "sheet_number": "102",
  "system_group": "=10",
  "location": "+HVC1",
  "summary": "Main circuit breaker schematic",
  "references": ["=10/102.2", "=10/102.5"],
  "components": ["-CB1", "-TR1"],
  "connections": ["CB1 feeds main transformer TR1"],
  "terminals": ["1U", "2V", "3W"],
  "wire_numbers": ["W1234", "W5678"]
}
```

---

### `GET /api/sheets/by-system/{system_code}`
Get all sheets for a system group

**Path Parameters:**
- `system_code` - System group code (e.g., =11, =10)

**Example:**
```bash
GET /api/sheets/by-system/=11
```

**Response:** Array of sheets in that system

---

### `GET /api/sheets/by-location/{location_code}`
Get all sheets at a location

**Path Parameters:**
- `location_code` - Location code (e.g., +E11)

**Example:**
```bash
GET /api/sheets/by-location/+E11
```

**Response:** Array of sheets at that location

---

### `GET /api/systems`
List all system groups with sheet counts

**Example:**
```bash
GET /api/systems
```

**Response:**
```json
[
  {
    "code": "=10",
    "name": "MV-Supply",
    "sheet_count": 3,
    "sheets": ["101", "102", "103"]
  },
  {
    "code": "=11",
    "name": "Feeding",
    "sheet_count": 61,
    "sheets": ["1", "2", "3", ...]
  }
]
```

---

## Validation Endpoints

### `GET /api/validate/{section_code}`
Validate parts vs schematics for a section

**Path Parameters:**
- `section_code` - Section code (e.g., "10", "11")

**Example:**
```bash
GET /api/validate/11
```

**Response:**
```json
{
  "success": true,
  "section": "11",
  "stats": {
    "total_parts": 264,
    "found_on_sheet": 250,
    "missing_from_sheet": 5,
    "sheet_not_indexed": 9,
    "has_connections": 45
  },
  "results": [
    {
      "symbol": "-TR1",
      "sheet_ref": "=11/7.7",
      "location": "+E11",
      "description": "transformator 3000VA 480/230V",
      "status": "found_with_connections",
      "connections": ["TR1 supplies power to panel"],
      "sheet_summary": "Power distribution schematic..."
    }
  ]
}
```

---

### `GET /api/validate`
Validate all sections

**Example:**
```bash
GET /api/validate
```

**Response:**
```json
{
  "success": true,
  "sections": {
    "10": { /* validation results */ },
    "11": { /* validation results */ }
  },
  "total_stats": {
    "total_parts": 274,
    "found_on_sheet": 260,
    "missing_from_sheet": 5,
    "sheet_not_indexed": 9,
    "has_connections": 50
  }
}
```

---

## PWA Use Cases

### 1. Component Lookup (Hands-Free)
```javascript
// Voice: "Find transformer TR1"
const response = await fetch(`/api/parts/-TR1`);
const part = await response.json();
// Show: Location, sheet, description
```

### 2. Location-Based Parts List
```javascript
// User at cabinet E11, wants to see all parts there
const response = await fetch(`/api/parts/by-location/+E11`);
const parts = await response.json();
// Display list of all components in that cabinet
```

### 3. Sheet Quick Reference
```javascript
// Voice: "Show me sheet 102"
const response = await fetch(`/api/sheets/102`);
const sheet = await response.json();
// Show: PDF page, components, connections
```

### 4. Search While Troubleshooting
```javascript
// Voice: "Find all circuit breakers"
const response = await fetch(`/api/parts/search?q=breaker`);
const breakers = await response.json();
// Show results, filter by location
```

---

## Error Handling

All endpoints return standard HTTP status codes:

- `200 OK` - Success
- `404 Not Found` - Resource not found
- `500 Internal Server Error` - Server error

Error response format:
```json
{
  "detail": "Error description here"
}
```

---

## CORS Configuration

CORS is enabled for all origins in development. Configure for production:

```python
# In api.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-pwa-domain.com"],  # Update this
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## Interactive API Documentation

FastAPI automatically generates interactive docs:

- **Swagger UI:** `http://localhost:8000/docs`
- **ReDoc:** `http://localhost:8000/redoc`

Use these to test endpoints directly in your browser!

---

## Next Steps

1. **Nina:** Start PWA development using these endpoints
2. **Joseph:** Continue CLI features while I add API endpoints in parallel
3. **Both:** Sync via GitHub - core logic is shared!

---

## Contact

Questions? Sync via GitHub issues or update this doc with questions!
