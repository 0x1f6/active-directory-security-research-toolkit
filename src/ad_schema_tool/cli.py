#!/usr/bin/env python3
"""CLI interface for AD Schema Mapping Tool."""

import argparse
import csv
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional


# ANSI Color codes for terminal output
class Colors:
    """ANSI color codes for terminal output."""

    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"

    # Foreground colors
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"
    GRAY = "\033[90m"

    # Background colors
    BG_RED = "\033[41m"
    BG_GREEN = "\033[42m"
    BG_YELLOW = "\033[43m"
    BG_BLUE = "\033[44m"


# Global flag for plain output mode
_PLAIN_OUTPUT = False


def set_plain_output(plain: bool) -> None:
    """Set plain output mode globally."""
    global _PLAIN_OUTPUT
    _PLAIN_OUTPUT = plain


def supports_color() -> bool:
    """Check if terminal supports ANSI colors."""
    if _PLAIN_OUTPUT:
        return False
    return (
        hasattr(sys.stdout, "isatty")
        and sys.stdout.isatty()
        and os.getenv("TERM") != "dumb"
        and os.getenv("NO_COLOR") is None
    )


def colorize(text: str, color: str = "", reset: bool = True) -> str:
    """Apply color to text if terminal supports it."""
    if not supports_color():
        return text

    result = f"{color}{text}"
    if reset:
        result += Colors.RESET
    return result


def print_header(title: str, subtitle: str = "") -> None:
    """Print a formatted header."""
    print()
    print(colorize(f"┌─ {title}", Colors.BOLD + Colors.CYAN))
    if subtitle:
        print(colorize(f"│  {subtitle}", Colors.DIM))
    print(colorize("└─", Colors.CYAN))


def print_success(message: str) -> None:
    """Print a success message."""
    icon = "✓" if supports_color() else "[OK]"
    print(colorize(f"{icon} {message}", Colors.GREEN))


def print_error(message: str) -> None:
    """Print an error message."""
    icon = "✗" if supports_color() else "[ERROR]"
    print(colorize(f"{icon} {message}", Colors.RED), file=sys.stderr)


def print_info(message: str) -> None:
    """Print an info message."""
    icon = "ℹ" if supports_color() else "[INFO]"
    print(colorize(f"{icon} {message}", Colors.BLUE))


def format_guid(guid: str) -> str:
    """Format GUID with color."""
    return colorize(guid, Colors.YELLOW)


def format_attribute_name(name: str) -> str:
    """Format attribute name with color."""
    return colorize(name, Colors.GREEN + Colors.BOLD)


def format_count(count: int) -> str:
    """Format count with color."""
    return colorize(str(count), Colors.CYAN + Colors.BOLD)


def export_mappings(
    mappings: Dict[str, str], format_type: str, output_file: Optional[Path] = None
) -> None:
    """Export schema mappings in specified format."""
    # Generate filename if not provided
    if not output_file:
        output_file = Path(f"ad_schema_attributes.{format_type}")

    try:
        if format_type == "json":
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(mappings, f, indent=2, sort_keys=True)

        elif format_type == "csv":
            with open(output_file, "w", encoding="utf-8", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["GUID", "AttributeName"])  # Header
                for guid, name in sorted(mappings.items(), key=lambda x: x[1]):
                    writer.writerow([guid, name])

        elif format_type == "tsv":
            with open(output_file, "w", encoding="utf-8") as f:
                f.write("GUID\tAttributeName\n")  # Header
                for guid, name in sorted(mappings.items(), key=lambda x: x[1]):
                    f.write(f"{guid}\t{name}\n")

        if _PLAIN_OUTPUT:
            print(f"Exported {len(mappings)} mappings to {output_file}")
        else:
            print_success(
                f"Exported {format_count(len(mappings))} mappings to {colorize(str(output_file), Colors.CYAN)}"
            )

    except OSError as e:
        if _PLAIN_OUTPUT:
            print(f"ERROR: Failed to write export file: {e}", file=sys.stderr)
        else:
            print_error(f"Failed to write export file: {e}")
        sys.exit(1)


