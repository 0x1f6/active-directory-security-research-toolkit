# AD Schema Tool - User Guide

Complete guide for using the `ad-schema-tool` command-line utility.

## Quick Start

```bash
# Install the tool
uv pip install -e .

# Basic lookup examples
ad-schema-tool lookup-guid bf967944-0de6-11d0-a285-00aa003049e2
ad-schema-tool lookup-name cost
ad-schema-tool search msTS

# New: Find common GUIDs across multiple files
ad-schema-tool intersect file1.txt file2.txt --annotate
```

## Commands Overview

| Command | Purpose | Example |
|---------|---------|---------|
| `lookup-guid` | Get attribute name from GUID | `ad-schema-tool lookup-guid <guid>` |
| `lookup-name` | Get GUID from attribute name | `ad-schema-tool lookup-name cost` |
| `search` | Find attributes by pattern | `ad-schema-tool search msTS` |
| `list` | Show all attributes | `ad-schema-tool list` |
| **`intersect`** | **Find common GUIDs across files** | `ad-schema-tool intersect file1.txt file2.txt` |
| `export` | Export all mappings to file | `ad-schema-tool export csv --output file.csv` |

## Output Modes

**Interactive Mode (default):** Colorized, formatted output with headers, icons, and visual structure - perfect for manual use.

**Plain Mode (`--plain`):** Tab-separated values without colors or formatting - ideal for scripting and automation.

## Detailed Command Reference

### lookup-guid

Convert a schema GUID to its human-readable attribute name.

```bash
# Interactive mode (colorized output)
ad-schema-tool lookup-guid bf967944-0de6-11d0-a285-00aa003049e2
# Output: 
# ┌─ 🔍 GUID Lookup Result
# └─
#   GUID: bf967944-0de6-11d0-a285-00aa003049e2
#   Name: cost

# Plain mode (tab-separated for scripts)
ad-schema-tool --plain lookup-guid bf967944-0de6-11d0-a285-00aa003049e2
# Output: bf967944-0de6-11d0-a285-00aa003049e2	cost
```

**Use cases:**
- Analyzing AD logs with GUIDs
- Reverse-engineering schema references
- Converting technical identifiers to readable names

### lookup-name

Convert an attribute name to its schema GUID.

```bash
# Interactive mode
ad-schema-tool lookup-name cost
# Output:
# ┌─ 🔍 Name Lookup Result
# └─
#   Name: cost
#   GUID: bf967944-0de6-11d0-a285-00aa003049e2

# Plain mode
ad-schema-tool --plain lookup-name cost
# Output: cost	bf967944-0de6-11d0-a285-00aa003049e2
```

**Use cases:**
- Finding schema GUIDs for scripting
- Technical documentation
- Cross-referencing different AD tools

### search

Find attributes matching a pattern (case-insensitive).

```bash
# Interactive mode (formatted, numbered list)
ad-schema-tool search msTS
# Output:
# ┌─ 🔎 Search Results
# │  Found 38 attributes matching 'msTS'
# └─
#     1. msTSAllowLogon
#        GUID: 3a0cd464-bc54-40e7-93ae-a646a6ecc4b4
#     2. msTSBrokenConnectionAction
#        GUID: 1cf41bba-5604-463e-94d6-1a1287b72ca3
#     ...

# Plain mode (tab-separated)
ad-schema-tool --plain search msTS
# Output:
# msTSAllowLogon	3a0cd464-bc54-40e7-93ae-a646a6ecc4b4
# msTSBrokenConnectionAction	1cf41bba-5604-463e-94d6-1a1287b72ca3
# ...
```

**Common search patterns:**
- `ms` - Microsoft-specific attributes
- `msTS` - Terminal Services attributes  
- `msDS` - Directory Services attributes
- `msExch` - Exchange Server attributes
- `user` - User-related attributes

### intersect (NEW)

Find common GUIDs across multiple text files containing GUID lists.

