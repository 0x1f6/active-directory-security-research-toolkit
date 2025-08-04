# Development Guide

Guide for developing and maintaining the AD Schema Mapping Tool.

## Development Environment Setup

### Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) package manager
- Microsoft AD Schema PDF documents (MS-ADA1, MS-ADA2, MS-ADA3)

### Setup

```bash
# Clone repository
git clone https://github.com/0x1f6/active-directory-security-research-toolkit.git
cd active-directory-security-research-toolkit

# Install dependencies
uv sync

# Install in development mode
uv pip install -e .

# Install development dependencies
uv add --dev ruff

# Verify installation
uv run ad-schema-tool --help
```

## Project Architecture

### Current Design (PDF-based)

The toolkit uses a **direct PDF parsing** model for maximum reliability and completeness:

```
MS-ADA PDFs  →  PDF Parser  →  Enhanced JSON  →  CLI Tool
(Official docs)   (PyMuPDF)      (Rich metadata)    (Direct load)
```

**Key Benefits:**
- Direct extraction from official Microsoft documentation
- No rate limiting or web scraping issues
- Complete metadata extraction (15+ fields per attribute)
- Reproducible and reliable
- Self-contained (users provide their own PDFs)

### Data Flow

```
1. Microsoft PDFs     →  parse_ms_ada_pdfs.py  →  Enhanced JSON
   (MS-ADA1-3)           (PDF extraction +         (1500+ attributes)
                          schema building)
                              
2. Enhanced JSON      →  CLI Tool (direct consumption)
   (Rich metadata)       (Instant lookups)
```

## Development Scripts

Development tools are located in the `scripts/` directory:

### `scripts/parse_ms_ada_pdfs.py`

Python script to parse Microsoft AD Schema PDF documents and build enhanced JSON.

**Features:**
- **PDF Text Extraction**: Uses PyMuPDF for reliable text extraction
- **Regex Pattern Matching**: Extracts 15+ metadata fields per attribute
- **Multiline Field Support**: Handles complex systemFlags and schemaFlagsEx
- **Enhanced Schema Building**: Direct output to CLI-ready JSON format
- **Type Conversion**: Boolean/integer conversion for proper JSON types

**Usage:**
```bash
# Parse all three MS-ADA PDFs and build enhanced schema
uv run python scripts/parse_ms_ada_pdfs.py \
  ms-ada1.pdf ms-ada2.pdf ms-ada3.pdf \
  -o ad_schema_enhanced.json \
  --stats

# Parse single PDF (for testing)
uv run python scripts/parse_ms_ada_pdfs.py ms-ada1.pdf --stats

# Raw JSON output (for debugging)
uv run python scripts/parse_ms_ada_pdfs.py ms-ada1.pdf -o raw_output.json
```

**Output:** Enhanced JSON file with complete metadata

**Note:** Previously included a PowerShell script for AD extraction, but the PDF-based approach is now the only supported method.

## Development Workflow

### Building Enhanced Schema

The primary workflow for maintaining the enhanced schema:

```bash
# 1. Download Microsoft PDF documents
# Download MS-ADA1, MS-ADA2, MS-ADA3 from Microsoft Learn:
# - https://learn.microsoft.com/en-us/openspecs/windows_protocols/ms-ada1/
# - https://learn.microsoft.com/en-us/openspecs/windows_protocols/ms-ada2/
# - https://learn.microsoft.com/en-us/openspecs/windows_protocols/ms-ada3/

# 2. Build enhanced schema using CLI tool
uv run ad-schema-tool build-schema ms-ada1.pdf ms-ada2.pdf ms-ada3.pdf --stats

# 3. Test the result
uv run ad-schema-tool search user
uv run ad-schema-tool lookup-guid bf967944-0de6-11d0-a285-00aa003049e2
```

### Alternative: Direct Script Usage

For development and debugging:

```bash
# Use the script directly for more control
uv run python scripts/parse_ms_ada_pdfs.py \
  ms-ada1.pdf ms-ada2.pdf ms-ada3.pdf \
  --stats \
  -o ad_schema_enhanced_new.json

# Test new schema
uv run ad-schema-tool --schema-file ad_schema_enhanced_new.json search msTS

# Replace current schema (if satisfied)
mv ad_schema_enhanced_new.json ad_schema_enhanced.json
```

## Enhanced JSON Format

### Structure

The enhanced JSON format contains comprehensive metadata for each AD attribute:

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

### Field Extraction

The PDF parser extracts these fields from Microsoft documentation:

