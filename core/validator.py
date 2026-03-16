"""
Validator - Cross-validation between parts lists and schematics
Shared by CLI and API interfaces
"""

import json
import os
from typing import List, Dict, Any


class PartsValidator:
    """Validates parts against schematic index"""

    def __init__(self, registry_file: str = "schematic_registry.json"):
        self.registry_file = registry_file
        self.registry = self._load_registry()

    def _load_registry(self) -> Dict[str, Any]:
        """Load schematic registry"""
        if os.path.exists(self.registry_file):
            with open(self.registry_file, 'r') as f:
                return json.load(f)
        return {"sections": {}, "parts_lists": {}}

    def validate_section(self, section_code: str) -> Dict[str, Any]:
        """
        Validate parts list against schematic index for a section

        Args:
            section_code: Section code (e.g., "10", "11")

        Returns:
            Validation report dictionary
        """
        pdf_name = f"{section_code}_parts.pdf"
        schematic_name = f"{section_code}.pdf"
        section = "electrical"

        # Check if parts list exists
        if pdf_name not in self.registry.get("parts_lists", {}).get(section, {}):
            return {
                "success": False,
                "error": f"Parts list {pdf_name} not found"
            }

        parts = self.registry["parts_lists"][section][pdf_name].get("parts", [])

        # Build schematic page index
        schematic_pages = self._build_schematic_index(section, schematic_name)

        # Validate each part
        validation_results = []
        stats = {
            "total_parts": len(parts),
            "found_on_sheet": 0,
            "missing_from_sheet": 0,
            "sheet_not_indexed": 0,
            "has_connections": 0
        }

        for part in parts:
            result = self._validate_part(part, schematic_pages, stats)
            validation_results.append(result)

        return {
            "success": True,
            "section": section_code,
            "stats": stats,
            "results": validation_results
        }

    def _build_schematic_index(self, section: str, schematic_name: str) -> Dict[str, Dict]:
        """Build index of schematic pages by sheet number"""
        schematic_pages = {}

        if schematic_name not in self.registry.get("sections", {}).get(section, {}):
            return schematic_pages

        schematic_info = self.registry["sections"][section][schematic_name]

        if not schematic_info.get("indexed"):
            return schematic_pages

        for page_num, page_data in schematic_info.get("pages", {}).items():
            sheet_num = page_data.get("sheet_number", "")
            if sheet_num:
                schematic_pages[sheet_num] = {
                    "page": page_num,
                    "components": [c.lower() for c in page_data.get("components", [])],
                    "connections": page_data.get("connections", []),
                    "summary": page_data.get("summary", "")
                }

        return schematic_pages

    def _validate_part(self, part: Dict, schematic_pages: Dict, stats: Dict) -> Dict[str, Any]:
        """Validate a single part against schematic"""
        symbol = part.get("symbol", "")
        sheet_ref = part.get("sheet_section", "")
        location = part.get("location", "")
        description = part.get("description", "")

        # Extract sheet number from reference (=11/7.7 -> 7)
        sheet_num = self._extract_sheet_number(sheet_ref)

        result = {
            "symbol": symbol,
            "sheet_ref": sheet_ref,
            "location": location,
            "description": description,
            "status": "unknown"
        }

        if not sheet_num:
            result["status"] = "no_sheet_reference"
            return result

        if sheet_num not in schematic_pages:
            result["status"] = "sheet_not_indexed"
            stats["sheet_not_indexed"] += 1
            return result

        # Check if component appears on that sheet
        page_info = schematic_pages[sheet_num]
        symbol_lower = symbol.lower()

        # Try to find component
        found = False
        for comp in page_info["components"]:
            if symbol_lower in comp or symbol_lower.replace("-", "") in comp:
                found = True
                break

        if found:
            stats["found_on_sheet"] += 1

            # Check if connections were extracted
            connections = [c for c in page_info["connections"] if symbol in c]

            if connections:
                stats["has_connections"] += 1
                result["status"] = "found_with_connections"
                result["connections"] = connections
            else:
                result["status"] = "found_no_connections"

            result["sheet_summary"] = page_info["summary"]
        else:
            stats["missing_from_sheet"] += 1
            result["status"] = "not_found_on_sheet"
            result["sheet_summary"] = page_info["summary"]

        return result

    def _extract_sheet_number(self, sheet_ref: str) -> str:
        """Extract sheet number from reference"""
        if "/" in sheet_ref:
            return sheet_ref.split("/")[1].split(".")[0]
        return ""

    def validate_all_sections(self) -> Dict[str, Any]:
        """
        Validate all sections

        Returns:
            Combined validation report
        """
        results = {}

        if "parts_lists" not in self.registry:
            return {"error": "No parts lists found"}

        section = "electrical"
        if section not in self.registry["parts_lists"]:
            return {"error": f"No parts lists in section {section}"}

        for pdf_name in self.registry["parts_lists"][section].keys():
            section_code = pdf_name.replace("_parts.pdf", "")
            results[section_code] = self.validate_section(section_code)

        # Aggregate stats
        total_stats = {
            "total_parts": 0,
            "found_on_sheet": 0,
            "missing_from_sheet": 0,
            "sheet_not_indexed": 0,
            "has_connections": 0
        }

        for section_result in results.values():
            if "stats" in section_result:
                for key in total_stats:
                    total_stats[key] += section_result["stats"].get(key, 0)

        return {
            "success": True,
            "sections": results,
            "total_stats": total_stats
        }