def load_schema_mappings(json_file: Path) -> Dict[str, str]:
    """Load schema mappings from enhanced JSON file.

    Converts from enhanced JSON format (GUID -> {ldapDisplayName, ...})
    to simple mapping format (GUID -> ldapDisplayName).
    """
    try:
        with open(json_file, "r", encoding="utf-8") as f:
            enhanced_data = json.load(f)

        # Convert enhanced format to simple GUID -> ldapDisplayName mapping
        mappings = {}
        for guid, attr_data in enhanced_data.items():
            ldap_display_name = attr_data.get(
                "ldapDisplayName", attr_data.get("cn", f"Unknown-{guid}")
            )
            mappings[guid] = ldap_display_name

        return mappings
    except FileNotFoundError:
        print_error(f"Schema mapping file not found: {json_file}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print_error(f"Invalid JSON in schema mapping file: {e}")
        sys.exit(1)


def lookup_guid(mappings: Dict[str, str], guid: str) -> None:
    """Look up attribute name for a GUID."""
    name = mappings.get(guid)
    if name:
        if _PLAIN_OUTPUT:
            print(f"{guid}\t{name}")
        else:
            print_header("🔍 GUID Lookup Result")
            print(f"  GUID: {format_guid(guid)}")
            print(f"  Name: {format_attribute_name(name)}")
    else:
        if _PLAIN_OUTPUT:
            print(f"ERROR: GUID {guid} not found", file=sys.stderr)
        else:
            print_error(f"GUID {format_guid(guid)} not found in schema mappings")
        sys.exit(1)


def lookup_name(mappings: Dict[str, str], name: str) -> None:
    """Look up GUID for an attribute name."""
    reverse_mappings = {v: k for k, v in mappings.items()}
    guid = reverse_mappings.get(name)
    if guid:
        if _PLAIN_OUTPUT:
            print(f"{name}\t{guid}")
        else:
            print_header("🔍 Name Lookup Result")
            print(f"  Name: {format_attribute_name(name)}")
            print(f"  GUID: {format_guid(guid)}")
    else:
        if _PLAIN_OUTPUT:
            print(f"ERROR: Attribute name '{name}' not found", file=sys.stderr)
        else:
            print_error(
                f"Attribute name '{format_attribute_name(name)}' not found in schema mappings"
            )
        sys.exit(1)


def search_pattern(mappings: Dict[str, str], pattern: str) -> None:
    """Search for attributes matching a pattern."""
    pattern_lower = pattern.lower()
    matches = [
        (guid, name) for guid, name in mappings.items() if pattern_lower in name.lower()
    ]

    if matches:
        if _PLAIN_OUTPUT:
            for guid, name in sorted(matches, key=lambda x: x[1]):
                print(f"{name}\t{guid}")
        else:
            print_header(
                "🔎 Search Results",
                f"Found {format_count(len(matches))} attributes matching '{colorize(pattern, Colors.MAGENTA)}'",
            )

            # Group results nicely
            for i, (guid, name) in enumerate(sorted(matches, key=lambda x: x[1]), 1):
                # Highlight the matching pattern in the name (case-insensitive)
                if supports_color():
                    import re

                    # Find all matches of the pattern (case-insensitive)
                    matches_iter = re.finditer(re.escape(pattern), name, re.IGNORECASE)

                    formatted_parts = []
                    last_end = 0

                    for match in matches_iter:
                        # Add text before the match (in green)
                        if match.start() > last_end:
                            formatted_parts.append(
                                colorize(
                                    name[last_end : match.start()],
                                    Colors.GREEN + Colors.BOLD,
                                )
                            )
                        # Add the highlighted match (in magenta)
                        formatted_parts.append(
                            colorize(match.group(0), Colors.MAGENTA + Colors.BOLD)
                        )
                        last_end = match.end()

                    # Add remaining text after last match (in green)
                    if last_end < len(name):
                        formatted_parts.append(
                            colorize(name[last_end:], Colors.GREEN + Colors.BOLD)
                        )

                    formatted_name = "".join(formatted_parts)
                else:
                    formatted_name = format_attribute_name(name)

                print(f"  {colorize(f'{i:3}.', Colors.GRAY)} {formatted_name}")
                print(f"       {colorize('GUID:', Colors.DIM)} {format_guid(guid)}")

                # Add spacing every 5 items for readability
                if i % 5 == 0 and i < len(matches):
                    print()
    else:
        if _PLAIN_OUTPUT:
            print(f"ERROR: No attributes found matching '{pattern}'", file=sys.stderr)
        else:
            print_error(
                f"No attributes found matching '{colorize(pattern, Colors.MAGENTA)}'"
            )


def intersect_files(
    mappings: Dict[str, str],
    file_paths: list[Path],
    annotate: bool = False,
    output_file: Optional[Path] = None,
) -> None:
    """Find intersection of GUIDs across multiple text files.

    Args:
        mappings: GUID to attribute name mappings
        file_paths: List of text files containing GUIDs (one per line)
        annotate: Whether to show attribute names alongside GUIDs
        output_file: Optional file to write results to
    """
    if len(file_paths) < 2:
        if _PLAIN_OUTPUT:
            print("ERROR: Need at least 2 files for intersection", file=sys.stderr)
        else:
            print_error("Need at least 2 files for intersection")
        sys.exit(1)

    # Read GUIDs from each file
    file_sets = []
    file_names = []

    for file_path in file_paths:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                guids = set()
                for line in f:
                    line = line.strip()
                    if line and not line.startswith(
                        "#"
                    ):  # Skip empty lines and comments
                        guids.add(line)
                file_sets.append(guids)
                file_names.append(file_path.name)

        except FileNotFoundError:
            if _PLAIN_OUTPUT:
                print(f"ERROR: File not found: {file_path}", file=sys.stderr)
            else:
                print_error(f"File not found: {colorize(str(file_path), Colors.CYAN)}")
            sys.exit(1)
        except OSError as e:
            if _PLAIN_OUTPUT:
                print(f"ERROR: Cannot read file {file_path}: {e}", file=sys.stderr)
            else:
                print_error(
                    f"Cannot read file {colorize(str(file_path), Colors.CYAN)}: {e}"
                )
            sys.exit(1)

    # Find intersection
    intersection = file_sets[0]
    for guid_set in file_sets[1:]:
        intersection = intersection.intersection(guid_set)

    # Prepare output lines
    output_lines = []
    if not intersection:
        if not output_file:  # Only print to stderr if not writing to file
            if _PLAIN_OUTPUT:
                print("No common GUIDs found", file=sys.stderr)
            else:
                print_error("No common GUIDs found across all files")
        return

    # Generate output content
    for guid in sorted(intersection):
        if annotate:
            name = mappings.get(guid, "Unknown")
            if output_file or _PLAIN_OUTPUT:
                output_lines.append(f"{guid}\t{name}")
            else:
                output_lines.append((guid, name))  # Tuple for fancy console output
        else:
            output_lines.append(guid)

    # Write to file if specified
    if output_file:
        try:
            with open(output_file, "w", encoding="utf-8") as f:
                if annotate:
                    f.write("GUID\tAttributeName\n")  # Header for annotated output
                for line in output_lines:
                    f.write(f"{line}\n")

            if _PLAIN_OUTPUT:
                print(f"Wrote {len(intersection)} common GUIDs to {output_file}")
            else:
                print_success(
                    f"Wrote {format_count(len(intersection))} common GUIDs to {colorize(str(output_file), Colors.CYAN)}"
                )

        except OSError as e:
            if _PLAIN_OUTPUT:
                print(f"ERROR: Failed to write output file: {e}", file=sys.stderr)
            else:
                print_error(f"Failed to write output file: {e}")
            sys.exit(1)

    # Console output
    if _PLAIN_OUTPUT and not output_file:
        for line in output_lines:
            print(line)
    elif not output_file:  # Fancy output only when not writing to file
        print_header(
            "🔍 GUID Intersection Results",
            f"Found {format_count(len(intersection))} common GUIDs across {len(file_paths)} files",
        )

        # Show file info
        print(colorize("Files analyzed:", Colors.DIM))
        for i, name in enumerate(file_names, 1):
            print(
                f"  {colorize(f'{i}.', Colors.GRAY)} {colorize(name, Colors.CYAN)} ({format_count(len(file_sets[i - 1]))} GUIDs)"
            )
        print()

        # Show intersection results
        for i, item in enumerate(output_lines, 1):
            if annotate:
                guid, name = item
                print(
                    f"  {colorize(f'{i:3}.', Colors.GRAY)} {format_guid(guid)} {colorize('→', Colors.DIM)} {format_attribute_name(name)}"
                )
            else:
                print(f"  {colorize(f'{i:3}.', Colors.GRAY)} {format_guid(item)}")


def list_all(mappings: Dict[str, str]) -> None:
    """List all schema attributes."""
    if _PLAIN_OUTPUT:
        for guid, name in sorted(mappings.items(), key=lambda x: x[1]):
            print(f"{name}\t{guid}")
    else:
        print_header(
            "📚 All AD Schema Attributes",
            f"Showing all {format_count(len(mappings))} available attributes",
        )

        # Add a note about piping for large output
        if len(mappings) > 50:
            print_info(
                "💡 Tip: Pipe to 'less' for easier browsing: ad-schema-tool list | less"
            )
            print()

        for i, (guid, name) in enumerate(
            sorted(mappings.items(), key=lambda x: x[1]), 1
        ):
            print(f"  {colorize(f'{i:4}.', Colors.GRAY)} {format_attribute_name(name)}")
            print(f"         {colorize('GUID:', Colors.DIM)} {format_guid(guid)}")

            # Add spacing every 10 items for readability
            if i % 10 == 0 and i < len(mappings):
                print()


def build_schema_from_pdfs(
    pdf_files: List[Path], output_file: Path, show_stats: bool = False
) -> None:
    """Build enhanced schema from Microsoft AD Schema PDF documents."""
    try:
        # Import PDF parsing functionality
        import sys

        sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))
        from parse_ms_ada_pdfs import MSADAPDFParser
    except ImportError as e:
        print_error(f"Unable to import PDF parsing modules: {e}")
        print_info("Make sure PyMuPDF is installed: uv add pymupdf")
        sys.exit(1)

    # Validate PDF files exist
    missing_files = [f for f in pdf_files if not f.exists()]
    if missing_files:
        print_error("PDF files not found:")
        for f in missing_files:
            print(f"  {f}")
        sys.exit(1)

    print_info(f"Building enhanced AD schema from {len(pdf_files)} PDF file(s)...")

    # Parse PDFs and create enhanced schema directly
    parser = MSADAPDFParser()
    attributes = parser.parse_multiple_pdfs(pdf_files)

    if show_stats:
        print_info(f"Parsed {len(attributes)} attributes from PDFs")

        # Show PDF stats
        pdf_counts = {}
        for attr in attributes.values():
            pdf = attr.source_pdf or "unknown"
            pdf_counts[pdf] = pdf_counts.get(pdf, 0) + 1

        print_info("Attributes per PDF:")
        for pdf, count in sorted(pdf_counts.items()):
            print(f"  {pdf}: {count}")

    # Export directly to enhanced schema format
    parser.export_to_enhanced_json(attributes, output_file)
    print_success(f"Enhanced schema built successfully: {output_file}")