| Field | PDF Pattern | Type | Coverage | Example |
|-------|-------------|------|----------|---------|
| `ldapDisplayName` | `ldapDisplayName: <value>` | String | 100.0% | `"name"` |
| `cn` | `cn: <value>` | String | 99.6% | `"RDN"` |
| `attributeId` | `attributeId: <value>` | String | 99.6% | `"1.2.840.113556.1.4.1"` |
| `attributeSyntax` | `attributeSyntax: <value>` | String | 99.6% | `"2.5.5.12"` |
| `omSyntax` | `omSyntax: <value>` | Integer | 99.6% | `64` |
| `isSingleValued` | `isSingleValued: TRUE/FALSE` | Boolean | 99.6% | `true` |
| `systemOnly` | `systemOnly: TRUE/FALSE` | Boolean | 94.3% | `true` |
| `searchFlags` | `searchFlags: <flags>` | String | 99.6% | `"fATTINDEX"` |
| `systemFlags` | `systemFlags: <flags>` | String | 89.4% | `"FLAG_SCHEMA_BASE_OBJECT"` |
| `schemaFlagsEx` | `schemaFlagsEx: <flags>` | String | 26.1% | `"FLAG_ATTR_IS_CRITICAL"` |
| `rangeLower` | `rangeLower: <value>` | Integer | 20.9% | `1` |
| `rangeUpper` | `rangeUpper: <value>` | Integer | 27.7% | `255` |
| `attributeSecurityGuid` | `attributeSecurityGuid: <guid>` | String | 13.7% | `"guid"` |
| `mapiID` | `mapiID: <value>` | Integer | 8.8% | `33282` |
| `isMemberOfPartialAttributeSet` | `isMemberOfPartialAttributeSet: TRUE/FALSE` | Boolean | 15.0% | `true` |

### Data Type Conversion

The parser automatically converts:
- `"TRUE"/"FALSE"` → `true/false` (JSON boolean)
- Numeric strings → integers for specific fields (omSyntax, rangeLower, rangeUpper, mapiID)
- Multiline values → single line with proper spacing (systemFlags, schemaFlagsEx)

## Project Structure

### Current Clean Structure

```
active-directory-security-research-toolkit/
├── src/ad_schema_tool/             # Main Python package
│   ├── __init__.py
│   └── cli.py                      # CLI interface (loads JSON directly)
├── scripts/                        # Development tools
│   └── parse_ms_ada_pdfs.py        # PDF parser and schema builder
├── docs/                           # Documentation
│   ├── USER_GUIDE.md               # Complete CLI reference
│   └── DEVELOPMENT.md              # This file
├── ad_schema_enhanced.json         # Enhanced schema data (primary)
├── pyproject.toml                  # Package configuration
├── README.md                       # Main documentation
└── .gitignore                      # Git ignore patterns
```

### Design Principles

- **PDF-based extraction**: Direct parsing from official Microsoft documentation
- **Complete metadata**: 15+ fields per attribute with high coverage
- **Single-script processing**: All functionality in one script
- **Direct JSON consumption**: No code generation needed
- **Clean separation**: Development tools separate from user CLI
- **Self-contained**: Users provide their own PDF files

## Testing

### CLI Testing

```bash
# Test build-schema command
uv run ad-schema-tool build-schema ms-ada1.pdf ms-ada2.pdf ms-ada3.pdf --stats

# Test all main functions
uv run ad-schema-tool lookup-guid bf967944-0de6-11d0-a285-00aa003049e2
uv run ad-schema-tool lookup-name cost
uv run ad-schema-tool search msTS
uv run ad-schema-tool list | head -5

# Test intersect functionality
echo "bf967944-0de6-11d0-a285-00aa003049e2" > test1.txt
echo "bf967a68-0de6-11d0-a285-00aa003049e2" > test2.txt
uv run ad-schema-tool intersect --annotate test1.txt test2.txt

# Test export functions
uv run ad-schema-tool export csv --output test.csv
uv run ad-schema-tool export json --output test.json

# Test error handling
uv run ad-schema-tool lookup-name invalid-attribute
uv run ad-schema-tool lookup-guid invalid-guid
```

### Schema Validation

```bash
# Validate JSON structure
python -c "
import json
with open('ad_schema_enhanced.json') as f:
    data = json.load(f)
    print(f'Valid JSON with {len(data)} entries')
    
    # Check required fields
    sample = next(iter(data.values()))
    required = ['ldapDisplayName']
    for field in required:
        if field not in sample:
            print(f'WARNING: Missing {field} in sample entry')
        else:
            print(f'✓ {field} present')
"

# Check for duplicates
python -c "
import json
with open('ad_schema_enhanced.json') as f:
    data = json.load(f)
    names = [attr.get('ldapDisplayName', attr.get('cn', 'Unknown')) 
             for attr in data.values()]
    print(f'Unique names: {len(set(names))}/{len(names)}')
    if len(set(names)) != len(names):
        print('WARNING: Duplicate attribute names found')
"
```

