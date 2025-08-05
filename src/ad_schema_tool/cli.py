#!/usr/bin/env python3
"""CLI interface for AD Schema Mapping Tool."""

import argparse
import csv
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple


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


def normalize_guid(guid: str) -> str:
    """Normalize GUID format by removing wrapping braces if present.
    
    Args:
        guid: GUID string, optionally wrapped in braces
        
    Returns:
        GUID string without braces
        
    Examples:
        normalize_guid("{12345678-1234-5678-9012-123456789abc}") -> "12345678-1234-5678-9012-123456789abc"
        normalize_guid("12345678-1234-5678-9012-123456789abc") -> "12345678-1234-5678-9012-123456789abc"
    """
    guid = guid.strip()
    if guid.startswith('{') and guid.endswith('}'):
        return guid[1:-1]
    return guid


class SchemaLookup:
    """Centralized schema lookup functionality."""
    
    def __init__(self, mappings: Dict[str, str]):
        self.guid_to_name = mappings
        self._name_to_guid = None
    
    @property
    def name_to_guid(self) -> Dict[str, str]:
        """Lazy-build reverse mapping from name to GUID."""
        if self._name_to_guid is None:
            self._name_to_guid = {v: k for k, v in self.guid_to_name.items()}
        return self._name_to_guid
    
    def lookup_by_guid(self, guid: str) -> Optional[str]:
        """Look up attribute name by GUID.
        
        Args:
            guid: GUID string (with or without braces)
            
        Returns:
            Attribute name if found, None otherwise
        """
        normalized_guid = normalize_guid(guid)
        return self.guid_to_name.get(normalized_guid)
    
    def lookup_by_name(self, name: str) -> Optional[str]:
        """Look up GUID by attribute name.
        
        Args:
            name: Attribute name
            
        Returns:
            GUID string (without braces) if found, None otherwise
        """
        return self.name_to_guid.get(name)
    
    def search_by_pattern(self, pattern: str) -> List[Tuple[str, str]]:
        """Search for attributes matching a pattern.
        
        Args:
            pattern: Search pattern (case-insensitive)
            
        Returns:
            List of (guid, name) tuples matching the pattern
        """
        pattern_lower = pattern.lower()
        return [
            (guid, name) 
            for guid, name in self.guid_to_name.items() 
            if pattern_lower in name.lower()
        ]


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


def lookup_guid(lookup: SchemaLookup, guid: str) -> None:
    """Look up attribute name for a GUID."""
    normalized_guid = normalize_guid(guid)
    name = lookup.lookup_by_guid(guid)
    if name:
        if _PLAIN_OUTPUT:
            print(f"{normalized_guid}\t{name}")
        else:
            print_header("🔍 GUID Lookup Result")
            print(f"  GUID: {format_guid(normalized_guid)}")
            print(f"  Name: {format_attribute_name(name)}")
    else:
        if _PLAIN_OUTPUT:
            print(f"ERROR: GUID {normalized_guid} not found", file=sys.stderr)
        else:
            print_error(f"GUID {format_guid(normalized_guid)} not found in schema mappings")
        sys.exit(1)


def lookup_name(lookup: SchemaLookup, name: str) -> None:
    """Look up GUID for an attribute name."""
    guid = lookup.lookup_by_name(name)
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


def search_pattern(lookup: SchemaLookup, pattern: str) -> None:
    """Search for attributes matching a pattern."""
    matches = lookup.search_by_pattern(pattern)

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
    lookup: SchemaLookup,
    file_paths: list[Path],
    annotate: bool = False,
    output_file: Optional[Path] = None,
) -> None:
    """Find intersection of GUIDs across multiple text files.
    
    This is a wrapper around subset_analysis for backward compatibility.
    """
    if len(file_paths) < 2:
        if _PLAIN_OUTPUT:
            print("ERROR: Need at least 2 files for intersection", file=sys.stderr)
        else:
            print_error("Need at least 2 files for intersection")
        sys.exit(1)
    
    # Use subset_analysis with include_all (intersection logic)
    subset_analysis(
        lookup=lookup,
        include_all=file_paths,
        annotate=annotate,
        output_file=output_file,
        operation_name="GUID Intersection"
    )


