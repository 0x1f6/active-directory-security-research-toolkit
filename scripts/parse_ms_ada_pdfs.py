#!/usr/bin/env python3
"""
Parse Microsoft AD Schema PDFs (MS-ADA1, MS-ADA2, MS-ADA3) to extract attribute data.

This script extracts AD attribute information from the official Microsoft PDF documents
and outputs structured JSON data compatible with the enhanced schema format.
"""

import re
import json
import argparse
import sys
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict

try:
    import pymupdf  # PyMuPDF for PDF parsing
except ImportError:
    print("Error: PyMuPDF not installed. Run: uv add pymupdf", file=sys.stderr)
    sys.exit(1)


@dataclass
class ADAttribute:
    """Active Directory attribute data extracted from PDF."""

    cn: Optional[str] = None
    ldap_display_name: Optional[str] = None
    attribute_id: Optional[str] = None
    attribute_syntax: Optional[str] = None
    om_syntax: Optional[str] = None
    schema_id_guid: Optional[str] = None
    is_single_valued: Optional[str] = None
    system_only: Optional[str] = None
    search_flags: Optional[str] = None
    range_lower: Optional[str] = None
    range_upper: Optional[str] = None
    attribute_security_guid: Optional[str] = None
    mapi_id: Optional[str] = None
    is_member_of_partial_attribute_set: Optional[str] = None
    system_flags: Optional[str] = None
    schema_flags_ex: Optional[str] = None
    source_section: Optional[str] = None
    source_pdf: Optional[str] = None


