"""EnrichedFlattenedMetadata class for handling schema-enriched tabular metadata."""

from typing import List

import pandas as pd

from mdstools.metadata.flattened_metadata import FlattenedMetadata
from mdstools.schema.enricher import SchemaEnricher


class EnrichedFlattenedMetadata:
    """
    Schema-enriched wrapper for flattened tabular metadata structures.

    Extends FlattenedMetadata by adding Example and Description columns
    from JSON Schema files. This provides documentation and reference values
    alongside the actual metadata.

    EXAMPLES::

        Load from a dictionary and enrich with schema information::

            >>> from mdstools.metadata.enriched_metadata import EnrichedFlattenedMetadata
            >>> import os

            >>> # Start with nested metadata
            >>> data = {'curation': {'process': [{'role': 'curator', 'name': 'John Doe'}]}}

            >>> # Create enriched metadata (flattens and adds schema info)
            >>> enriched = EnrichedFlattenedMetadata.from_dict(data, schema_dir='schemas')

            >>> # Base rows have 3 columns: [Number, Key, Value]
            >>> enriched.base_rows[0]  # Top level
            ['1', 'curation', '<nested>']
            >>> enriched.base_rows[3]  # Leaf value
            ['1.1.a.1', 'role', 'curator']

            >>> # Enriched rows have 5 columns: [Number, Key, Value, Example, Description]
            >>> enriched.rows
            [['1', 'curation', '<nested>', '', ''],
            ['1.1', 'process', '<nested>', '', 'List of people involved in creating, recording, or curating this data.'],
            ['1.1.a', '', '<nested>', '', 'List of people involved in creating, recording, or curating this data.'],
            ['1.1.a.1', 'role', 'curator', 'experimentalist', 'A person that recorded the (meta)data.'],
            ['1.1.a.2', 'name', 'John Doe', 'Jane Doe', 'Full name of the person.']]
            >>> enriched.rows[3][3]  # Example for 'role' field
            'experimentalist'
            >>> 'person' in enriched.rows[3][4].lower()  # Description contains 'person'
            True
    """

    def __init__(self, rows: List[List], schema_dir: str):
        """
        Initialize with flattened data rows and schema directory.

        :param rows: List of rows, each containing [number, key, value]
        :param schema_dir: Path to directory containing JSON Schema files
        """
        # Store base flattened data (3 columns)
        # Ensure all numbers are strings
        self._base_rows = [[str(row[0]), row[1], row[2]] for row in rows]
        self._schema_dir = schema_dir

        # Initialize schema enricher
        self._enricher = SchemaEnricher(schema_dir)

        # Enrich the rows (adds Example and Description columns)
        self._enriched_rows = self._enricher.enrich_flattened_data(self._base_rows)

    @property
    def rows(self) -> List[List]:
        """Get the enriched data rows with Example and Description columns."""
        return self._enriched_rows

    @property
    def base_rows(self) -> List[List]:
        """Get the base 3-column rows without enrichment."""
        return self._base_rows

    @classmethod
    def from_dict(cls, data: dict, schema_dir: str):
        """
        Create EnrichedFlattenedMetadata from a nested dictionary.

        :param data: Nested dictionary of metadata
        :param schema_dir: Path to directory containing JSON Schema files
        :return: EnrichedFlattenedMetadata instance

        EXAMPLES::

            >>> from mdstools.metadata.enriched_metadata import EnrichedFlattenedMetadata
            >>> data = {'system': {'type': 'electrochemical'}}
            >>> enriched = EnrichedFlattenedMetadata.from_dict(data, schema_dir='schemas')
            >>> enriched.base_rows[0]
            ['1', 'system', '<nested>']
            >>> enriched.base_rows[1]
            ['1.1', 'type', 'electrochemical']
            >>> len(enriched.rows[1])  # Enriched row has 5 columns
            5
        """
        from mdstools.metadata.metadata import Metadata

        # Create Metadata and flatten it
        metadata = Metadata(data)
        flattened = metadata.flatten()

        # Create enriched version
        return cls(flattened.rows, schema_dir)

    @classmethod
    def from_csv(cls, filepath, schema_dir: str, **kwargs):
        """
        Load flattened metadata from a CSV file and enrich with schema information.

        :param filepath: Path to CSV file
        :param schema_dir: Path to directory containing JSON Schema files
        :param kwargs: Additional arguments passed to FlattenedMetadata.from_csv
        :return: EnrichedFlattenedMetadata instance

        EXAMPLES::

            >>> from mdstools.metadata.enriched_metadata import EnrichedFlattenedMetadata
            >>> from mdstools.metadata.flattened_metadata import FlattenedMetadata
            >>> import os
            >>> # Create a test CSV with system metadata
            >>> import csv
            >>> os.makedirs('tests/generated/docstrings', exist_ok=True)
            >>> with open('tests/generated/docstrings/system_example.csv', 'w', newline='') as f:
            ...     writer = csv.writer(f)
            ...     _ = writer.writerow(['Number', 'Key', 'Value'])
            ...     _ = writer.writerow(['1', 'system', '<nested>'])
            ...     _ = writer.writerow(['1.1', 'type', 'electrochemical'])
            >>> enriched = EnrichedFlattenedMetadata.from_csv('tests/generated/docstrings/system_example.csv',
            ...                                                schema_dir='schemas')
            >>> len(enriched.rows)
            2
            >>> len(enriched.rows[0])  # Has 5 columns
            5
        """
        # Load base data via FlattenedMetadata
        base_flattened = FlattenedMetadata.from_csv(filepath, **kwargs)
        return cls(base_flattened.rows, schema_dir)

    @classmethod
    def from_excel(cls, filepath, schema_dir: str, **kwargs):
        """
        Load flattened metadata from an Excel file and enrich with schema information.

        :param filepath: Path to Excel file
        :param schema_dir: Path to directory containing JSON Schema files
        :param kwargs: Additional arguments passed to FlattenedMetadata.from_excel
        :return: EnrichedFlattenedMetadata instance

        EXAMPLES::

            >>> from mdstools.metadata.enriched_metadata import EnrichedFlattenedMetadata
            >>> from mdstools.metadata.flattened_metadata import FlattenedMetadata
            >>> import os
            >>> # Create test data
            >>> rows = [['1', 'system', '<nested>'], ['1.1', 'type', 'electrochemical']]
            >>> flattened = FlattenedMetadata(rows)
            >>> flattened.to_excel('tests/generated/docstrings/system_excel_example.xlsx')
            >>> # Load with enrichment
            >>> enriched = EnrichedFlattenedMetadata.from_excel('tests/generated/docstrings/system_excel_example.xlsx',
            ...                                                  schema_dir='schemas')
            >>> len(enriched.rows[0])  # Has 5 columns
            5

            Load multi-sheet enriched Excel file:

            >>> # Can load enriched files saved with separate_sheets=True
            >>> rows = [['1', 'system', '<nested>'], ['1.1', 'type', 'electrochemical'],
            ...         ['2', 'curation', '<nested>'], ['2.1', 'process', '<nested>']]
            >>> enriched_multi = EnrichedFlattenedMetadata(rows, schema_dir='schemas')
            >>> enriched_multi.to_excel('tests/generated/docstrings/enriched_multi_ex.xlsx', separate_sheets=True)
            >>> loaded = EnrichedFlattenedMetadata.from_excel('tests/generated/docstrings/enriched_multi_ex.xlsx',
            ...                                                schema_dir='schemas')
            >>> len(loaded.base_rows)
            4
        """
        # Load base data via FlattenedMetadata (which handles multi-sheet files)
        base_flattened = FlattenedMetadata.from_excel(filepath, **kwargs)
        return cls(base_flattened.rows, schema_dir)

    def unflatten(self, schema_path: str | None = None):
        """
        Convert back to nested metadata structure (ignores enrichment columns).

        :param schema_path: Optional JSON schema file path for validation
        :return: Metadata instance

        EXAMPLES::

            >>> from mdstools.metadata.enriched_metadata import EnrichedFlattenedMetadata
            >>> rows = [['1', 'experiment', '<nested>'],
            ... ['1.1', 'value', 1]]
            >>> enriched = EnrichedFlattenedMetadata(rows, schema_dir='schemas')
            >>> metadata = enriched.unflatten()
            >>> metadata.data
            {'experiment': {'value': 1}}
        """
        from mdstools.converters.unflatten import unflatten
        from mdstools.metadata.metadata import Metadata

        # Unflatten only uses the first 3 columns (Number, Key, Value)
        nested_dict = unflatten(self._base_rows)
        metadata = Metadata(nested_dict)

        if schema_path:
            from mdstools.schema.validator import validate_metadata

            validate_metadata(metadata.data, schema_path)

        return metadata

    def to_pandas(self) -> pd.DataFrame:
        """
        Convert to pandas DataFrame with enrichment columns.

        :return: DataFrame with columns ['Number', 'Key', 'Value', 'Example', 'Description']

        EXAMPLES::

            >>> from mdstools.metadata.enriched_metadata import EnrichedFlattenedMetadata
            >>> rows = [['1', 'system', '<nested>'], ['1.1', 'type', 'electrochemical']]
            >>> enriched = EnrichedFlattenedMetadata(rows, schema_dir='schemas')
            >>> df = enriched.to_pandas()
            >>> df.columns.tolist()
            ['Number', 'Key', 'Value', 'Example', 'Description']
            >>> '<nested>' in df['Value'].tolist()
            True
        """
        return pd.DataFrame(
            self._enriched_rows,
            columns=["Number", "Key", "Value", "Example", "Description"],
        )

    def to_csv(self, filepath, **kwargs):
        """
        Save enriched metadata to a CSV file.

        :param filepath: Path to save CSV file
        :param kwargs: Additional arguments passed to pandas.DataFrame.to_csv

        EXAMPLES::

            >>> from mdstools.metadata.enriched_metadata import EnrichedFlattenedMetadata
            >>> import os
            >>> rows = [['1', 'system', '<nested>'], ['1.1', 'type', 'electrochemical']]
            >>> enriched = EnrichedFlattenedMetadata(rows, schema_dir='schemas')
            >>> enriched.to_csv('tests/generated/docstrings/enriched_test.csv')
            >>> os.path.exists('tests/generated/docstrings/enriched_test.csv')
            True
        """
        from mdstools.metadata.local import save_csv_with_path_creation

        df = self.to_pandas()
        save_csv_with_path_creation(df, filepath, **kwargs)

    def to_excel(self, filepath, separate_sheets=False, **kwargs):
        """
        Save enriched metadata to an Excel file.

        :param filepath: Path to save Excel file
        :param separate_sheets: If True, create separate sheets for each top-level key
        :param kwargs: Additional arguments passed to pandas.DataFrame.to_excel

        When separate_sheets=True, the Excel file will have one sheet per top-level
        key in the nested structure, making it easier to navigate large metadata files.

        EXAMPLES::

            Single sheet export:

            >>> from mdstools.metadata.enriched_metadata import EnrichedFlattenedMetadata
            >>> import os
            >>> rows = [['1', 'system', '<nested>'], ['1.1', 'type', 'electrochemical']]
            >>> enriched = EnrichedFlattenedMetadata(rows, schema_dir='schemas')
            >>> enriched.to_excel('tests/generated/docstrings/enriched_test.xlsx')
            >>> os.path.exists('tests/generated/docstrings/enriched_test.xlsx')
            True

            Multi-sheet export:

            >>> rows = [['1', 'system', '<nested>'], ['1.1', 'type', 'electrochemical'],
            ...         ['2', 'source', '<nested>'], ['2.1', 'author', 'test']]
            >>> enriched = EnrichedFlattenedMetadata(rows, schema_dir='schemas')
            >>> enriched.to_excel('tests/generated/docstrings/enriched_multi.xlsx', separate_sheets=True)
            >>> os.path.exists('tests/generated/docstrings/enriched_multi.xlsx')
            True
        """
        from mdstools.metadata.local import save_excel_with_optional_sheets

        df = self.to_pandas()
        save_excel_with_optional_sheets(
            df,
            filepath,
            ["Number", "Key", "Value", "Example", "Description"],
            separate_sheets,
            **kwargs,
        )

    def to_markdown(self, **kwargs) -> str:
        """
        Convert to Markdown table format with enrichment columns.

        :param kwargs: Additional arguments passed to pandas.DataFrame.to_markdown
        :return: Markdown-formatted string

        EXAMPLES::

            >>> from mdstools.metadata.enriched_metadata import EnrichedFlattenedMetadata
            >>> rows = [['1', 'system', '<nested>'], ['1.1', 'type', 'electrochemical']]
            >>> enriched = EnrichedFlattenedMetadata(rows, schema_dir='schemas')
            >>> markdown = enriched.to_markdown()
            >>> 'Example' in markdown and 'Description' in markdown
            True
        """
        df = self.to_pandas()
        return df.to_markdown(index=False, **kwargs)
