"""
Parts Manager - Core business logic for parts operations
Shared by CLI and API interfaces
"""

import json
import os
from typing import List, Dict, Any, Optional
from collections import defaultdict


class PartsManager:
    """Manages parts list data and operations"""

    def __init__(self, registry_file: str = "schematic_registry.json"):
        self.registry_file = registry_file
        self.registry = self._load_registry()

    def _load_registry(self) -> Dict[str, Any]:
        """Load schematic registry from file"""
        if os.path.exists(self.registry_file):
            with open(self.registry_file, 'r') as f:
                return json.load(f)
        return {"sections": {}, "parts_lists": {}}

    def _save_registry(self):
        """Save registry to file"""
        with open(self.registry_file, 'w') as f:
            json.dump(self.registry, f, indent=2)

    def get_all_parts(self, section: str = "electrical") -> List[Dict[str, Any]]:
        """
        Get all parts from all parts lists in a section

        Args:
            section: Section name (default: electrical)

        Returns:
            List of all parts with metadata
        """
        all_parts = []

        if "parts_lists" not in self.registry:
            return all_parts

        if section not in self.registry["parts_lists"]:
            return all_parts

        for pdf_name, parts_info in self.registry["parts_lists"][section].items():
            if not parts_info.get("indexed"):
                continue

            for part in parts_info.get("parts", []):
                # Add source metadata
                part_copy = part.copy()
                part_copy["source_section"] = section
                part_copy["source_pdf"] = pdf_name
                all_parts.append(part_copy)

        return all_parts

    def get_part_by_symbol(self, symbol: str, section: str = "electrical") -> Optional[Dict[str, Any]]:
        """
        Get a specific part by its symbol (exact match)

        Args:
            symbol: Component symbol (e.g., -TR1, -CB1)
            section: Section to search in

        Returns:
            Part data or None if not found
        """
        parts = self.search_parts(symbol=symbol, section=section)
        return parts[0] if parts else None

    def search_parts(self, query: str = None, symbol: str = None,
                     sheet: str = None, location: str = None,
                     section: str = "electrical") -> List[Dict[str, Any]]:
        """
        Search parts with multiple filter options

        Args:
            query: Search in description or identification
            symbol: Exact component symbol match
            sheet: Sheet reference (can be partial, e.g., =10/ or =10/102.2)
            location: Location code
            section: Section to search in

        Returns:
            List of matching parts
        """
        results = []

        if "parts_lists" not in self.registry:
            return results

        if section not in self.registry["parts_lists"]:
            return results

        for pdf_name, parts_info in self.registry["parts_lists"][section].items():
            if not parts_info.get("indexed"):
                continue

            for part in parts_info.get("parts", []):
                match = True

                # Filter by query (description or identification)
                if query:
                    query_lower = query.lower()
                    desc_match = query_lower in part.get("description", "").lower()
                    ident_match = query_lower in part.get("identification", "").lower()
                    if not (desc_match or ident_match):
                        match = False

                # Filter by symbol (exact match)
                if symbol and symbol.lower() != part.get("symbol", "").lower():
                    match = False

                # Filter by sheet (can be partial match)
                if sheet and sheet.lower() not in part.get("sheet_section", "").lower():
                    match = False

                # Filter by location
                if location and location.lower() not in part.get("location", "").lower():
                    match = False

                if match:
                    result = part.copy()
                    result["source_section"] = section
                    result["source_pdf"] = pdf_name
                    results.append(result)

        return results

    def get_parts_by_sheet(self, sheet_ref: str, section: str = "electrical") -> List[Dict[str, Any]]:
        """
        Get all parts on a specific sheet

        Args:
            sheet_ref: Sheet reference (e.g., =10/102.2 or just =10/)
            section: Section to search in

        Returns:
            List of parts on that sheet
        """
        return self.search_parts(sheet=sheet_ref, section=section)

    def get_parts_by_location(self, location: str, section: str = "electrical") -> List[Dict[str, Any]]:
        """
        Get all parts at a specific location

        Args:
            location: Location code (e.g., +E11, +GDW)
            section: Section to search in

        Returns:
            List of parts at that location
        """
        return self.search_parts(location=location, section=section)

    def get_parts_stats(self, section: str = "electrical") -> Dict[str, Any]:
        """
        Get statistics about parts

        Args:
            section: Section to analyze

        Returns:
            Dictionary with statistics
        """
        all_parts = self.get_all_parts(section)

        # Count unique values
        symbols = set()
        sheets = set()
        locations = set()

        for part in all_parts:
            if part.get("symbol"):
                symbols.add(part["symbol"])
            if part.get("sheet_section"):
                sheets.add(part["sheet_section"])
            if part.get("location"):
                locations.add(part["location"])

        return {
            "total_parts": len(all_parts),
            "unique_symbols": len(symbols),
            "unique_sheets": len(sheets),
            "unique_locations": len(locations),
            "section": section
        }

    def update_part(self, symbol: str, updates: Dict[str, Any], section: str = "electrical") -> bool:
        """
        Update a part's data

        Args:
            symbol: Component symbol to update
            updates: Dictionary of fields to update
            section: Section containing the part

        Returns:
            True if updated, False if not found
        """
        if "parts_lists" not in self.registry:
            return False

        if section not in self.registry["parts_lists"]:
            return False

        updated = False

        for pdf_name, parts_info in self.registry["parts_lists"][section].items():
            for part in parts_info.get("parts", []):
                if part.get("symbol", "").lower() == symbol.lower():
                    # Update fields
                    for key, value in updates.items():
                        part[key] = value
                    updated = True

        if updated:
            self._save_registry()

        return updated

    def get_parts_structure(self, section: str = "electrical") -> Dict[str, Any]:
        """
        Analyze parts structure to identify assemblies vs reused components

        Args:
            section: Section to analyze

        Returns:
            Dictionary with:
            - assemblies: Components where multiple parts make one schematic symbol
            - reused_components: Same part used in multiple locations
            - single_components: Parts with only one entry
            - summary: Statistics
        """
        all_parts = self.get_all_parts(section)

        # Group parts by symbol
        by_symbol = defaultdict(list)
        for part in all_parts:
            symbol = part.get("symbol", "")
            if symbol:
                by_symbol[symbol].append(part)

        assemblies = []
        reused_components = []
        single_components = []

        for symbol, instances in by_symbol.items():
            if len(instances) == 1:
                # Single component
                single_components.append(instances[0])
            else:
                # Multiple instances - check if assembly or reused
                by_location_sheet = defaultdict(list)
                for inst in instances:
                    key = (inst.get("location", ""), inst.get("sheet_section", ""))
                    by_location_sheet[key].append(inst)

                if len(by_location_sheet) == 1:
                    # All parts at same location/sheet = ASSEMBLY
                    assemblies.append({
                        "symbol": symbol,
                        "location": instances[0].get("location", ""),
                        "sheet": instances[0].get("sheet_section", ""),
                        "part_count": len(instances),
                        "parts": instances
                    })
                else:
                    # Different locations = REUSED COMPONENT
                    locations_data = []
                    for (location, sheet), parts in by_location_sheet.items():
                        locations_data.append({
                            "location": location,
                            "sheet": sheet,
                            "parts": parts
                        })

                    reused_components.append({
                        "symbol": symbol,
                        "instance_count": len(by_location_sheet),
                        "locations": locations_data
                    })

        return {
            "assemblies": assemblies,
            "reused_components": reused_components,
            "single_components": single_components,
            "summary": {
                "total_assemblies": len(assemblies),
                "total_reused": len(reused_components),
                "total_single": len(single_components),
                "total_unique_symbols": len(by_symbol),
                "total_parts_entries": len(all_parts)
            }
        }

    def get_assemblies(self, section: str = "electrical") -> List[Dict[str, Any]]:
        """
        Get all assemblies (multiple parts making one schematic component)

        Args:
            section: Section to analyze

        Returns:
            List of assembly data
        """
        structure = self.get_parts_structure(section)
        return structure["assemblies"]

    def get_reused_components(self, section: str = "electrical") -> List[Dict[str, Any]]:
        """
        Get all reused components (same part in multiple locations)

        Args:
            section: Section to analyze

        Returns:
            List of reused component data
        """
        structure = self.get_parts_structure(section)
        return structure["reused_components"]

    def get_assembly_by_symbol(self, symbol: str, section: str = "electrical") -> Optional[Dict[str, Any]]:
        """
        Get assembly details for a specific symbol

        Args:
            symbol: Component symbol
            section: Section to search in

        Returns:
            Assembly data or None if not an assembly
        """
        assemblies = self.get_assemblies(section)
        for assembly in assemblies:
            if assembly["symbol"].lower() == symbol.lower():
                return assembly
        return None
