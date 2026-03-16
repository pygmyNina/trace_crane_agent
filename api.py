#!/usr/bin/env python3
"""
TRACE API - FastAPI wrapper for crane electrical system documentation
RESTful API for PWA frontend consumption
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Any, Optional
import uvicorn

from core.parts_manager import PartsManager
from core.search import SchematicSearch
from core.validator import PartsValidator

# Initialize FastAPI app
app = FastAPI(
    title="TRACE API",
    description="Crane Electrical System Documentation API",
    version="0.3.0"
)

# Enable CORS for PWA
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize core modules
parts_mgr = PartsManager()
search = SchematicSearch()
validator = PartsValidator()


# ========================================
# Health & Info Endpoints
# ========================================

@app.get("/")
async def root():
    """API root - health check"""
    return {
        "name": "TRACE API",
        "version": "0.3.0",
        "status": "operational"
    }

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "services": {
            "parts_manager": "ready",
            "search": "ready",
            "validator": "ready"
        }
    }


# ========================================
# Parts Endpoints
# ========================================

@app.get("/api/parts")
async def list_parts(
    section: str = Query("electrical", description="Section to query"),
    limit: Optional[int] = Query(None, description="Limit results")
) -> List[Dict[str, Any]]:
    """
    Get all parts in a section

    Example: GET /api/parts?section=electrical&limit=50
    """
    parts = parts_mgr.get_all_parts(section=section)

    if limit:
        parts = parts[:limit]

    return parts


@app.get("/api/parts/search")
async def search_parts(
    q: Optional[str] = Query(None, description="Search query (description/manufacturer)"),
    symbol: Optional[str] = Query(None, description="Exact symbol match"),
    sheet: Optional[str] = Query(None, description="Sheet reference"),
    location: Optional[str] = Query(None, description="Location code"),
    section: str = Query("electrical", description="Section to search")
) -> List[Dict[str, Any]]:
    """
    Search parts with multiple filters

    Examples:
    - GET /api/parts/search?q=transformer
    - GET /api/parts/search?symbol=-TR1
    - GET /api/parts/search?sheet==11/7.7
    - GET /api/parts/search?location=+E11
    """
    results = parts_mgr.search_parts(
        query=q,
        symbol=symbol,
        sheet=sheet,
        location=location,
        section=section
    )

    return results


@app.get("/api/parts/stats")
async def get_parts_stats(section: str = Query("electrical")) -> Dict[str, Any]:
    """
    Get parts statistics

    Example: GET /api/parts/stats?section=electrical
    """
    return parts_mgr.get_parts_stats(section=section)


@app.get("/api/parts/by-sheet/{sheet_ref}")
async def get_parts_by_sheet(
    sheet_ref: str,
    section: str = Query("electrical")
) -> List[Dict[str, Any]]:
    """
    Get all parts on a specific sheet

    Example: GET /api/parts/by-sheet/=11/7.7
    """
    parts = parts_mgr.get_parts_by_sheet(sheet_ref, section=section)
    return parts


@app.get("/api/parts/by-location/{location}")
async def get_parts_by_location(
    location: str,
    section: str = Query("electrical")
) -> List[Dict[str, Any]]:
    """
    Get all parts at a specific location

    Example: GET /api/parts/by-location/+E11
    """
    parts = parts_mgr.get_parts_by_location(location, section=section)
    return parts


@app.get("/api/parts/structure")
async def get_parts_structure(
    section: str = Query("electrical")
) -> Dict[str, Any]:
    """
    Get complete parts structure analysis

    Identifies:
    - Assemblies: Multiple parts making one schematic component
    - Reused components: Same part used in multiple locations
    - Single components: Parts with one entry only

    Example: GET /api/parts/structure?section=electrical
    """
    return parts_mgr.get_parts_structure(section=section)


@app.get("/api/parts/assemblies")
async def list_assemblies(
    section: str = Query("electrical")
) -> List[Dict[str, Any]]:
    """
    Get all assemblies (multiple parts → one schematic component)

    Example: GET /api/parts/assemblies?section=electrical
    """
    return parts_mgr.get_assemblies(section=section)


@app.get("/api/parts/assemblies/{symbol}")
async def get_assembly(
    symbol: str,
    section: str = Query("electrical")
) -> Dict[str, Any]:
    """
    Get assembly details for a specific symbol

    Example: GET /api/parts/assemblies/-PB1?section=electrical
    """
    assembly = parts_mgr.get_assembly_by_symbol(symbol, section=section)

    if not assembly:
        raise HTTPException(
            status_code=404,
            detail=f"Assembly {symbol} not found (may be a single part or reused component)"
        )

    return assembly


@app.get("/api/parts/reused")
async def list_reused_components(
    section: str = Query("electrical")
) -> List[Dict[str, Any]]:
    """
    Get all reused components (same part in multiple locations)

    Example: GET /api/parts/reused?section=electrical
    """
    return parts_mgr.get_reused_components(section=section)


@app.get("/api/parts/{symbol}")
async def get_part(symbol: str) -> Dict[str, Any]:
    """
    Get specific part by symbol

    NOTE: This route must come AFTER all specific /api/parts/* routes
    to avoid matching path segments as symbols.

    Example: GET /api/parts/-TR1
    """
    part = parts_mgr.get_part_by_symbol(symbol)

    if not part:
        raise HTTPException(status_code=404, detail=f"Part {symbol} not found")

    return part


# ========================================
# Schematic/Sheet Endpoints
# ========================================

@app.get("/api/sheets/search")
async def search_sheets(
    q: str = Query(..., description="Search query"),
    section: Optional[str] = Query(None, description="Limit to section")
) -> List[Dict[str, Any]]:
    """
    Search schematic index

    Example: GET /api/sheets/search?q=transformer&section=electrical
    """
    results = search.search_schematics(query=q, section=section)
    return results


@app.get("/api/sheets/{sheet_number}")
async def get_sheet(
    sheet_number: str,
    section: Optional[str] = Query(None)
) -> Dict[str, Any]:
    """
    Find specific sheet by number

    Example: GET /api/sheets/102
    """
    sheet = search.find_sheet(sheet_number, section=section)

    if not sheet:
        raise HTTPException(status_code=404, detail=f"Sheet {sheet_number} not found")

    return sheet


@app.get("/api/sheets/by-system/{system_code}")
async def get_sheets_by_system(system_code: str) -> List[Dict[str, Any]]:
    """
    Get all sheets for a system group

    Example: GET /api/sheets/by-system/=11
    """
    sheets = search.get_sheets_by_system(system_code)
    return sheets


@app.get("/api/sheets/by-location/{location_code}")
async def get_sheets_by_location(location_code: str) -> List[Dict[str, Any]]:
    """
    Get all sheets at a location

    Example: GET /api/sheets/by-location/+E11
    """
    sheets = search.get_sheets_by_location(location_code)
    return sheets


@app.get("/api/systems")
async def list_systems() -> List[Dict[str, Any]]:
    """
    List all system groups

    Example: GET /api/systems
    """
    return search.list_systems()


# ========================================
# Validation Endpoints
# ========================================

@app.get("/api/validate/{section_code}")
async def validate_section(section_code: str) -> Dict[str, Any]:
    """
    Validate parts vs schematics for a section

    Example: GET /api/validate/11
    """
    result = validator.validate_section(section_code)

    if not result.get("success"):
        raise HTTPException(status_code=404, detail=result.get("error"))

    return result


@app.get("/api/validate")
async def validate_all() -> Dict[str, Any]:
    """
    Validate all sections

    Example: GET /api/validate
    """
    return validator.validate_all_sections()


# ========================================
# Run Server
# ========================================

if __name__ == "__main__":
    uvicorn.run(
        "api:app",
        host="0.0.0.0",
        port=8000,
        reload=True  # Auto-reload during development
    )
