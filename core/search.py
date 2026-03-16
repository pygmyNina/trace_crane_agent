"""
Search - Core search logic for schematics and sheets
Shared by CLI and API interfaces
"""

import json
import os
from typing import List, Dict, Any, Optional


class SchematicSearch:
    """Manages schematic searching and querying"""

    def __init__(self, registry_file: str = "schematic_registry.json",
                 knowledge_file: str = "trace_knowledge.json"):
        self.registry_file = registry_file
        self.knowledge_file = knowledge_file
        self.registry = self._load_registry()
        self.knowledge = self._load_knowledge()

    def _load_registry(self) -> Dict[str, Any]:
        """Load schematic registry"""
        if os.path.exists(self.registry_file):
            with open(self.registry_file, 'r') as f:
                return json.load(f)
        return {"sections": {}}

    def _load_knowledge(self) -> Dict[str, Any]:
        """Load knowledge base"""
        if os.path.exists(self.knowledge_file):
            with open(self.knowledge_file, 'r') as f:
                return json.load(f)
        return {}

    def search_schematics(self, query: str, section: str = None) -> List[Dict[str, Any]]:
        """
        Search schematic index for a query term

        Args:
            query: Search term
            section: Limit to specific section (optional)

        Returns:
            List of matching pages with context
        """
        results = []
        query_lower = query.lower()

        sections_to_search = [section] if section else self.registry["sections"].keys()

        for sect in sections_to_search:
            if sect not in self.registry["sections"]:
                continue

            for pdf_name, pdf_info in self.registry["sections"][sect].items():
                if not pdf_info.get("indexed"):
                    continue

                for page_num, page_data in pdf_info.get("pages", {}).items():
                    match = False
                    match_details = []

                    # Search in references
                    for ref in page_data.get("references", []):
                        if query_lower in ref.lower():
                            match = True
                            match_details.append(f"Reference: {ref}")

                    # Search in components
                    for comp in page_data.get("components", []):
                        if query_lower in comp.lower():
                            match = True
                            match_details.append(f"Component: {comp}")

                    # Search in cabinets
                    for cab in page_data.get("cabinets", []):
                        if query_lower in cab.lower():
                            match = True
                            match_details.append(f"Cabinet: {cab}")

                    # Search in summary
                    if query_lower in page_data.get("summary", "").lower():
                        match = True

                    if match:
                        results.append({
                            "section": sect,
                            "pdf": pdf_name,
                            "page": int(page_num),
                            "sheet_number": page_data.get("sheet_number", ""),
                            "system_group": page_data.get("system_group", ""),
                            "location": page_data.get("location", ""),
                            "summary": page_data.get("summary", ""),
                            "matches": match_details,
                            "references": page_data.get("references", []),
                            "components": page_data.get("components", []),
                            "connections": page_data.get("connections", [])
                        })

        return results

    def find_sheet(self, sheet_number: str, section: str = None) -> Optional[Dict[str, Any]]:
        """
        Find a specific sheet by number

        Args:
            sheet_number: Sheet number to find
            section: Limit to specific section (optional)

        Returns:
            Sheet data or None
        """
        sections_to_search = [section] if section else self.registry["sections"].keys()

        for sect in sections_to_search:
            if sect not in self.registry["sections"]:
                continue

            for pdf_name, pdf_info in self.registry["sections"][sect].items():
                if not pdf_info.get("indexed"):
                    continue

                for page_num, page_data in pdf_info.get("pages", {}).items():
                    if page_data.get("sheet_number") == sheet_number:
                        return {
                            "section": sect,
                            "pdf": pdf_name,
                            "page": int(page_num),
                            "sheet_number": sheet_number,
                            "system_group": page_data.get("system_group", ""),
                            "location": page_data.get("location", ""),
                            "summary": page_data.get("summary", ""),
                            "references": page_data.get("references", []),
                            "components": page_data.get("components", []),
                            "connections": page_data.get("connections", []),
                            "terminals": page_data.get("terminals", []),
                            "wire_numbers": page_data.get("wire_numbers", [])
                        }

        return None

    def get_sheets_by_system(self, system_code: str) -> List[Dict[str, Any]]:
        """
        Get all sheets for a system group

        Args:
            system_code: System group code (e.g., =10, =11)

        Returns:
            List of sheets in that system
        """
        sheets = []

        for section, pdfs in self.registry["sections"].items():
            for pdf_name, pdf_info in pdfs.items():
                if not pdf_info.get("indexed"):
                    continue

                for page_num, page_data in pdf_info.get("pages", {}).items():
                    if page_data.get("system_group") == system_code:
                        sheets.append({
                            "section": section,
                            "pdf": pdf_name,
                            "page": int(page_num),
                            "sheet_number": page_data.get("sheet_number", ""),
                            "location": page_data.get("location", ""),
                            "summary": page_data.get("summary", "")
                        })

        # Sort by sheet number
        sheets.sort(key=lambda x: x.get("sheet_number", ""))
        return sheets

    def get_sheets_by_location(self, location_code: str) -> List[Dict[str, Any]]:
        """
        Get all sheets for a location

        Args:
            location_code: Location code (e.g., +E11, +GDW)

        Returns:
            List of sheets at that location
        """
        sheets = []

        for section, pdfs in self.registry["sections"].items():
            for pdf_name, pdf_info in pdfs.items():
                if not pdf_info.get("indexed"):
                    continue

                for page_num, page_data in pdf_info.get("pages", {}).items():
                    if page_data.get("location") == location_code:
                        sheets.append({
                            "section": section,
                            "pdf": pdf_name,
                            "page": int(page_num),
                            "sheet_number": page_data.get("sheet_number", ""),
                            "system_group": page_data.get("system_group", ""),
                            "summary": page_data.get("summary", "")
                        })

        sheets.sort(key=lambda x: x.get("sheet_number", ""))
        return sheets

    def list_systems(self) -> List[Dict[str, Any]]:
        """
        List all system groups found in indexed sheets

        Returns:
            List of systems with sheet counts
        """
        systems = {}

        for section, pdfs in self.registry["sections"].items():
            for pdf_name, pdf_info in pdfs.items():
                if not pdf_info.get("indexed"):
                    continue

                for page_num, page_data in pdf_info.get("pages", {}).items():
                    sys_code = page_data.get("system_group")
                    if sys_code:
                        if sys_code not in systems:
                            systems[sys_code] = {
                                "code": sys_code,
                                "name": self._get_system_name(sys_code),
                                "sheets": []
                            }
                        systems[sys_code]["sheets"].append(page_data.get("sheet_number", ""))

        # Convert to list and add counts
        result = []
        for sys_code, data in sorted(systems.items()):
            result.append({
                "code": sys_code,
                "name": data["name"],
                "sheet_count": len(data["sheets"]),
                "sheets": sorted(set(data["sheets"]))
            })

        return result

    def _get_system_name(self, system_code: str) -> str:
        """Get system name from knowledge base"""
        if "system_groups" in self.knowledge and system_code in self.knowledge["system_groups"]:
            return self.knowledge["system_groups"][system_code].get("definition", system_code)
        return system_code

    def _get_location_name(self, location_code: str) -> str:
        """Get location name from knowledge base"""
        if "locations" in self.knowledge and location_code in self.knowledge["locations"]:
            return self.knowledge["locations"][location_code].get("description", location_code)
        return location_code
