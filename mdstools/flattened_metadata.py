"""FlattenedMetadata class for handling tabular representations of metadata."""

import csv
from typing import List, Optional

import pandas as pd

from mdstools.tabular_schema import unflatten


class FlattenedMetadata:
    """
    Wrapper for flattened tabular metadata structures.

    Handles metadata in tabular format as list of [number, key, value] rows.
    Provides methods to load from/save to CSV and Excel formats.

    EXAMPLES::

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
            raise ValueError(f"Each row must have exactly 3 elements [number, key, value], got {len(rows[0])}")

        self._rows = rows

    @property
    def rows(self) -> List[List]:
        """Get the underlying flattened data rows."""
        return self._rows

    @classmethod
    def from_csv(cls, filepath, **kwargs):
        """
        Load flattened metadata from a CSV file.

        :param filepath: Path to CSV file or file-like object (e.g., StringIO)
        :param kwargs: Additional arguments (currently unused, for future compatibility)
        :return: FlattenedMetadata instance

        EXAMPLES::

            >>> flattened = FlattenedMetadata.from_csv('generated/doctests/from_csv_example.csv')
            >>> len(flattened.rows)
            5
            >>> flattened.rows[0][1]  # First row, key column
            'name'
        """
        def convert_value(value_str):
            """Convert string value to appropriate type (int, float, or keep as string)"""
            if value_str == '<nested>':
                return value_str
            try:
                # Try int first
                if '.' not in value_str:
                    return int(value_str)
                # Try float
                return float(value_str)
            except (ValueError, AttributeError):
                return value_str

        # Handle both file path and file-like objects
        if isinstance(filepath, str):
            with open(filepath, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                rows = list(reader)
        else:
            reader = csv.reader(filepath)
            rows = list(reader)

        # Skip header if present and convert values to appropriate types
        if rows and rows[0] and str(rows[0][0]).lower() in ['number', 'num']:
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

            >>> import os
            >>> os.makedirs('generated/doctests', exist_ok=True)
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
        """
        # Read Excel file with pandas
        df = pd.read_excel(filepath, **kwargs)

        # Convert to list of lists (Excel preserves numeric types)
        # Ensure Number column is string for consistency
        df['Number'] = df['Number'].astype(str)
        data_rows = df.values.tolist()

        return cls(data_rows)

    def unflatten(self):
        """
        Convert back to nested metadata structure.

        :return: Metadata instance

        EXAMPLES::

            >>> rows = [['1', 'experiment', '<nested>'],
            ... ['1.1', 'value', 1],
            ... ['1.2', 'units', 'mV']]
            >>> flattened = FlattenedMetadata(rows)
            >>> metadata = flattened.unflatten()
            >>> metadata.data
            {'experiment': {'value': 1, 'units': 'mV'}}
        """
        from mdstools.metadata import Metadata

        nested_dict = unflatten(self._rows)
        return Metadata(nested_dict)

    def to_pandas(self) -> pd.DataFrame:
        """
        Convert to pandas DataFrame.

        :return: DataFrame with columns ['Number', 'Key', 'Value']

        EXAMPLES::

            >>> rows = [['1', 'name', 'test'], ['2', 'value', 42]]
            >>> flattened = FlattenedMetadata(rows)
            >>> df = flattened.to_pandas()
            >>> df.columns.tolist()
            ['Number', 'Key', 'Value']
            >>> df['Key'].tolist()
            ['name', 'value']
        """
        return pd.DataFrame(self._rows, columns=["Number", "Key", "Value"])

    def to_csv(self, filepath, **kwargs):
        """
        Save flattened metadata to a CSV file.

        :param filepath: Path to save CSV file or file-like object
        :param kwargs: Additional arguments passed to pandas.DataFrame.to_csv

        EXAMPLES::

            >>> import os
            >>> os.makedirs('generated/doctests', exist_ok=True)
            >>> rows = [['1', 'name', 'test'], ['2', 'value', 42]]
            >>> flattened = FlattenedMetadata(rows)
            >>> flattened.to_csv('generated/doctests/test_flat.csv')
            >>> os.path.exists('generated/doctests/test_flat.csv')
            True
        """
        df = self.to_pandas()
        df.to_csv(filepath, index=False, **kwargs)

    def to_excel(self, filepath, **kwargs):
        """
        Save flattened metadata to an Excel file.

        :param filepath: Path to save Excel file
        :param kwargs: Additional arguments passed to pandas.DataFrame.to_excel

        EXAMPLES::

            >>> import os
            >>> os.makedirs('generated/doctests', exist_ok=True)
            >>> rows = [['1', 'name', 'test'], ['2', 'value', 42]]
            >>> flattened = FlattenedMetadata(rows)
            >>> flattened.to_excel('generated/doctests/test_flat.xlsx')
            >>> os.path.exists('generated/doctests/test_flat.xlsx')
            True
        """
        df = self.to_pandas()
        df.to_excel(filepath, index=False, **kwargs)

    def to_markdown(self, **kwargs) -> str:
        """
        Convert to Markdown table format.

        :param kwargs: Additional arguments passed to pandas.DataFrame.to_markdown
        :return: Markdown-formatted string

        EXAMPLES::

            >>> rows = [['1', 'name', 'test'], ['2', 'foo', '<nested>'], ['2.a', '', 'bar']]
            >>> flattened = FlattenedMetadata(rows)
            >>> print(flattened.to_markdown()) # doctest: +NORMALIZE_WHITESPACE
            | Number   | Key   | Value    |
            |:---------|:------|:---------|
            | 1        | name  | test     |
            | 2        | foo   | <nested> |
            | 2.a      |       | bar      |
        """
        df = self.to_pandas()
        return df.to_markdown(index=False, **kwargs)