```bash
# Basic intersection (GUIDs only)
ad-schema-tool intersect file1.txt file2.txt file3.txt
# Output:
# ┌─ 🔍 GUID Intersection Results
# │  Found 5 common GUIDs across 3 files
# └─
# Files analyzed:
#   1. file1.txt (25 GUIDs)
#   2. file2.txt (18 GUIDs)
#   3. file3.txt (32 GUIDs)
# 
#     1. bf967944-0de6-11d0-a285-00aa003049e2
#     2. bf967a68-0de6-11d0-a285-00aa003049e2
#     ...

# With attribute names (--annotate)
ad-schema-tool intersect --annotate file1.txt file2.txt
# Output:
# ┌─ 🔍 GUID Intersection Results
# │  Found 2 common GUIDs across 2 files
# └─
#     1. bf967944-0de6-11d0-a285-00aa003049e2 → cost
#     2. bf967a68-0de6-11d0-a285-00aa003049e2 → userAccountControl

# Write results to file
ad-schema-tool intersect --output common.txt file1.txt file2.txt
# Creates common.txt with intersection results

# Plain mode (for automation)
ad-schema-tool --plain intersect --annotate file1.txt file2.txt
# Output:
# bf967944-0de6-11d0-a285-00aa003049e2	cost
# bf967a68-0de6-11d0-a285-00aa003049e2	userAccountControl
```

**File Format:**
Text files with one GUID per line:
```
# Comments start with #
bf967944-0de6-11d0-a285-00aa003049e2
bf967a68-0de6-11d0-a285-00aa003049e2
bf9679c0-0de6-11d0-a285-00aa003049e2
```

**Use cases:**
- Compare attribute sets from different AD environments
- Find common attributes between security tools
- Analyze overlapping GUID collections
- Security research and correlation

### list

Display all available schema attributes.

```bash
# Interactive mode (formatted with numbering)
ad-schema-tool list | head -15
# Output:
# ┌─ 📚 All AD Schema Attributes
# │  Showing all 1499 available attributes
# └─
# ℹ 💡 Tip: Pipe to 'less' for easier browsing: ad-schema-tool list | less
#      1. Enabled
#         GUID: a8df73f2-c5ea-11d1-bbcb-0080c76670c0
#      2. MSMQ-MulticastAddress
#         GUID: 1d2f4412-f10d-4337-9b48-6e5b125cd265
#      ...

# Plain mode (tab-separated, no headers)
ad-schema-tool --plain list | head -5
# Output:
# Enabled	a8df73f2-c5ea-11d1-bbcb-0080c76670c0
# MSMQ-MulticastAddress	1d2f4412-f10d-4337-9b48-6e5b125cd265
# ...
```

**Tip:** Use with `grep`, `head`, or `tail` for filtering:
```bash
ad-schema-tool list | grep -i exchange
ad-schema-tool list | wc -l  # Count total attributes
```

### export

Export all schema mappings to various file formats.

```bash
# Export to CSV (Excel-compatible)
ad-schema-tool export csv --output ad_mappings.csv

# Export to JSON (API-ready format)
ad-schema-tool export json --output ad_mappings.json

# Export to TSV (database import format)
ad-schema-tool export tsv --output ad_mappings.tsv

# Auto-generate filename if not specified
ad-schema-tool export csv  # Creates ad_schema_attributes.csv
```

## Advanced Usage

### Custom Schema File

By default, the tool uses the built-in enhanced schema. You can specify a custom file:

```bash
ad-schema-tool --schema-file /path/to/custom_schema.json lookup-guid <guid>
```

### GUID List Analysis

Create and analyze GUID lists for intersection analysis:

```bash
# Create GUID lists (one GUID per line)
echo "bf967944-0de6-11d0-a285-00aa003049e2" > user_attrs.txt
echo "bf967a68-0de6-11d0-a285-00aa003049e2" >> user_attrs.txt

echo "bf967944-0de6-11d0-a285-00aa003049e2" > security_attrs.txt  
echo "bf9679e3-0de6-11d0-a285-00aa003049e2" >> security_attrs.txt

# Find common attributes with names
ad-schema-tool intersect --annotate --output common_attrs.tsv user_attrs.txt security_attrs.txt

# Extract just the attribute names from intersection
ad-schema-tool --plain intersect --annotate user_attrs.txt security_attrs.txt | cut -f2
```

### Piping and Filtering

The tool works well with standard Unix tools:

```bash
# Count Terminal Services attributes (plain mode recommended)
ad-schema-tool --plain search msTS | wc -l

# Save search results to file  
ad-schema-tool --plain search msExch > exchange_attributes.txt

# Find attributes containing "password"
ad-schema-tool --plain search password | grep -i managed

# Extract just the attribute names
ad-schema-tool --plain list | cut -f1 | sort

# Find intersection and get only names
ad-schema-tool --plain intersect --annotate file1.txt file2.txt | cut -f2 > common_names.txt
```

