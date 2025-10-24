"""
Schematic Analyzer using Claude Vision
Analyzes crane schematic images and extracts components, references, and connections
"""

import base64
import os
from pathlib import Path
from typing import Dict, List, Any, Optional
import anthropic
from pdf_processor import SchematicPDFProcessor


class SchematicAnalyzer:
    """Analyzes crane schematics using Claude Vision API"""

    def __init__(self, api_key: Optional[str] = None):
        """Initialize the analyzer"""
        if api_key is None:
            api_key = os.getenv("ANTHROPIC_API_KEY")

        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not found")

        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = "claude-3-5-sonnet-20241022"

    def analyze_schematic_page(self, pdf_path: str, page_num: int = 0,
                               focus_areas: List[str] = None) -> Dict[str, Any]:
        """
        Analyze a single page of a schematic using Claude Vision

        Args:
            pdf_path: Path to PDF file
            page_num: Page number to analyze (0-indexed)
            focus_areas: Optional list of what to focus on
                        ['components', 'index_references', 'wire_connections', 'labels']

        Returns:
            Dictionary with analysis results
        """
        if focus_areas is None:
            focus_areas = ['components', 'index_references', 'wire_connections', 'labels']

        # Extract page as image
        with SchematicPDFProcessor(pdf_path) as processor:
            if page_num >= processor.num_pages:
                raise ValueError(f"Page {page_num} out of range (0-{processor.num_pages-1})")

            # Render page to image
            img = processor.render_page_image(page_num, zoom=2.0)

            # Convert to base64
            import io
            img_byte_arr = io.BytesIO()
            img.save(img_byte_arr, format='PNG')
            img_byte_arr = img_byte_arr.getvalue()
            img_base64 = base64.b64encode(img_byte_arr).decode('utf-8')

        # Build analysis prompt
        prompt = self._build_analysis_prompt(focus_areas)

        # Call Claude Vision API
        response = self.client.messages.create(
            model=self.model,
            max_tokens=4096,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/png",
                                "data": img_base64,
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
        analysis_text = response.content[0].text

        return {
            "pdf_path": pdf_path,
            "page_num": page_num,
            "raw_response": analysis_text,
            "focus_areas": focus_areas,
            "model": self.model,
            "parsed_analysis": self._parse_analysis(analysis_text, focus_areas)
        }

    def _build_analysis_prompt(self, focus_areas: List[str]) -> str:
        """Build the prompt for schematic analysis"""

        prompt = """You are analyzing a crane electrical schematic. Please provide a detailed analysis.

# Schematic Reading Rules

## Index Format
- Format: =XX/YY.Y.Z where:
  - XX = Section number (2 digits)
  - YY.Y = Sheet number (2 digits + 1 decimal digit)
  - Z = Column number (1 digit)
- Shorthand: =XX/YY.Z means =XX/YY.0.Z
- Example: =61/102.8 expands to =61/102.0.8

## Wire Connections
- Dots at wire crossings indicate electrical connections
- Perpendicular crossings WITHOUT dots are NOT connected

## Component Types to Look For
- HVC (High Voltage Contactors): HVC1, HVC2, HVC3, etc.
- Slaves: Slave 22, Slave 23, Slave 60, etc.
- Cabinets: Cabinet E11, Cabinet E12, etc.
- Modules: IM151, PM, DI, RTD
- Transformers
- Other labeled components

"""

        prompt += "\n# Please Analyze:\n\n"

        if 'components' in focus_areas:
            prompt += """## 1. COMPONENTS
List all identifiable components with:
- Component name/label (exactly as shown)
- Type (HVC, Slave, Cabinet, Module, etc.)
- Approximate location (describe position on page)
- Any associated index reference nearby

"""

        if 'index_references' in focus_areas:
            prompt += """## 2. INDEX REFERENCES
List all index references (=XX/YY.Y.Z format):
- Full reference (e.g., =61/102.0.8)
- If shorthand, provide expanded form
- Location on page
- What component or wire it's associated with

"""

        if 'wire_connections' in focus_areas:
            prompt += """## 3. WIRE CONNECTIONS
Identify key wire connections:
- Wire labels/numbers
- Connection points (marked with dots)
- What components they connect
- Any non-connections (perpendicular crossings without dots)

"""

        if 'labels' in focus_areas:
            prompt += """## 4. LABELS AND TEXT
List any other important labels:
- Terminal numbers
- Wire identifiers
- Notes or specifications
- Section/sheet identifiers

"""

        prompt += """\n# Output Format

Please structure your response clearly with headers for each section.
Be specific and precise - use exact labels and references as they appear.
If something is unclear or ambiguous, note that.
"""

        return prompt

    def _parse_analysis(self, analysis_text: str, focus_areas: List[str]) -> Dict[str, Any]:
        """
        Parse Claude's analysis text into structured data

        This is a basic parser - can be enhanced based on actual response format
        """
        parsed = {
            "components": [],
            "index_references": [],
            "wire_connections": [],
            "labels": [],
            "notes": []
        }

        # Simple section-based parsing
        current_section = None
        lines = analysis_text.split('\n')

        for line in lines:
            line = line.strip()

            # Detect section headers
            if 'COMPONENT' in line.upper():
                current_section = 'components'
            elif 'INDEX REFERENCE' in line.upper():
                current_section = 'index_references'
            elif 'WIRE CONNECTION' in line.upper():
                current_section = 'wire_connections'
            elif 'LABEL' in line.upper() or 'TEXT' in line.upper():
                current_section = 'labels'

            # Add content to current section
            if current_section and line and not line.startswith('#'):
                if line.startswith('-') or line.startswith('*'):
                    parsed[current_section].append(line[1:].strip())

        return parsed

    def analyze_full_schematic(self, pdf_path: str,
                               focus_areas: List[str] = None) -> List[Dict[str, Any]]:
        """
        Analyze all pages of a schematic PDF

        Returns list of analysis results, one per page
        """
        results = []

        with SchematicPDFProcessor(pdf_path) as processor:
            num_pages = processor.num_pages

            for page_num in range(num_pages):
                print(f"Analyzing page {page_num + 1}/{num_pages}...")

                analysis = self.analyze_schematic_page(
                    pdf_path,
                    page_num,
                    focus_areas
                )

                results.append(analysis)

        return results

    def compare_with_ground_truth(self, analysis: Dict[str, Any],
                                  ground_truth: Dict[str, Any]) -> Dict[str, Any]:
        """
        Compare Claude's analysis with ground truth
        Returns differences and accuracy metrics
        """
        comparison = {
            "matches": [],
            "misses": [],
            "false_positives": [],
            "accuracy": {}
        }

        # Compare each category
        for category in ['components', 'index_references', 'wire_connections']:
            if category in analysis['parsed_analysis'] and category in ground_truth:
                analyzed = set(analysis['parsed_analysis'][category])
                truth = set(ground_truth[category])

                matches = analyzed & truth
                misses = truth - analyzed
                false_pos = analyzed - truth

                comparison["matches"].extend([{
                    "category": category,
                    "item": item
                } for item in matches])

                comparison["misses"].extend([{
                    "category": category,
                    "item": item
                } for item in misses])

                comparison["false_positives"].extend([{
                    "category": category,
                    "item": item
                } for item in false_pos])

                # Calculate accuracy
                total = len(truth)
                if total > 0:
                    comparison["accuracy"][category] = len(matches) / total

        return comparison


if __name__ == "__main__":
    import sys
    from dotenv import load_dotenv

    load_dotenv()

    if len(sys.argv) < 2:
        print("Usage: python schematic_analyzer.py <pdf_path> [page_num]")
        sys.exit(1)

    pdf_path = sys.argv[1]
    page_num = int(sys.argv[2]) if len(sys.argv) > 2 else 0

    analyzer = SchematicAnalyzer()

    print(f"Analyzing {pdf_path}, page {page_num}...")
    result = analyzer.analyze_schematic_page(pdf_path, page_num)

    print("\n" + "="*60)
    print("ANALYSIS RESULT")
    print("="*60)
    print(result['raw_response'])
    print("\n" + "="*60)
    print("PARSED COMPONENTS:")
    for comp in result['parsed_analysis']['components']:
        print(f"  - {comp}")
    print("\nPARSED INDEX REFERENCES:")
    for ref in result['parsed_analysis']['index_references']:
        print(f"  - {ref}")