class MSADAPDFParser:
    """Parser for Microsoft Active Directory Schema PDF documents."""

    def __init__(self):
        # Regex patterns for extracting attribute data
        self.attribute_header_pattern = re.compile(
            r"^(\d+\.\d+)\s+Attribute\s+(.+)$", re.MULTILINE
        )
        self.field_patterns = {
            "cn": re.compile(r"^\xa0cn:\s*(.+)$", re.MULTILINE | re.IGNORECASE),
            "ldap_display_name": re.compile(
                r"^\xa0ldapDisplayName:\s*(.+)$", re.MULTILINE | re.IGNORECASE
            ),
            "attribute_id": re.compile(
                r"^\xa0attributeId:\s*(.+)$", re.MULTILINE | re.IGNORECASE
            ),
            "attribute_syntax": re.compile(
                r"^\xa0attributeSyntax:\s*(.+)$", re.MULTILINE | re.IGNORECASE
            ),
            "om_syntax": re.compile(
                r"^\xa0omSyntax:\s*(.+)$", re.MULTILINE | re.IGNORECASE
            ),
            "schema_id_guid": re.compile(
                r"^\xa0schemaIdGuid:\s*(.+)$", re.MULTILINE | re.IGNORECASE
            ),
            "is_single_valued": re.compile(
                r"^\xa0isSingleValued:\s*(.+)$", re.MULTILINE | re.IGNORECASE
            ),
            "system_only": re.compile(
                r"^\xa0systemOnly:\s*(.+)$", re.MULTILINE | re.IGNORECASE
            ),
            "search_flags": re.compile(
                r"^\xa0searchFlags:\s*(.+)$", re.MULTILINE | re.IGNORECASE
            ),
            "range_lower": re.compile(
                r"^\xa0rangeLower:\s*(.+)$", re.MULTILINE | re.IGNORECASE
            ),
            "range_upper": re.compile(
                r"^\xa0rangeUpper:\s*(.+)$", re.MULTILINE | re.IGNORECASE
            ),
            "attribute_security_guid": re.compile(
                r"^\xa0attributeSecurityGuid:\s*(.+)$", re.MULTILINE | re.IGNORECASE
            ),
            "mapi_id": re.compile(
                r"^\xa0mapiID:\s*(.+)$", re.MULTILINE | re.IGNORECASE
            ),
            "is_member_of_partial_attribute_set": re.compile(
                r"^\xa0isMemberOfPartialAttributeSet:\s*(.+)$",
                re.MULTILINE | re.IGNORECASE,
            ),
            "system_flags": re.compile(
                r"^\xa0systemFlags:\s*(.+)$", re.MULTILINE | re.IGNORECASE
            ),
            "schema_flags_ex": re.compile(
                r"^\xa0schemaFlagsEx:\s*(.+)$", re.MULTILINE | re.IGNORECASE
            ),
        }

    def extract_text_from_pdf(self, pdf_path: Path) -> str:
        """Extract all text content from PDF."""
        try:
            doc = pymupdf.open(pdf_path)
            text_content = []

            for page_num in range(len(doc)):
                page = doc[page_num]
                text_content.append(page.get_text())

            doc.close()
            return "\n".join(text_content)

        except Exception as e:
            print(f"Error reading PDF {pdf_path}: {e}", file=sys.stderr)
            return ""

    def parse_attribute_blocks(self, text: str, source_pdf: str) -> List[ADAttribute]:
        """Parse attribute blocks from extracted PDF text."""
        attributes = []

        # Find all attribute headers
        attribute_matches = list(self.attribute_header_pattern.finditer(text))

        for i, match in enumerate(attribute_matches):
            section_num = match.group(1)
            attr_name = match.group(2).strip()

            # Determine the text block for this attribute
            start_pos = match.start()
            if i + 1 < len(attribute_matches):
                end_pos = attribute_matches[i + 1].start()
                attr_block = text[start_pos:end_pos]
            else:
                # Last attribute, take rest of text or reasonable chunk
                attr_block = text[start_pos : start_pos + 2000]

            # Extract field data from this block
            attribute = ADAttribute(source_section=section_num, source_pdf=source_pdf)

            # Extract each field using regex patterns
            for field_name, pattern in self.field_patterns.items():
                field_match = pattern.search(attr_block)
                if field_match:
                    value = field_match.group(1).strip()

                    # Handle multiline fields (especially systemFlags, schemaFlagsEx)
                    if field_name in [
                        "system_flags",
                        "schema_flags_ex",
                    ] and value.endswith("|"):
                        # Look for continuation lines
                        lines = attr_block.split("\n")
                        start_line_found = False
                        multiline_value = value

                        for line in lines:
                            if field_match.group(0).strip() in line:
                                start_line_found = True
                                continue
                            elif start_line_found:
                                # Check if this is a continuation line (double \xa0)
                                if line.startswith("\xa0\xa0") and (
                                    "FLAG_" in line or line.strip()
                                ):
                                    continuation = line.replace("\xa0\xa0", "").strip()
                                    if continuation:
                                        multiline_value += " " + continuation
                                else:
                                    # End of multiline field
                                    break

                        value = multiline_value

                    # Clean up common formatting issues
                    value = re.sub(r"\s+", " ", value)  # Normalize whitespace
                    value = value.strip()
                    setattr(attribute, field_name, value)

            # If we didn't find ldap_display_name, try to infer from attribute name
            if not attribute.ldap_display_name and attr_name:
                attribute.ldap_display_name = attr_name

            attributes.append(attribute)

        return attributes

    def parse_pdf_file(self, pdf_path: Path) -> List[ADAttribute]:
        """Parse a single PDF file and return extracted attributes."""
        print(f"Parsing PDF: {pdf_path.name}")

        text = self.extract_text_from_pdf(pdf_path)
        if not text:
            return []

        attributes = self.parse_attribute_blocks(text, pdf_path.name)
        print(f"  Found {len(attributes)} attributes")

        return attributes

    def parse_multiple_pdfs(self, pdf_paths: List[Path]) -> Dict[str, ADAttribute]:
        """Parse multiple PDF files and return consolidated attribute data."""
        all_attributes = {}

        for pdf_path in pdf_paths:
            if not pdf_path.exists():
                print(f"Warning: PDF file not found: {pdf_path}", file=sys.stderr)
                continue

            attributes = self.parse_pdf_file(pdf_path)

            for attr in attributes:
                # Use GUID as key if available, otherwise ldap_display_name
                key = attr.schema_id_guid or attr.ldap_display_name
                if key:
                    # Clean up GUID format if needed
                    if key and len(key) == 36 and "-" in key:
                        key = key.lower()
                    all_attributes[key] = attr

        return all_attributes

    def export_to_enhanced_json(
        self, attributes: Dict[str, ADAttribute], output_path: Path
    ) -> None:
        """Export attributes directly to enhanced schema format."""
        enhanced_schema = {}

        for guid, attr in attributes.items():
            enhanced_entry = {
                "ldapDisplayName": attr.ldap_display_name,
            }

            # Field mapping from raw PDF data to enhanced schema format
            field_mapping = {
                "cn": attr.cn,
                "attributeId": attr.attribute_id,
                "attributeSyntax": attr.attribute_syntax,
                "omSyntax": attr.om_syntax,
                "isSingleValued": attr.is_single_valued,
                "systemOnly": attr.system_only,
                "searchFlags": attr.search_flags,
                "rangeLower": attr.range_lower,
                "rangeUpper": attr.range_upper,
                "attributeSecurityGuid": attr.attribute_security_guid,
                "mapiID": attr.mapi_id,
                "isMemberOfPartialAttributeSet": attr.is_member_of_partial_attribute_set,
                "systemFlags": attr.system_flags,
                "schemaFlagsEx": attr.schema_flags_ex,
            }

            for enhanced_field, value in field_mapping.items():
                if value is not None and value != "":
                    # Convert TRUE/FALSE strings to boolean for specific fields
                    if enhanced_field in [
                        "isSingleValued",
                        "systemOnly",
                        "isMemberOfPartialAttributeSet",
                    ]:
                        if value == "TRUE":
                            enhanced_entry[enhanced_field] = True
                        elif value == "FALSE":
                            enhanced_entry[enhanced_field] = False
                        else:
                            enhanced_entry[enhanced_field] = value
                    # Convert numeric strings to integers for specific fields
                    elif enhanced_field in [
                        "omSyntax",
                        "rangeLower",
                        "rangeUpper",
                        "mapiID",
                    ]:
                        try:
                            enhanced_entry[enhanced_field] = int(value)
                        except ValueError:
                            enhanced_entry[enhanced_field] = value
                    else:
                        enhanced_entry[enhanced_field] = value

            enhanced_schema[guid] = enhanced_entry

        # Save enhanced schema
        with open(output_path, "w") as f:
            json.dump(enhanced_schema, f, indent=2, sort_keys=True)

        # Print summary
        print("\n📊 Enhanced Schema Summary:")
        print(f"Total attributes: {len(enhanced_schema)}")

        # Count attributes with various levels of completeness
        field_counts = {}
        for entry in enhanced_schema.values():
            for field in entry.keys():
                field_counts[field] = field_counts.get(field, 0) + 1

        print("\nField Coverage:")
        for field, count in sorted(field_counts.items()):
            percentage = (count / len(enhanced_schema)) * 100
            print(f"  {field}: {count}/{len(enhanced_schema)} ({percentage:.1f}%)")

        # Show example enhanced entry
        example_entries = [
            (guid, data) for guid, data in enhanced_schema.items() if len(data) > 1
        ]
        if example_entries:
            print("\n💎 Example enhanced entry:")
            example_guid, example_data = example_entries[0]
            print(f"GUID: {example_guid}")
            for key, value in example_data.items():
                print(f"  {key}: {value}")

        print(f"\n💾 Enhanced schema saved to: {output_path}")

    def export_to_json(
        self, attributes: Dict[str, ADAttribute], output_path: Optional[Path] = None
    ) -> str:
        """Export attributes to raw JSON format (for intermediate processing)."""
        # Convert to raw JSON format
        raw_data = {}

        for key, attr in attributes.items():
            attr_dict = asdict(attr)
            # Remove None values and internal fields
            cleaned_dict = {
                k: v
                for k, v in attr_dict.items()
                if v is not None and not k.startswith("source_")
            }
            raw_data[key] = cleaned_dict

        json_output = json.dumps(raw_data, indent=2, ensure_ascii=False)

        if output_path:
            output_path.write_text(json_output, encoding="utf-8")
            print(f"Exported {len(raw_data)} raw attributes to {output_path}")

        return json_output