def main() -> None:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="AD Schema Mapping Tool - Convert between GUIDs and attribute names",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  # Build schema from Microsoft PDF documents
  ad-schema-tool build-schema ms-ada1.pdf ms-ada2.pdf ms-ada3.pdf --stats
  
  # Look up attribute name by GUID
  ad-schema-tool lookup-guid bf967944-0de6-11d0-a285-00aa003049e2
  
  # Look up GUID by attribute name (plain output for scripts)
  ad-schema-tool --plain lookup-name cost
  
  # Search for attributes
  ad-schema-tool search msTS
  
  # Find common GUIDs across multiple files
  ad-schema-tool intersect file1.txt file2.txt file3.txt
  
  # Find intersection with attribute names
  ad-schema-tool intersect --annotate file1.txt file2.txt
  
  # Write intersection results to file
  ad-schema-tool intersect --output results.txt file1.txt file2.txt
  
  # List all attributes with plain output
  ad-schema-tool --plain list
""",
    )

    parser.add_argument(
        "--schema-file",
        "-s",
        type=Path,
        default=Path("ad_schema_enhanced.json"),
        help="Path to enhanced schema JSON file",
    )

    parser.add_argument(
        "--plain",
        "-p",
        action="store_true",
        help="Plain output format (no colors/formatting, tab-separated)",
    )

    parser.add_argument(
        "--export",
        "-e",
        choices=["csv", "json", "tsv"],
        help="Export all mappings in specified format",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Lookup GUID command
    lookup_guid_parser = subparsers.add_parser(
        "lookup-guid", help="Look up attribute name by GUID"
    )
    lookup_guid_parser.add_argument("guid", help="Schema GUID to look up")

    # Lookup name command
    lookup_name_parser = subparsers.add_parser(
        "lookup-name", help="Look up GUID by attribute name"
    )
    lookup_name_parser.add_argument("name", help="Attribute name to look up")

    # Search command
    search_parser = subparsers.add_parser("search", help="Search attributes by pattern")
    search_parser.add_argument("pattern", help="Search pattern (case-insensitive)")

    # List command
    subparsers.add_parser("list", help="List all schema attributes")

    # Intersect command
    intersect_parser = subparsers.add_parser(
        "intersect", help="Find common GUIDs across multiple text files"
    )
    intersect_parser.add_argument(
        "files", nargs="+", type=Path, help="Text files containing GUIDs (one per line)"
    )
    intersect_parser.add_argument(
        "--annotate",
        "-a",
        action="store_true",
        help="Show attribute names alongside GUIDs",
    )
    intersect_parser.add_argument(
        "--output", "-o", type=Path, help="Write results to file instead of console"
    )

    # Build schema command
    build_parser = subparsers.add_parser(
        "build-schema", help="Build enhanced schema from Microsoft PDF documents"
    )
    build_parser.add_argument(
        "pdf_files",
        nargs="+",
        type=Path,
        help="Paths to MS-ADA PDF files (MS-ADA1, MS-ADA2, MS-ADA3)",
    )
    build_parser.add_argument(
        "--output",
        "-o",
        type=Path,
        default=Path("ad_schema_enhanced.json"),
        help="Output enhanced schema file (default: ad_schema_enhanced.json)",
    )
    build_parser.add_argument(
        "--stats",
        action="store_true",
        help="Show parsing and building statistics",
    )

    # Export command
    export_parser = subparsers.add_parser("export", help="Export all mappings to file")
    export_parser.add_argument(
        "format", choices=["csv", "json", "tsv"], help="Export format"
    )
    export_parser.add_argument("--output", "-o", type=Path, help="Output filename")

    args = parser.parse_args()

    # Set plain output mode if requested (global option)
    if args.plain:
        set_plain_output(True)

    # Handle export without subcommand
    if args.export and not args.command:
        mappings = load_schema_mappings(args.schema_file)
        export_mappings(mappings, args.export)
        return

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Handle build-schema command separately (doesn't need existing schema)
    if args.command == "build-schema":
        build_schema_from_pdfs(args.pdf_files, args.output, args.stats)
        return

    # Load schema mappings from default file
    mappings = load_schema_mappings(args.schema_file)

    if args.command == "lookup-guid":
        lookup_guid(mappings, args.guid)
    elif args.command == "lookup-name":
        lookup_name(mappings, args.name)
    elif args.command == "search":
        search_pattern(mappings, args.pattern)
    elif args.command == "list":
        list_all(mappings)
    elif args.command == "intersect":
        intersect_files(mappings, args.files, args.annotate, args.output)
    elif args.command == "export":
        export_mappings(mappings, args.format, args.output)


if __name__ == "__main__":
    main()
