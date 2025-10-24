"""
Vision API Integration for TRACE
Uses Claude Vision API to analyze crane schematic images
"""

import os
import json
from typing import Dict, List, Any, Optional
import base64

try:
    from anthropic import Anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False


class VisionAnalyzer:
    """Analyzes schematic images using Claude Vision API"""

    def __init__(self, api_key: str = None):
        """
        Initialize Vision Analyzer

        Args:
            api_key: Anthropic API key (or set ANTHROPIC_API_KEY env var)
        """
        if not ANTHROPIC_AVAILABLE:
            print("⚠ anthropic library not installed. Run: pip install anthropic")
            self.client = None
            return

        # Get API key from parameter or environment
        self.api_key = api_key or os.getenv('ANTHROPIC_API_KEY')

        if not self.api_key:
            print("⚠ No API key found. Set ANTHROPIC_API_KEY environment variable")
            self.client = None
        else:
            self.client = Anthropic(api_key=self.api_key)

    def _encode_image(self, image_path: str) -> Optional[str]:
        """Encode image to base64"""
        try:
            with open(image_path, 'rb') as img_file:
                return base64.standard_b64encode(img_file.read()).decode('utf-8')
        except Exception as e:
            print(f"✗ Error encoding image: {e}")
            return None

    def _get_image_media_type(self, image_path: str) -> str:
        """Determine media type from file extension"""
        ext = os.path.splitext(image_path)[1].lower()
        media_types = {
            '.png': 'image/png',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.gif': 'image/gif',
            '.webp': 'image/webp'
        }
        return media_types.get(ext, 'image/png')

    def index_page(self, image_path: str, page_num: int) -> Optional[Dict[str, Any]]:
        """
        Index a schematic page by extracting structured data

        Args:
            image_path: Path to page image
            page_num: Page number

        Returns:
            Dictionary with extracted data or None on error
        """
        if not self.client:
            return None

        # Encode image
        image_data = self._encode_image(image_path)
        if not image_data:
            return None

        # Create indexing prompt
        prompt = """Analyze this crane electrical schematic page and extract structured information.

Extract ALL of the following that you can find:

1. REFERENCES: All schematic references in format =XX/YY.Y.Z (e.g., =10/102.0.3, =22/1.1.1)
2. COMPONENTS: Component names and IDs (e.g., "Slave 22", "Breaker B1", "Motor M1", "Transformer T1")
3. CABINETS: Cabinet identifiers (e.g., "E11", "E12", "Cabinet E15")
4. TERMINALS: Terminal IDs (e.g., "1U", "2V", "3W", "X1", "A1")
5. WIRE_NUMBERS: Wire identification numbers if visible
6. CONNECTIONS: Key connections you can identify (e.g., "HVC3 breaker to =61/4.1.3")
7. SUMMARY: Brief description of what this page shows (1-2 sentences)

Return ONLY a JSON object with these fields:
{
  "references": ["=10/1.1.1", "=10/1.1.2", ...],
  "components": ["Breaker B1", "Breaker B2", ...],
  "cabinets": ["E11"],
  "terminals": ["1U", "2V", "3W"],
  "wire_numbers": ["W1", "W2", ...],
  "connections": ["Component A to =XX/YY.Y.Z", ...],
  "summary": "Brief description of page content"
}

If a field has no data, return an empty array or empty string.
"""

        try:
            # Call Vision API
            message = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=2048,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": self._get_image_media_type(image_path),
                                    "data": image_data,
                                },
                            },
                            {
                                "type": "text",
                                "text": prompt
                            }
                        ],
                    }
                ],
            )

            # Parse response
            response_text = message.content[0].text

            # Extract JSON from response (might have markdown code blocks)
            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                response_text = response_text[json_start:json_end].strip()
            elif "```" in response_text:
                json_start = response_text.find("```") + 3
                json_end = response_text.find("```", json_start)
                response_text = response_text[json_start:json_end].strip()

            # Parse JSON
            extracted_data = json.loads(response_text)

            # Add metadata
            extracted_data['page_number'] = page_num
            extracted_data['indexed_with'] = 'claude-vision'

            return extracted_data

        except json.JSONDecodeError as e:
            print(f"⚠ Failed to parse Vision API response as JSON: {e}")
            print(f"Response: {response_text[:200]}...")
            return None
        except Exception as e:
            print(f"✗ Error calling Vision API: {e}")
            return None

    def ask_question(self, image_paths: List[str], question: str) -> Optional[str]:
        """
        Ask a question about schematic page(s)

        Args:
            image_paths: List of image paths to analyze
            question: Question to ask

        Returns:
            Answer string or None on error
        """
        if not self.client:
            return None

        # Build content with images and question
        content = []

        for image_path in image_paths:
            image_data = self._encode_image(image_path)
            if image_data:
                content.append({
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": self._get_image_media_type(image_path),
                        "data": image_data,
                    },
                })

        # Add question
        content.append({
            "type": "text",
            "text": f"""You are analyzing crane electrical schematic diagrams.
Please answer this question based on the schematic page(s) provided:

{question}

Provide a detailed answer with:
1. Direct answer to the question
2. Specific references (=XX/YY.Y.Z format) where relevant
3. Component names and locations
4. Any relevant connections or signal paths

Be precise and reference specific elements visible in the schematic."""
        })

        try:
            # Call Vision API
            message = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=2048,
                messages=[
                    {
                        "role": "user",
                        "content": content,
                    }
                ],
            )

            return message.content[0].text

        except Exception as e:
            print(f"✗ Error calling Vision API: {e}")
            return None

    def analyze_connection(self, image_paths: List[str], from_component: str,
                          to_component: str = None) -> Optional[str]:
        """
        Trace a connection between components

        Args:
            image_paths: List of image paths to analyze
            from_component: Starting component
            to_component: Ending component (optional)

        Returns:
            Connection description or None on error
        """
        if to_component:
            question = f"Trace the connection from {from_component} to {to_component}. " \
                      f"Show the complete signal path including all intermediate components, " \
                      f"wire numbers, terminals, and references."
        else:
            question = f"Show all connections from {from_component}. " \
                      f"List what it connects to, including wire numbers, terminals, and references."

        return self.ask_question(image_paths, question)

    def extract_component_details(self, image_path: str, component_name: str) -> Optional[str]:
        """
        Extract detailed information about a specific component

        Args:
            image_path: Path to schematic image
            component_name: Name of component to analyze

        Returns:
            Component details or None on error
        """
        question = f"Provide detailed information about {component_name} shown in this schematic. " \
                  f"Include: location/cabinet, all terminals, connections, ratings, " \
                  f"and any other specifications visible."

        return self.ask_question([image_path], question)

    def check_api_available(self) -> bool:
        """Check if Vision API is available and configured"""
        return self.client is not None

    def get_usage_estimate(self, num_pages: int) -> Dict[str, Any]:
        """
        Estimate API usage cost for indexing pages

        Args:
            num_pages: Number of pages to index

        Returns:
            Dictionary with cost estimates
        """
        # Rough estimates based on Claude Vision pricing
        cost_per_page = 0.02  # Approximate
        total_cost = num_pages * cost_per_page

        return {
            "pages": num_pages,
            "estimated_cost_per_page": cost_per_page,
            "estimated_total_cost": total_cost,
            "note": "Actual costs may vary based on image size and API pricing"
        }