### Batch Processing

Process multiple GUIDs from a file:

```bash
# Create a file with GUIDs (one per line)
cat > guids.txt << EOF
bf967944-0de6-11d0-a285-00aa003049e2
bf967a68-0de6-11d0-a285-00aa003049e2
bf9679c0-0de6-11d0-a285-00aa003049e2
EOF

# Process each GUID (plain mode for scripting)
while read guid; do
  ad-schema-tool --plain lookup-guid "$guid"
done < guids.txt

# Create a mapping file
while read guid; do
  ad-schema-tool --plain lookup-guid "$guid" >> guid_mappings.tsv
done < guids.txt

# More efficient: export first, then filter
ad-schema-tool export tsv --output all_mappings.tsv
grep -f guids.txt all_mappings.tsv
```

## Common Use Cases

### Security Analysis

**Analyzing AD audit logs:**
```bash
# Convert GUIDs from logs to readable names
ad-schema-tool lookup-guid 9a9a021e-4a5b-11d1-a9c3-0000f80367c1
# Output: lastLogonTimestamp
```

**Finding sensitive attributes:**
```bash
ad-schema-tool search password
ad-schema-tool search credential  
ad-schema-tool search secret
ad-schema-tool search token
```

**Comparing attribute sets from different environments:**
```bash
# Export attributes from production environment
ad-schema-tool --plain list > prod_attributes.txt

# Compare with test environment attributes
ad-schema-tool intersect --annotate prod_attributes.txt test_attributes.txt
```

### Detection Engineering

**Finding monitoring targets:**
```bash
# Find all user-related attributes for detection rules
ad-schema-tool --plain search user | grep -E "(logon|password|account)" > critical_user_attrs.txt

# Export Terminal Services attributes for monitoring
ad-schema-tool --plain search msTS > ts_attributes_for_monitoring.txt

# Find authentication-related attributes
ad-schema-tool --plain search logon > logon_attributes.txt
```

**SIEM correlation development:**
```bash
# Find common attributes across multiple security tools
ad-schema-tool intersect \
  --annotate \
  --output siem_correlation_attrs.tsv \
  windows_events.txt \
  sysmon_logs.txt \
  security_tools.txt
```

### Documentation and Research

**Catalog AD schema extensions:**
```bash
# Find all Microsoft extensions
ad-schema-tool --plain search ms | wc -l

# List all Terminal Services settings
ad-schema-tool search msTS > terminal_services_complete.txt

# Find vendor-specific attributes
ad-schema-tool search oracle > oracle_attributes.txt
ad-schema-tool search vmware > vmware_attributes.txt
```

**Generate attribute listings:**
```bash
# Create comprehensive attribute list
ad-schema-tool export csv --output comprehensive_ad_attributes.csv

# Generate summary by prefix
for prefix in ms msDS msTS msExch; do
  count=$(ad-schema-tool --plain search $prefix | wc -l)
  echo "$prefix: $count attributes"
done
```

### Development and Scripting

**Schema validation in scripts:**
```bash
#!/bin/bash
GUID="bf967944-0de6-11d0-a285-00aa003049e2"

# Use plain mode for reliable parsing
ATTR_NAME=$(ad-schema-tool --plain lookup-guid "$GUID" | cut -f2)
echo "Processing attribute: $ATTR_NAME"

# Check if attribute exists
if ad-schema-tool --plain lookup-name "userAccountControl" > /dev/null 2>&1; then
    echo "Attribute exists in schema"
else
    echo "Attribute not found"
fi

# Validate GUID list
while read guid; do
    if ad-schema-tool --plain lookup-guid "$guid" > /dev/null 2>&1; then
        echo "$guid: Valid"
    else
        echo "$guid: Invalid" >&2
    fi
done < guid_list.txt
```

**Data analysis and reporting:**
```bash
# Generate CSV report of all Terminal Services attributes
ad-schema-tool --plain search msTS | \
  awk -F'\t' 'BEGIN{print "AttributeName,GUID"} {print $1","$2}' > \
  terminal_services_attributes.csv

# Create summary statistics
echo "Total AD schema attributes: $(ad-schema-tool --plain list | wc -l)"
echo "Microsoft-specific: $(ad-schema-tool --plain search ms | wc -l)"
echo "Terminal Services: $(ad-schema-tool --plain search msTS | wc -l)"
echo "Exchange: $(ad-schema-tool --plain search msExch | wc -l)"

# Find common attributes between different categories
ad-schema-tool --plain search user > user_related.txt
ad-schema-tool --plain search security > security_related.txt
ad-schema-tool --plain intersect --annotate user_related.txt security_related.txt > user_security_overlap.txt
echo "User+Security overlap: $(wc -l < user_security_overlap.txt) attributes"
```

