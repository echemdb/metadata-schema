# mdstools - Metadata Schema Tools

Tools for converting between nested and flattened metadata structures, with optional schema-based enrichment.

## Modules

### `tabular_schema.py`

Core module for flattening nested YAML/dict structures into tabular formats suitable for Excel editing.

**Key Features:**

- Flatten nested dictionaries and lists into numbered rows
- Unflatten back to nested structure (planned)
- Export to CSV, Excel (single or multi-sheet), and Markdown
- Optional schema-based enrichment with descriptions and examples

**Main Classes:**

- `MetadataConverter` - Bidirectional converter between nested and flat formats

### `schema_enricher.py`

Schema-based enrichment module that adds descriptions and examples from JSON Schema files.

**Key Features:**

- Load and cache JSON Schema files
- Automatically use "resolved" schemas (with inlined $refs)
- Extract descriptions and examples from schema definitions
- Support for oneOf/anyOf enum descriptions

**Main Classes:**

- `SchemaEnricher` - Enriches data using JSON Schema metadata

## Usage Examples

### Basic Flattening

```python
import yaml
from mdstools.tabular_schema import MetadataConverter

# Load YAML data
with open('metadata.yaml', 'r') as f:
    data = yaml.safe_load(f)

# Create converter
converter = MetadataConverter.from_dict(data)

# Get flattened DataFrame
df = converter.df
print(df.head())

# Export to CSV
converter.to_csv('output.csv')

# Export to Excel (multi-sheet)
converter.to_excel('output.xlsx', separate_sheets=True)
```

### With Schema Enrichment

```python
import yaml
from mdstools.tabular_schema import MetadataConverter

# Load YAML data
with open('metadata.yaml', 'r') as f:
    data = yaml.safe_load(f)

# Create converter with schema directory
converter = MetadataConverter.from_dict(data, schema_dir='schemas')

# Get enriched DataFrame with Description and Example columns
df = converter.enriched_df
print(df[['Key', 'Value', 'Description', 'Example']].head())

# Export enriched data
converter.to_csv('output_enriched.csv', enriched=True)
converter.to_excel('output_enriched.xlsx', enriched=True)
```

### Markdown Export

```python
# Export as markdown table
markdown = converter.to_markdown(enriched=True)
print(markdown)
```

## Testing

Run all tests:

```bash
pixi run test
```

Run individual test suites:

```bash
pixi run doctest              # Run doctests in mdstools modules
pixi run test-comprehensive   # Run comprehensive integration tests
```