def main():
    parser = argparse.ArgumentParser(
        description="Parse Microsoft AD Schema PDFs to extract attribute data",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Parse all three MS-ADA PDFs
  %(prog)s ms-ada1.pdf ms-ada2.pdf ms-ada3.pdf -o ad_schema_from_pdfs.json
  
  # Parse single PDF and output to stdout
  %(prog)s ms-ada1.pdf
  
  # Parse PDFs from docs/specs directory
  %(prog)s docs/specs/openspecs-windows_protocols-ms-ada*.pdf
        """,
    )

    parser.add_argument(
        "pdf_files", nargs="+", type=Path, help="Path(s) to MS-ADA PDF files"
    )

    parser.add_argument(
        "-o", "--output", type=Path, help="Output JSON file (default: stdout)"
    )

    parser.add_argument("--stats", action="store_true", help="Show parsing statistics")

    args = parser.parse_args()

    # Initialize parser
    pdf_parser = MSADAPDFParser()

    # Parse PDFs
    attributes = pdf_parser.parse_multiple_pdfs(args.pdf_files)

    if args.stats:
        print("\nParsing Statistics:")
        print(f"  Total attributes found: {len(attributes)}")

        # Count by source PDF
        pdf_counts = {}
        for attr in attributes.values():
            pdf = attr.source_pdf or "unknown"
            pdf_counts[pdf] = pdf_counts.get(pdf, 0) + 1

        for pdf, count in sorted(pdf_counts.items()):
            print(f"  {pdf}: {count} attributes")

        # Count fields with data
        field_stats = {}
        for attr in attributes.values():
            for field_name in [
                "cn",
                "ldap_display_name",
                "attribute_id",
                "schema_id_guid",
                "attribute_syntax",
            ]:
                value = getattr(attr, field_name)
                if value:
                    field_stats[field_name] = field_stats.get(field_name, 0) + 1

        print("\nField Coverage:")
        for field, count in sorted(field_stats.items()):
            percentage = (count / len(attributes)) * 100
            print(f"  {field}: {count}/{len(attributes)} ({percentage:.1f}%)")

    # Export results
    json_output = pdf_parser.export_to_json(attributes, args.output)

    if not args.output:
        print(json_output)


if __name__ == "__main__":
    main()