**Integration with other tools:**
```bash
# Export for Excel analysis
ad-schema-tool export csv --output ad_analysis.csv

# Create GUID validation function
validate_guid() {
    local guid="$1"
    if ad-schema-tool --plain lookup-guid "$guid" > /dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

# Use in larger scripts
if validate_guid "bf967944-0de6-11d0-a285-00aa003049e2"; then
    echo "GUID is valid AD schema attribute"
fi
```

## Tips and Best Practices

### Performance
- The tool loads schema data once per command - very fast lookups
- For repeated operations, consider exporting to a file first
- Use plain mode for better performance in scripts

### Pattern Matching
- Search is case-insensitive: `msds` matches `msDS-`
- Use partial matches: `logon` finds `lastLogon`, `logonCount`, etc.
- No wildcards needed - simple substring matching

### GUID List Management
- One GUID per line in text files
- Comments supported with `#` prefix
- Empty lines are ignored
- Use descriptive filenames: `user_attrs.txt`, `security_attrs.txt`

### Error Handling
- Invalid GUIDs return clear error messages
- Unknown attribute names exit with status code 1
- Empty search results are handled gracefully
- Intersection with no results shows appropriate message

### Integration
- Tool returns proper exit codes for scripting
- Plain mode provides consistent tab-separated output
- Interactive mode offers user-friendly formatted display
- Export functions provide data in standard formats (CSV/JSON/TSV)
- Works well in pipelines with other Unix tools

## Troubleshooting

### Common Issues

**Command not found:**
```bash
# Make sure the package is installed
uv pip install -e .

# Or use with uv run
uv run ad-schema-tool lookup-name cost
```

**Schema file not found:**
```bash
# Check if enhanced schema file exists
ls ad_schema_enhanced.json

# Use custom schema file if needed
ad-schema-tool --schema-file /path/to/schema.json lookup-name cost
```

**No results for valid attribute:**
- Schema data might be incomplete
- Try case-insensitive search instead: `ad-schema-tool search <partial-name>`
- Verify the attribute exists: `ad-schema-tool --plain list | grep -i <name>`

**Intersection returns no results:**
- Check GUID format in input files
- Verify files contain valid GUIDs
- Test with smaller known GUID sets first

### Getting Help

```bash
# Show general help
ad-schema-tool --help

# Show help for specific commands
ad-schema-tool lookup-guid --help
ad-schema-tool search --help
ad-schema-tool intersect --help
ad-schema-tool export --help
```

## Integration Examples

### Shell Scripting

```bash
#!/bin/bash
# AD Schema Analysis Script

# Configuration
SCHEMA_FILE="ad_schema_enhanced.json"
OUTPUT_DIR="analysis_results"
mkdir -p "$OUTPUT_DIR"

# Generate various attribute lists
echo "Generating attribute analysis..."

# Critical security attributes
ad-schema-tool --plain search password > "$OUTPUT_DIR/password_attrs.txt"
ad-schema-tool --plain search logon > "$OUTPUT_DIR/logon_attrs.txt"
ad-schema-tool --plain search credential > "$OUTPUT_DIR/credential_attrs.txt"

# Find overlaps
ad-schema-tool intersect \
  --annotate \
  --output "$OUTPUT_DIR/security_overlap.tsv" \
  "$OUTPUT_DIR/password_attrs.txt" \
  "$OUTPUT_DIR/logon_attrs.txt" \
  "$OUTPUT_DIR/credential_attrs.txt"

# Generate summary
echo "Security Attribute Analysis Summary" > "$OUTPUT_DIR/summary.txt"
echo "====================================" >> "$OUTPUT_DIR/summary.txt"
echo "Password-related: $(wc -l < "$OUTPUT_DIR/password_attrs.txt")" >> "$OUTPUT_DIR/summary.txt"
echo "Logon-related: $(wc -l < "$OUTPUT_DIR/logon_attrs.txt")" >> "$OUTPUT_DIR/summary.txt"
echo "Credential-related: $(wc -l < "$OUTPUT_DIR/credential_attrs.txt")" >> "$OUTPUT_DIR/summary.txt"
echo "Common across all: $(wc -l < "$OUTPUT_DIR/security_overlap.tsv")" >> "$OUTPUT_DIR/summary.txt"

echo "Analysis complete. Results in $OUTPUT_DIR/"
```