def annotate_file(
    lookup: SchemaLookup,
    input_file: Path,
    output_file: Optional[Path] = None,
) -> None:
    """Annotate a file containing GUIDs by adding attribute names.
    
    Args:
        lookup: Schema lookup instance
        input_file: Input file containing GUIDs (one per line)
        output_file: Optional output file, if None writes to stdout
    """
    try:
        with open(input_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except FileNotFoundError:
        if _PLAIN_OUTPUT:
            print(f"ERROR: Input file not found: {input_file}", file=sys.stderr)
        else:
            print_error(f"Input file not found: {colorize(str(input_file), Colors.CYAN)}")
        sys.exit(1)
    except OSError as e:
        if _PLAIN_OUTPUT:
            print(f"ERROR: Cannot read input file {input_file}: {e}", file=sys.stderr)
        else:
            print_error(f"Cannot read input file {colorize(str(input_file), Colors.CYAN)}: {e}")
        sys.exit(1)

    # Process lines and build output
    output_lines = []
    found_count = 0
    total_count = 0
    
    for line in lines:
        line = line.strip()
        if line and not line.startswith("#"):  # Skip empty lines and comments
            total_count += 1
            normalized_guid = normalize_guid(line)
            attribute_name = lookup.lookup_by_guid(normalized_guid)
            
            if attribute_name:
                output_lines.append(f"{normalized_guid}\t{attribute_name}")
                found_count += 1
            else:
                output_lines.append(f"{normalized_guid}\tUnknown")
        elif line:  # Keep comments and empty lines as-is
            output_lines.append(line)
    
    # Write output
    if output_file:
        try:
            with open(output_file, "w", encoding="utf-8") as f:
                for line in output_lines:
                    f.write(f"{line}\n")
            
            if _PLAIN_OUTPUT:
                print(f"Annotated {found_count}/{total_count} GUIDs, wrote to {output_file}")
            else:
                print_success(
                    f"Annotated {format_count(found_count)}/{format_count(total_count)} GUIDs, "
                    f"wrote to {colorize(str(output_file), Colors.CYAN)}"
                )
                
        except OSError as e:
            if _PLAIN_OUTPUT:
                print(f"ERROR: Failed to write output file: {e}", file=sys.stderr)
            else:
                print_error(f"Failed to write output file: {e}")
            sys.exit(1)
    else:
        # Write to stdout
        for line in output_lines:
            print(line)
        
        # Show stats to stderr if not in plain mode
        if not _PLAIN_OUTPUT:
            print_info(f"Annotated {format_count(found_count)}/{format_count(total_count)} GUIDs")


def unique_elements(
    lookup: SchemaLookup,
    file_paths: list[Path],
    annotate: bool = False,
    output_file: Optional[Path] = None,
) -> None:
    """Find elements that are unique to each file (set difference analysis).
    
    This function performs multiple subset analyses to find elements unique to each file.
    """
    if len(file_paths) < 2:
        if _PLAIN_OUTPUT:
            print("ERROR: Need at least 2 files for unique analysis", file=sys.stderr)
        else:
            print_error("Need at least 2 files for unique analysis")
        sys.exit(1)

    # Collect results for each file
    all_unique_results = []
    total_unique = 0
    
    for i, current_file in enumerate(file_paths):
        # Get all other files to exclude
        other_files = [file_paths[j] for j in range(len(file_paths)) if j != i]
        
        # Use subset_analysis to find elements unique to current file
        # We'll capture the results by temporarily redirecting to a temp approach
        # For now, let's use the original logic but simplified
        
        try:
            with open(current_file, "r", encoding="utf-8") as f:
                current_guids = set()
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        normalized_guid = normalize_guid(line)
                        current_guids.add(normalized_guid)
        except FileNotFoundError:
            if _PLAIN_OUTPUT:
                print(f"ERROR: File not found: {current_file}", file=sys.stderr)
            else:
                print_error(f"File not found: {colorize(str(current_file), Colors.CYAN)}")
            sys.exit(1)
        except OSError as e:
            if _PLAIN_OUTPUT:
                print(f"ERROR: Cannot read file {current_file}: {e}", file=sys.stderr)
            else:
                print_error(f"Cannot read file {colorize(str(current_file), Colors.CYAN)}: {e}")
            sys.exit(1)
        
        # Get union of all other files
        other_guids = set()
        for other_file in other_files:
            try:
                with open(other_file, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#"):
                            normalized_guid = normalize_guid(line)
                            other_guids.add(normalized_guid)
            except (FileNotFoundError, OSError):
                continue  # Error handling was done above
        
        # Find unique elements
        unique_to_current = current_guids - other_guids
        if unique_to_current:
            all_unique_results.append((current_file.name, unique_to_current))
            total_unique += len(unique_to_current)

    # Generate output
    if total_unique == 0:
        if not output_file:
            if _PLAIN_OUTPUT:
                print("No unique GUIDs found in any file", file=sys.stderr)
            else:
                print_error("No unique GUIDs found in any file")
        return

    # Prepare output lines
    output_lines = []
    if output_file or _PLAIN_OUTPUT:
        # File/plain format
        for file_name, unique_guids in all_unique_results:
            output_lines.append(f"# Elements unique to {file_name} ({len(unique_guids)} items)")
            for guid in sorted(unique_guids):
                if annotate:
                    name = lookup.lookup_by_guid(guid) or "Unknown"
                    output_lines.append(f"{guid}\t{name}")
                else:
                    output_lines.append(guid)
            output_lines.append("")  # Empty line between sections

    # Write to file if specified
    if output_file:
        try:
            with open(output_file, "w", encoding="utf-8") as f:
                for line in output_lines:
                    f.write(f"{line}\n")

            if _PLAIN_OUTPUT:
                print(f"Wrote {total_unique} unique GUIDs to {output_file}")
            else:
                print_success(
                    f"Wrote {format_count(total_unique)} unique GUIDs to {colorize(str(output_file), Colors.CYAN)}"
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
    elif not output_file:  # Fancy output
        print_header(
            "🔍 Unique GUID Analysis",
            f"Found {format_count(total_unique)} unique GUIDs across {len(file_paths)} files",
        )

        # Show results per file
        for file_name, unique_guids in all_unique_results:
            print(colorize(f"Elements unique to {file_name} ({len(unique_guids)} items):", Colors.BOLD))
            for i, guid in enumerate(sorted(unique_guids), 1):
                if annotate:
                    name = lookup.lookup_by_guid(guid) or "Unknown"
                    print(
                        f"  {colorize(f'{i:3}.', Colors.GRAY)} {format_guid(guid)} {colorize('→', Colors.DIM)} {format_attribute_name(name)}"
                    )
                else:
                    print(f"  {colorize(f'{i:3}.', Colors.GRAY)} {format_guid(guid)}")
            print()


def subset_analysis(
    lookup: SchemaLookup,
    include_all: Optional[List[Path]] = None,
    include_any: Optional[List[Path]] = None,
    exclude: Optional[List[Path]] = None,
    annotate: bool = False,
    output_file: Optional[Path] = None,
    operation_name: str = "Subset Analysis",
) -> None:
    """Universal set analysis function supporting include/exclude operations.
    
    Args:
        lookup: Schema lookup instance
        include_all: Files where GUIDs must be present in ALL (intersection)
        include_any: Files where GUIDs must be present in ANY (union)  
        exclude: Files where GUIDs must NOT be present
        annotate: Whether to show attribute names alongside GUIDs
        output_file: Optional file to write results to
        operation_name: Name for headers/output (e.g. "Intersection", "Unique Analysis")
    """
    include_all = include_all or []
    include_any = include_any or []
    exclude = exclude or []
    
    all_files = include_all + include_any + exclude
    if len(all_files) < 1:
        if _PLAIN_OUTPUT:
            print("ERROR: Need at least 1 file for analysis", file=sys.stderr)
        else:
            print_error("Need at least 1 file for analysis")
        sys.exit(1)

    # Read GUIDs from all files
    file_data = {}  # filename -> set of GUIDs
    
    for file_path in all_files:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                guids = set()
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):  # Skip empty lines and comments
                        normalized_guid = normalize_guid(line)
                        guids.add(normalized_guid)
                file_data[file_path.name] = guids

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
                print_error(f"Cannot read file {colorize(str(file_path), Colors.CYAN)}: {e}")
            sys.exit(1)

    # Build include set
    include_set = set()
    
    if include_all:
        # Intersection: must be in ALL include_all files
        include_set = file_data[include_all[0].name].copy()
        for file_path in include_all[1:]:
            include_set = include_set.intersection(file_data[file_path.name])
    
    if include_any:
        # Union: must be in ANY include_any files
        any_set = set()
        for file_path in include_any:
            any_set = any_set.union(file_data[file_path.name])
        
        if include_all:
            # Both include_all and include_any: intersection of (include_all result) and (include_any union)
            include_set = include_set.intersection(any_set)
        else:
            # Only include_any: just the union
            include_set = any_set
    
    # Build exclude set (union of all exclude files)
    exclude_set = set()
    for file_path in exclude:
        exclude_set = exclude_set.union(file_data[file_path.name])
    
    # Final result: include_set - exclude_set
    result_set = include_set - exclude_set

    # Prepare output
    if not result_set:
        if not output_file:
            if _PLAIN_OUTPUT:
                print("No GUIDs found matching criteria", file=sys.stderr)
            else:
                print_error("No GUIDs found matching the specified criteria")
        return

    # Generate output content
    output_lines = []
    if output_file or _PLAIN_OUTPUT:
        # Simple format for files and plain output
        for guid in sorted(result_set):
            if annotate:
                name = lookup.lookup_by_guid(guid) or "Unknown"
                output_lines.append(f"{guid}\t{name}")
            else:
                output_lines.append(guid)
    else:
        # Store for fancy console output  
        output_lines = [(guid, lookup.lookup_by_guid(guid) or "Unknown") for guid in sorted(result_set)]

    # Write to file if specified
    if output_file:
        try:
            with open(output_file, "w", encoding="utf-8") as f:
                for line in output_lines:
                    f.write(f"{line}\n")

            if _PLAIN_OUTPUT:
                print(f"Wrote {len(result_set)} GUIDs to {output_file}")
            else:
                print_success(
                    f"Wrote {format_count(len(result_set))} GUIDs to {colorize(str(output_file), Colors.CYAN)}"
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
            f"🔍 {operation_name} Results",
            f"Found {format_count(len(result_set))} GUIDs matching criteria",
        )

        # Show operation details
        print(colorize("Operation:", Colors.DIM))
        if include_all:
            file_names = [f.name for f in include_all]
            print(f"  Include (ALL): {', '.join(file_names)}")
        if include_any:
            file_names = [f.name for f in include_any]  
            print(f"  Include (ANY): {', '.join(file_names)}")
        if exclude:
            file_names = [f.name for f in exclude]
            print(f"  Exclude: {', '.join(file_names)}")
        print()

        # Show results
        for i, item in enumerate(output_lines, 1):
            if annotate:
                guid, name = item
                print(
                    f"  {colorize(f'{i:3}.', Colors.GRAY)} {format_guid(guid)} {colorize('→', Colors.DIM)} {format_attribute_name(name)}"
                )
            else:
                guid, name = item
                print(f"  {colorize(f'{i:3}.', Colors.GRAY)} {format_guid(guid)}")

            # Add spacing every 5 items for readability
            if i % 5 == 0 and i < len(output_lines):
                print()


def list_all(lookup: SchemaLookup) -> None:
    """List all schema attributes."""
    mappings = lookup.guid_to_name
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
  
  # Annotate a file with GUIDs by adding attribute names
  ad-schema-tool annotate guids.txt --output annotated.txt
  
  # Find GUIDs that are unique to each file
  ad-schema-tool unique file1.txt file2.txt file3.txt --output unique_analysis.txt
  
  # Advanced set operations: GUIDs in A and B, but not in C
  ad-schema-tool subset --include fileA.txt fileB.txt --exclude fileC.txt
  
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

    # Annotate command
    annotate_parser = subparsers.add_parser(
        "annotate", help="Annotate a file containing GUIDs by adding attribute names"
    )
    annotate_parser.add_argument(
        "input_file", type=Path, help="Input file containing GUIDs (one per line)"
    )
    annotate_parser.add_argument(
        "--output", "-o", type=Path, help="Output file for annotated results (default: stdout)"
    )

    # Unique elements command
    unique_parser = subparsers.add_parser(
        "unique", help="Find GUIDs that are unique to each input file"
    )
    unique_parser.add_argument(
        "files", nargs="+", type=Path, help="Text files containing GUIDs (one per line)"
    )
    unique_parser.add_argument(
        "--annotate",
        "-a",
        action="store_true",
        help="Show attribute names alongside GUIDs",
    )
    unique_parser.add_argument(
        "--output", "-o", type=Path, help="Write results to file instead of console"
    )

    # Subset analysis command  
    subset_parser = subparsers.add_parser(
        "subset", help="Advanced set operations with include/exclude logic"
    )
    subset_parser.add_argument(
        "--include",
        nargs="+",
        type=Path,
        help="Files where GUIDs must be present in ALL (intersection)",
    )
    subset_parser.add_argument(
        "--include-any", 
        nargs="+",
        type=Path,
        help="Files where GUIDs must be present in ANY (union)",
    )
    subset_parser.add_argument(
        "--exclude",
        nargs="+", 
        type=Path,
        help="Files where GUIDs must NOT be present",
    )
    subset_parser.add_argument(
        "--annotate",
        "-a",
        action="store_true",
        help="Show attribute names alongside GUIDs",
    )
    subset_parser.add_argument(
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
    lookup = SchemaLookup(mappings)

    if args.command == "lookup-guid":
        lookup_guid(lookup, args.guid)
    elif args.command == "lookup-name":
        lookup_name(lookup, args.name)
    elif args.command == "search":
        search_pattern(lookup, args.pattern)
    elif args.command == "list":
        list_all(lookup)
    elif args.command == "intersect":
        intersect_files(lookup, args.files, args.annotate, args.output)
    elif args.command == "annotate":
        annotate_file(lookup, args.input_file, args.output)
    elif args.command == "unique":
        unique_elements(lookup, args.files, args.annotate, args.output)
    elif args.command == "subset":
        # Validate that at least one include option is provided
        if not args.include and not args.include_any:
            if _PLAIN_OUTPUT:
                print("ERROR: Must specify at least one of --include or --include-any", file=sys.stderr)
            else:
                print_error("Must specify at least one of --include or --include-any")
            sys.exit(1)
        
        subset_analysis(
            lookup=lookup,
            include_all=args.include,
            include_any=args.include_any, 
            exclude=args.exclude,
            annotate=args.annotate,
            output_file=args.output,
            operation_name="Subset Analysis"
        )
    elif args.command == "export":
        export_mappings(mappings, args.format, args.output)


if __name__ == "__main__":
    main()
