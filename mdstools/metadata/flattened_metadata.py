"""FlattenedMetadata class for handling tabular representations of metadata."""

import csv
import os
from typing import List, Optional

import pandas as pd

from mdstools.converters import unflatten


class FlattenedMetadata:
    """
    Wrapper for flattened tabular metadata structures.

    Handles metadata in tabular format as list of [number, key, value] rows.
    Provides methods to load from/save to CSV and Excel formats.

    EXAMPLES::

        >>> from mdstools.metadata import FlattenedMetadata
        >>> rows = [['1', 'name', 'test'], ['2', 'value', 42]]
        >>> flattened = FlattenedMetadata(rows)
        >>> len(flattened.rows)
        2
        >>> flattened.rows[0]
        ['1', 'name', 'test']
    """

    def __init__(self, rows: List[List]):
        """
        Initialize with flattened data rows.

        :param rows: List of rows, each containing [number, key, value]

        NOTE: The first row should NOT be a header row ['number', 'key', 'value'].
        If loading from a file with headers, they will be automatically skipped.
        """
        if not isinstance(rows, list):
            raise TypeError(f"Expected list, got {type(rows).__name__}")

        # Validate structure
        if rows and len(rows[0]) != 3:
            raise ValueError(
                f"Each row must have exactly 3 elements [number, key, value], got {len(rows[0])}"
            )

        self._rows = rows

    @property
    def rows(self) -> List[List]:
        """Get the underlying flattened data rows."""
        return self._rows

    @classmethod
    def from_csv(cls, filepath: str, **kwargs):
        """
        Load flattened metadata from a CSV file.

        :param filepath: Path to CSV file
        :param kwargs: Additional arguments (currently unused, for future compatibility)
        :return: FlattenedMetadata instance

        EXAMPLES::

            Basic CSV loading with type preservation:

            >>> from mdstools.metadata import FlattenedMetadata
            >>> flattened = FlattenedMetadata.from_csv('tests/from_csv_example.csv')
            >>> len(flattened.rows)
            5
            >>> flattened.rows[0][1]  # First row, key column
            'name'
            >>> # Values are converted to appropriate types (int, float, string)
            >>> isinstance(flattened.rows[1][2], int)  # value field is int 42
            True

            Reconstruct nested structure:

            >>> metadata = flattened.unflatten()
            >>> metadata.data
            {'name': 'test', 'value': 42, 'details': {'author': 'John Doe', 'year': 2024}}

        TESTS::

            Test roundtrip conversion with strings containing commas:

            >>> from mdstools.metadata import Metadata
            >>> import os
            >>> # Create data with comma in string value
            >>> original_data = {'description': 'test, with comma', 'value': 42, 'title': 'A, B, C'}
            >>> metadata = Metadata(original_data)
            >>> flattened = metadata.flatten()
            >>> # Save to CSV
            >>> flattened.to_csv('tests/generated/docstrings/test_comma.csv')
            >>> # Load back from CSV
            >>> loaded = FlattenedMetadata.from_csv('tests/generated/docstrings/test_comma.csv')
            >>> # Verify commas in strings are preserved
            >>> loaded.unflatten().data == original_data
            True
            >>> loaded.rows[0][2]  # First value should contain comma
            'test, with comma'
        """

        def convert_value(value_str):
            """
            Convert string value to appropriate type (int, float, or keep as string).

            NOTE: This is necessary because CSV files store all values as strings.
            Without type conversion, numeric values would remain strings after loading,
            breaking roundtrip equality (e.g., {'value': 42} != {'value': "42"}).
            This ensures that CSV roundtrips preserve the original data types.
            """
            if value_str == "<nested>":
                return value_str
            try:
                # Try int first
                if "." not in value_str:
                    return int(value_str)
                # Try float
                return float(value_str)
            except (ValueError, AttributeError):
                return value_str

        with open(filepath, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            rows = list(reader)

        # Skip header if present and convert values to appropriate types
        if rows and rows[0] and str(rows[0][0]).lower() in ["number", "num"]:
            # Has header, process data rows
            data_rows = [[row[0], row[1], convert_value(row[2])] for row in rows[1:]]
        else:
            data_rows = [[row[0], row[1], convert_value(row[2])] for row in rows]

        return cls(data_rows)

    @classmethod
    def from_excel(cls, filepath, **kwargs):
        """
        Load flattened metadata from an Excel file.

        :param filepath: Path to Excel file
        :param kwargs: Additional arguments passed to pandas.read_excel
        :return: FlattenedMetadata instance

        EXAMPLES::

            Test roundtrip: flattened → Excel → flattened

            >>> from mdstools.metadata import FlattenedMetadata
            >>> import os
            >>> original_rows = [['1', 'experiment', '<nested>'],
            ... ['1.a', '', '<nested>'],
            ... ['1.a.1', 'A', '<nested>'],
            ... ['1.a.1.1', 'value', 1],
            ... ['1.a.1.2', 'units', 'mV'],
            ... ['1.a.2', 'B', 2],
            ... ['1.b', '', '<nested>'],
            ... ['1.b.1', 'A', 3],
            ... ['1.b.2', 'B', 4]]
            >>> flattened = FlattenedMetadata(original_rows)
            >>> flattened.to_excel('generated/doctests/test_flattened.xlsx')
            >>> loaded = FlattenedMetadata.from_excel('generated/doctests/test_flattened.xlsx')
            >>> loaded.unflatten().data == flattened.unflatten().data
            True

            Multi-sheet roundtrip: save with separate_sheets, load automatically merges:

            >>> # Save as multi-sheet Excel
            >>> rows = [['1', 'experiment', '<nested>'], ['1.1', 'value', 1],
            ...         ['2', 'source', '<nested>'], ['2.1', 'author', 'test']]
            >>> flattened_multi = FlattenedMetadata(rows)
            >>> flattened_multi.to_excel('tests/generated/docstrings/multi_roundtrip.xlsx', separate_sheets=True)
            >>> # Load back - automatically handles multiple sheets
            >>> loaded_multi = FlattenedMetadata.from_excel('tests/generated/docstrings/multi_roundtrip.xlsx')
            >>> len(loaded_multi.rows) == len(rows)
            True
        """
        # Read Excel file (handles both single and multi-sheet files)
        from mdstools.metadata.local import load_excel_all_sheets

        df = load_excel_all_sheets(filepath, **kwargs)

        # Convert to list of lists (Excel preserves numeric types)
        # Ensure Number column is string for consistency
        df["Number"] = df["Number"].astype(str)

        # Only use first 3 columns (Number, Key, Value)
        # This allows loading enriched files that have Example/Description columns
        if len(df.columns) >= 3:
            df = df.iloc[:, :3]
            df.columns = ["Number", "Key", "Value"]  # Ensure consistent names

        # Fill NaN in Key column with empty string (Excel treats empty strings as NaN)
        df["Key"] = df["Key"].fillna("")

        data_rows = df.values.tolist()

        return cls(data_rows)

    def unflatten(self):
        """
        Convert back to nested metadata structure.

        :return: Metadata instance

        EXAMPLES::

            >>> from mdstools.metadata import FlattenedMetadata
            >>> rows = [['1', 'experiment', '<nested>'],
            ... ['1.1', 'value', 1],
            ... ['1.2', 'units', 'mV']]
            >>> flattened = FlattenedMetadata(rows)
            >>> metadata = flattened.unflatten()
            >>> metadata.data
            {'experiment': {'value': 1, 'units': 'mV'}}
        """
        from mdstools.metadata.metadata import Metadata

        nested_dict = unflatten(self._rows)
        return Metadata(nested_dict)

    def to_pandas(self) -> pd.DataFrame:
        """
        Convert to pandas DataFrame.

        :return: DataFrame with columns ['Number', 'Key', 'Value']

        EXAMPLES::

            >>> from mdstools.metadata import FlattenedMetadata
            >>> rows = [['1', 'name', 'test'], ['2', 'value', 42]]
            >>> flattened = FlattenedMetadata(rows)
            >>> df = flattened.to_pandas()
            >>> df.columns.tolist()
            ['Number', 'Key', 'Value']
            >>> df['Key'].tolist()
            ['name', 'value']
        """
        return pd.DataFrame(self._rows, columns=["Number", "Key", "Value"])

    def to_csv(self, filepath: str, **kwargs):
        """
        Save flattened metadata to a CSV file.

        :param filepath: Path to save CSV file
        :param kwargs: Additional arguments passed to pandas.DataFrame.to_csv

        EXAMPLES::

            >>> from mdstools.metadata import FlattenedMetadata
            >>> import os
            >>> rows = [['1', 'experiment', '<nested>'], ['1.1', 'value', 1]]
            >>> flattened = FlattenedMetadata(rows)
            >>> flattened.to_csv('tests/generated/docstrings/test_flat.csv')
            >>> os.path.exists('tests/generated/docstrings/test_flat.csv')
            True
        """
        if isinstance(filepath, str):
            os.makedirs(os.path.dirname(filepath) or ".", exist_ok=True)
        df = self.to_pandas()
        df.to_csv(filepath, index=False, **kwargs)

    def to_excel(self, filepath, separate_sheets=False, **kwargs):
        """
        Save flattened metadata to an Excel file.

        :param filepath: Path to save Excel file
        :param separate_sheets: If True, create separate sheets for each top-level key
        :param kwargs: Additional arguments passed to pandas.DataFrame.to_excel

        When separate_sheets=True, the Excel file will have one sheet per top-level
        key in the nested structure, making it easier to navigate large metadata files.

        EXAMPLES::

            Single sheet export:

            >>> from mdstools.metadata import FlattenedMetadata
            >>> import os
            >>> rows = [['1', 'experiment', '<nested>'], ['1.1', 'value', 1]]
            >>> flattened = FlattenedMetadata(rows)
            >>> flattened.to_excel('tests/generated/docstrings/test_flat.xlsx')
            >>> os.path.exists('tests/generated/docstrings/test_flat.xlsx')
            True

            Multi-sheet export:

            >>> rows = [['1', 'experiment', '<nested>'], ['1.1', 'value', 1],
            ...         ['2', 'source', '<nested>'], ['2.1', 'author', 'test']]
            >>> flattened = FlattenedMetadata(rows)
            >>> flattened.to_excel('tests/generated/docstrings/test_flat_multi.xlsx', separate_sheets=True)
            >>> os.path.exists('tests/generated/docstrings/test_flat_multi.xlsx')
            True
        """
        df = self.to_pandas()

        if not separate_sheets:
            # Single sheet export
            if isinstance(filepath, str):
                os.makedirs(os.path.dirname(filepath) or ".", exist_ok=True)
            df.to_excel(filepath, index=False, **kwargs)
        else:
            # Multi-sheet export: one sheet per top-level key
            from mdstools.metadata.local import save_excel_multi_sheet

            save_excel_multi_sheet(df, filepath, ["Number", "Key", "Value"])

    def to_markdown(self, **kwargs) -> str:
        """
        Convert to Markdown table format.

        :param kwargs: Additional arguments passed to pandas.DataFrame.to_markdown
        :return: Markdown-formatted string

        EXAMPLES::

            Simple example:

            >>> from mdstools.metadata import FlattenedMetadata
            >>> rows = [['1', 'name', 'test'], ['2', 'value', 42]]
            >>> flattened = FlattenedMetadata(rows)
            >>> print(flattened.to_markdown()) # doctest: +NORMALIZE_WHITESPACE
            |   Number | Key   | Value   |
            |---------:|:------|:--------|
            |        1 | name  | test    |
            |        2 | value | 42      |

            With nested structures and lists:

            >>> rows = [['1', 'name', 'test'], ['2', 'foo', '<nested>'],
            ... ['2.a', '', 'a'], ['2.b', '', 'b'], ['2.c', '', 'c']]
            >>> flattened = FlattenedMetadata(rows)
            >>> markdown = flattened.to_markdown()
            >>> 'Number' in markdown and 'Key' in markdown and 'Value' in markdown
            True
            >>> '<nested>' in markdown
            True
        """
        df = self.to_pandas()
        return df.to_markdown(index=False, **kwargs)
