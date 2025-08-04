# Security Research Toolkit

A defensive security research toolkit focused on Active Directory schema analysis and attribute mapping.

## Overview

This toolkit provides comprehensive tools for analyzing and working with Active Directory schema attributes, with enhanced metadata extracted directly from Microsoft's official PDF documentation. The main component is `ad-schema-tool`, a powerful CLI utility for schema attribute research and analysis.

## Features

### AD Schema Mapping Tool (`ad-schema-tool`)

Complete CLI tool for working with Active Directory schema attribute mappings:

**Core Functions:**
- **Build schema** from Microsoft PDF documents (MS-ADA1, MS-ADA2, MS-ADA3)
- Look up attribute names by schema GUID
- Look up schema GUIDs by attribute name  
- Search attributes by pattern matching
- List all available schema attributes
- **Find common attributes** across multiple GUID lists (intersect)
- Export mappings to CSV, JSON, or TSV formats

**Output Modes:**
- **Interactive**: Colorized, formatted output with headers and icons
- **Plain**: Tab-separated values for scripting and automation  

## Installation

### Prerequisites

- Python 3.12 or higher
- [uv](https://docs.astral.sh/uv/) package manager

### Install the package

```bash
# Clone the repository
git clone <repository-url>
cd security-research-toolkit

# Install dependencies
uv sync

# Install in development mode
uv pip install -e .
```

## Usage

### Quick Start

1. **Download Microsoft PDF documents** (MS-ADA1, MS-ADA2, MS-ADA3) from Microsoft Learn
2. **Build your schema database:**
   ```bash
   ad-schema-tool build-schema ms-ada1.pdf ms-ada2.pdf ms-ada3.pdf --stats
   ```
3. **Start using the tool:**
   ```bash
   ad-schema-tool search password
   ```

### Command Line Interface

#### Building Schema from PDFs

First, download the Microsoft AD Schema PDF documents and build your schema:

```bash
# Download MS-ADA1, MS-ADA2, MS-ADA3 PDFs from Microsoft Learn
# https://learn.microsoft.com/en-us/openspecs/windows_protocols/ms-ada1/
# https://learn.microsoft.com/en-us/openspecs/windows_protocols/ms-ada2/
# https://learn.microsoft.com/en-us/openspecs/windows_protocols/ms-ada3/

# Build enhanced schema database:
ad-schema-tool build-schema ms-ada1.pdf ms-ada2.pdf ms-ada3.pdf --stats
```

This creates `ad_schema_enhanced.json` with 1500+ attributes and comprehensive metadata.

#### Basic Lookups
```bash
# Look up attribute name by GUID
ad-schema-tool lookup-guid bf967944-0de6-11d0-a285-00aa003049e2

# Look up GUID by attribute name  
ad-schema-tool lookup-name cost

# Search for attributes matching a pattern
ad-schema-tool search msTS

# List all available attributes
ad-schema-tool list
```

#### GUID List Intersection
```bash
# Find common GUIDs across multiple text files
ad-schema-tool intersect file1.txt file2.txt file3.txt

# Find intersection with attribute names
ad-schema-tool intersect --annotate file1.txt file2.txt

# Write intersection results to file
ad-schema-tool intersect --output results.txt file1.txt file2.txt
```

#### Plain Output Mode (for scripts)
```bash
# Tab-separated output for scripting
ad-schema-tool --plain lookup-guid bf967944-0de6-11d0-a285-00aa003049e2
ad-schema-tool --plain search password | grep -i managed
ad-schema-tool --plain list | wc -l

# Use intersect for automation
ad-schema-tool --plain intersect --annotate file1.txt file2.txt | cut -f2
```

#### Export Functions
```bash
# Export all mappings to CSV
ad-schema-tool export csv --output ad_mappings.csv

# Export to JSON format
ad-schema-tool export json --output ad_mappings.json

# Export to TSV (tab-separated values)
ad-schema-tool export tsv --output ad_mappings.tsv
```

## Data Source

The toolkit uses an **enhanced AD schema** with rich metadata extracted from Microsoft's official PDF documentation:

### Enhanced JSON Format
- **1500+ AD schema attributes** from Microsoft documentation (MS-ADA1-3)
- **Complete technical metadata**: cn, attributeId, attributeSyntax, omSyntax, etc.
- **Advanced properties**: systemFlags, searchFlags, rangeLower/Upper, mapiID
- **Security information**: attributeSecurityGuid, isMemberOfPartialAttributeSet
- **Boolean/numeric types**: Properly typed JSON data

### Data File
```
ad_schema_enhanced.json             # Enhanced schema data (created by build-schema)
```

Example enhanced attribute entry:
```json
{
  "bf967a0e-0de6-11d0-a285-00aa003049e2": {
    "ldapDisplayName": "name",
    "cn": "RDN",
    "attributeId": "1.2.840.113556.1.4.1",
    "attributeSyntax": "2.5.5.12",
    "omSyntax": 64,
    "isSingleValued": true,
    "systemOnly": true,
    "searchFlags": "fPRESERVEONDELETE| fANR | fATTINDEX",
    "rangeLower": 1,
    "rangeUpper": 255,
    "attributeSecurityGuid": "e48d0154-bcf8-11d1-8702-00c04fb96050",
    "mapiID": 33282,
    "isMemberOfPartialAttributeSet": true,
    "systemFlags": "FLAG_SCHEMA_BASE_OBJECT | FLAG_ATTR_REQ_PARTIAL_SET_MEMBER",
    "schemaFlagsEx": "FLAG_ATTR_IS_CRITICAL"
  }
}
```

## Project Structure

Uses **src-layout** for clean package organization:

```
security-research-toolkit/
├── src/ad_schema_tool/             # Main Python package
│   └── cli.py                      # CLI interface
├── scripts/                        # Development tools
│   └── parse_ms_ada_pdfs.py        # PDF parser and schema builder
├── ad_schema_enhanced.json         # Enhanced schema data (created by build-schema)
└── docs/                           # Documentation
    ├── USER_GUIDE.md
    └── DEVELOPMENT.md
```

## Advanced Usage

### GUID List Analysis
```bash
# Create GUID lists (one GUID per line)
echo "bf967944-0de6-11d0-a285-00aa003049e2" > user_attrs.txt
echo "bf967a68-0de6-11d0-a285-00aa003049e2" >> user_attrs.txt

echo "bf967944-0de6-11d0-a285-00aa003049e2" > security_attrs.txt  
echo "bf9679e3-0de6-11d0-a285-00aa003049e2" >> security_attrs.txt

# Find common attributes
ad-schema-tool intersect --annotate user_attrs.txt security_attrs.txt
```

### Scripting and Automation
```bash
# Get all user-related attributes in plain format
ad-schema-tool --plain search user > user_attributes.txt

# Count Terminal Services attributes
ad-schema-tool --plain search msTS | wc -l

# Export for Excel analysis
ad-schema-tool export csv --output ad_analysis.csv

# Pipe to other tools
ad-schema-tool --plain list | awk -F'\t' '{print $1}' | sort

# Batch GUID processing
while read guid; do
    ad-schema-tool --plain lookup-guid "$guid"
done < guid_list.txt
```

### Integration Examples
```bash
# Use in shell scripts
GUID="bf967944-0de6-11d0-a285-00aa003049e2"
ATTR_NAME=$(ad-schema-tool --plain lookup-guid $GUID | cut -f2)
echo "Found attribute: $ATTR_NAME"

# Find intersection and extract names only
ad-schema-tool --plain intersect --annotate file1.txt file2.txt | cut -f2 > common_names.txt

# Create attribute mapping file
ad-schema-tool --plain intersect --output mapping.tsv file1.txt file2.txt
```

## Security Focus

This toolkit is designed for **defensive security** purposes:

- **Security analysis and auditing**
- **Detection rule development**  
- **Schema documentation and mapping**
- **SIEM correlation rule development**

## Use Cases

### Security Analysis
```bash
# Find sensitive attributes
ad-schema-tool search password
ad-schema-tool search secret
ad-schema-tool search credential

# Analyze audit log GUIDs
ad-schema-tool lookup-guid 9a9a021e-4a5b-11d1-a9c3-0000f80367c1
```

### Detection Engineering
```bash
# Find all user-related attributes for detection rules
ad-schema-tool --plain search user | grep -E "(logon|password|account)"

# Export Terminal Services attributes for monitoring
ad-schema-tool --plain search msTS > ts_attributes_for_monitoring.txt
```

### GUID List Analysis
```bash
# Compare attribute sets from different sources
ad-schema-tool intersect \
  --annotate \
  --output common_critical_attrs.txt \
  security_relevant.txt \
  audit_logged.txt \
  high_value_targets.txt
```

## Microsoft PDF Documents

This tool requires the official Microsoft AD Schema PDF documents:

- **MS-ADA1**: Active Directory Schema Attributes A-L
- **MS-ADA2**: Active Directory Schema Attributes M  
- **MS-ADA3**: Active Directory Schema Attributes N-Z

Download these from [Microsoft Learn](https://learn.microsoft.com/en-us/openspecs/windows_protocols/MS-WINPROTLP/e36c976a-6263-42a8-b119-7a3cc41ddd2a) before building your schema.

## Documentation

- **[User Guide](docs/USER_GUIDE.md)** - Complete CLI reference and examples
- **[Development Guide](docs/DEVELOPMENT.md)** - Development workflow and architecture

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Update documentation
6. Submit a pull request

## Development

This tool was developed with assistance from [Claude](https://claude.ai) by Anthropic.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

For questions, issues, or contributions, please [open an issue](../../issues) in the repository.