### Python Integration

```python
#!/usr/bin/env python3
"""Example Python integration with ad-schema-tool."""

import subprocess
import json
from pathlib import Path

def lookup_guid(guid: str) -> str:
    """Look up attribute name for GUID using ad-schema-tool."""
    try:
        result = subprocess.run([
            'ad-schema-tool', '--plain', 'lookup-guid', guid
        ], capture_output=True, text=True, check=True)
        return result.stdout.strip().split('\t')[1]
    except subprocess.CalledProcessError:
        return None

def find_intersection(files: list[str], annotate: bool = False) -> list[str]:
    """Find GUID intersection using ad-schema-tool."""
    cmd = ['ad-schema-tool', '--plain', 'intersect']
    if annotate:
        cmd.append('--annotate')
    cmd.extend(files)
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return result.stdout.strip().split('\n')
    except subprocess.CalledProcessError:
        return []

# Example usage
guid = "bf967944-0de6-11d0-a285-00aa003049e2"
attr_name = lookup_guid(guid)
print(f"GUID {guid} -> {attr_name}")

# Find intersection
intersection = find_intersection(['file1.txt', 'file2.txt'], annotate=True)
print(f"Found {len(intersection)} common attributes")
```

## Data Format Reference

### Enhanced Schema JSON Structure

The tool uses an enhanced JSON format with rich metadata:

```json
{
  "bf967a68-0de6-11d0-a285-00aa003049e2": {
    "cn": "User-Account-Control",
    "ldapDisplayName": "userAccountControl",
    "documentationUrl": "https://learn.microsoft.com/en-us/...",
    "implementedSince": "Windows 2000",
    "isSingleValued": true,
    "systemOnly": false,
    "ldapOid": "1.2.840.113556.1.4.8",
    "omSyntax": 2,
    "syntax": "2.5.5.9",
    "systemFlags": "FLAG_SCHEMA_BASE_OBJECT",
    "searchFlags": "fATTINDEX",
    "attributeSecurityGuid": "e48d0154-bcf8-11d1-8702-00c04fb96050",
    "isMemberOfPartialAttributeSet": true,
    "schemaFlagsEx": "FLAG_ATTR_IS_CRITICAL"
  }
}
```

### Export Formats

**CSV Format:**
```csv
GUID,AttributeName
bf967944-0de6-11d0-a285-00aa003049e2,cost
bf967a68-0de6-11d0-a285-00aa003049e2,userAccountControl
```

**TSV Format:**
```tsv
GUID	AttributeName
bf967944-0de6-11d0-a285-00aa003049e2	cost
bf967a68-0de6-11d0-a285-00aa003049e2	userAccountControl
```

**JSON Format:**
```json
{
  "bf967944-0de6-11d0-a285-00aa003049e2": "cost",
  "bf967a68-0de6-11d0-a285-00aa003049e2": "userAccountControl"
}
```

## Quick Reference Card

### Essential Commands
```bash
# Lookups
ad-schema-tool lookup-guid <guid>
ad-schema-tool lookup-name <name>

# Search
ad-schema-tool search <pattern>
ad-schema-tool list

# Intersection (NEW)
ad-schema-tool intersect file1.txt file2.txt
ad-schema-tool intersect --annotate --output results.txt file1.txt file2.txt

# Export
ad-schema-tool export csv --output mappings.csv
```

### Useful Flags
- `--plain` - Tab-separated output for scripts
- `--annotate` - Show attribute names with GUIDs  
- `--output file` - Write results to file
- `--schema-file file` - Use custom schema file

### Common Patterns
```bash
# Count results
ad-schema-tool --plain search ms | wc -l

# Save to file
ad-schema-tool --plain search msTS > ts_attrs.txt

# Extract names only
ad-schema-tool --plain intersect --annotate file1.txt file2.txt | cut -f2

# Validate GUID
ad-schema-tool lookup-guid <guid> > /dev/null 2>&1 && echo "Valid"
```