### PDF Parser Testing

```bash
# Test PDF parser directly
uv run python scripts/parse_ms_ada_pdfs.py ms-ada1.pdf --stats

# Test with multiple PDFs
uv run python scripts/parse_ms_ada_pdfs.py \
  ms-ada1.pdf ms-ada2.pdf ms-ada3.pdf \
  --stats \
  -o test_schema.json

# Validate output
head -20 test_schema.json
python -c "import json; print(len(json.load(open('test_schema.json'))))"
```

## Code Quality

### Linting and Formatting

```bash
# Run ruff checks
uv run ruff check

# Auto-fix issues
uv run ruff check --fix

# Format code
uv run ruff format

# Check formatting
uv run ruff format --check
```

### Type Checking

The CLI uses type hints throughout:

```python
def load_schema_mappings(json_file: Path) -> Dict[str, str]:
    """Load schema mappings from enhanced JSON file."""
```

## Adding Features

### New CLI Commands

1. **Edit** `src/ad_schema_tool/cli.py`
2. **Add parser** in `main()` function
3. **Implement function** following existing patterns
4. **Test** with `uv run ad-schema-tool <new-command>`

Example:
```python
# Add to argument parsers
validate_parser = subparsers.add_parser('validate', help='Validate GUIDs in file')
validate_parser.add_argument('file', type=Path, help='File with GUIDs to validate')

# Add to command handling
elif args.command == 'validate':
    validate_guids_in_file(mappings, args.file)
```

### New Metadata Fields

1. **Add regex pattern** in `scripts/parse_ms_ada_pdfs.py`:
   ```python
   'new_field': re.compile(r'^\xa0newField:\s*(.+)$', re.MULTILINE | re.IGNORECASE),
   ```

2. **Add to ADAttribute dataclass**:
   ```python
   new_field: Optional[str] = None
   ```

3. **Add to field mapping in export_to_enhanced_json()**:
   ```python
   "newField": attr.new_field,
   ```

4. **Test extraction** with sample PDF content

### New Export Formats  

1. **Add format choice** to CLI parser
2. **Implement export function** in `export_mappings()`
3. **Follow existing patterns** for CSV/JSON/TSV

## Troubleshooting

### Common Issues

**PDF parser fails:**
- Check PDF file paths are correct
- Verify PDFs are Microsoft AD Schema documents (MS-ADA1-3)
- Ensure PyMuPDF is installed: `uv add pymupdf`

**CLI tool not found:**
- Reinstall: `uv pip install -e .`
- Use absolute path or `uv run ad-schema-tool`
- Check virtual environment: `uv sync`

**Missing metadata in results:**
- Verify PDFs contain expected Microsoft documentation structure
- Check regex patterns in `parse_ms_ada_pdfs.py`
- Run parser with `--stats` for field coverage information

**Build-schema command fails:**
- Ensure PDF files exist and are readable
- Check PyMuPDF installation: `uv add pymupdf`
- Verify disk space for output file

### Development Tips

1. **Test with single PDF first**: Use one PDF file for faster debugging
2. **Check intermediate output**: Use `--stats` flag to see field coverage
3. **Validate JSON output**: Check JSON syntax and structure
4. **Keep backups**: Always backup `ad_schema_enhanced.json` before updates
5. **Use small samples**: Test regex patterns with small PDF sections first

## Contributing

### Code Style

- **Python**: Follow PEP 8, use type hints, run ruff
- **Documentation**: Keep README and guides updated
- **Testing**: Test manually with various scenarios

### Pull Request Process

1. Fork and create feature branch
2. Make changes and test thoroughly  
3. Run `uv run ruff check && uv run ruff format`
4. Update documentation if needed
5. Submit PR with clear description

## Microsoft PDF Documents

### Required Documents

The tool requires these official Microsoft PDF documents:

- **MS-ADA1**: Active Directory Schema Attributes A-L
- **MS-ADA2**: Active Directory Schema Attributes M  
- **MS-ADA3**: Active Directory Schema Attributes N-Z

### License Considerations

- PDFs are Microsoft's official documentation
- Users must download their own copies
- Tool does not redistribute Microsoft content
- PDFs are not included in git repository

## Future Improvements

### Potential Enhancements

- **Version tracking**: Compare different PDF versions and show changes
- **Advanced search**: Regex patterns, multiple field criteria
- **Schema validation**: Validate live AD schema against documentation
- **Export enhancements**: XML, YAML, custom formats
- **Integration APIs**: REST API for external tools
- **Batch processing**: Process multiple PDF sets

### Architecture Considerations

- **Caching**: Cache parsed PDF results for faster rebuilds
- **Async processing**: Parallel PDF processing for speed
- **Configuration**: Config files for parser settings
- **Plugins**: Extensible field extraction system