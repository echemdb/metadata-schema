"""Tools for converting between YAML and tabular representations with schema enrichment."""

import csv
from typing import Optional

import pandas as pd
import yaml

from mdstools.converters import flatten, unflatten


class MetadataConverter:
    """
    Bidirectional converter between nested dicts and flattened tabular formats.

    This class provides conversion between nested YAML/dict structures and
    flattened tabular formats suitable for Excel editing. It supports loading
    from either format and exporting to both.

    EXAMPLES::

        >>> data = {'experiment': 'abc', 'details': 'foo'}
        >>> converter = MetadataConverter.from_dict(data)
        >>> converter.flattened # doctest: +NORMALIZE_WHITESPACE
        [['1', 'experiment', 'abc'],
         ['2', 'details', 'foo']]

        >>> len(converter.df)
        2

        >>> converter.df.columns.tolist()
        ['Number', 'Key', 'Value']
    """

    def __init__(
        self, source_data, source_type="dict", schema_dir: Optional[str] = None
    ):
        """
        Initialize converter with data from either format.

        :param source_data: The data to convert (dict, list, or DataFrame)
        :param source_type: 'dict' for nested dict/list, 'flattened' for tabular data
        :param schema_dir: Optional path to directory containing JSON Schema files for enrichment
        """
        self._source_data = source_data
        self._source_type = source_type
        self._flattened = None
        self._nested = None
        self._df = None
        self._enricher = None
        self._schema_dir = schema_dir

        if schema_dir:
            from .schema_enricher import SchemaEnricher

            self._enricher = SchemaEnricher(schema_dir)

    @classmethod
    def from_dict(cls, data, schema_dir: Optional[str] = None):
        """
        Create a converter from a nested dictionary.

        :param data: The nested dictionary to convert
        :param schema_dir: Optional path to directory containing JSON Schema files for enrichment
        :return: MetadataConverter instance

        EXAMPLES::

            >>> data = {'name': 'test', 'value': 123}
            >>> converter = MetadataConverter.from_dict(data)
            >>> isinstance(converter, MetadataConverter)
            True
            >>> len(converter.flattened)
            2
        """
        return cls(data, source_type="dict", schema_dir=schema_dir)

    @classmethod
    def from_excel(cls, filepath, **kwargs):
        """
        Create a converter from a flattened Excel file.

        :param filepath: Path to the Excel file
        :param kwargs: Additional arguments passed to pandas.read_excel
        :return: MetadataConverter instance

        EXAMPLES::

            Test roundtrip conversion: flattened data → Excel → dict

            >>> import os
            >>> os.makedirs('generated/doctests', exist_ok=True)
            >>> # Create converter from complex flattened data
            >>> flattened_data = [['number', 'key', 'value'],
            ... ['1', 'experiment', '<nested>'],
            ... ['1.a', '', '<nested>'],
            ... ['1.a.1', 'A', '<nested>'],
            ... ['1.a.1.1', 'value', 1],
            ... ['1.a.1.2', 'units', 'mV'],
            ... ['1.a.2', 'B', 2],
            ... ['1.b', '', '<nested>'],
            ... ['1.b.1', 'A', 3],
            ... ['1.b.2', 'B', 4]]
            >>> converter = MetadataConverter(flattened_data[1:], source_type='flattened')
            >>> expected_dict = converter.nested_dict

            >>> # Export to Excel
            >>> converter.to_excel('generated/doctests/roundtrip.xlsx')

            >>> # Read back from Excel
            >>> converter_from_excel = MetadataConverter.from_excel('generated/doctests/roundtrip.xlsx')
            >>> converter_from_excel.nested_dict == expected_dict
            True
        """
        # Read Excel file with pandas
        df = pd.read_excel(filepath, **kwargs)

        # Convert to list of lists with type preservation
        # Excel preserves numeric types, so we don't need convert_value
        data_rows = df.values.tolist()

        return cls(data_rows, source_type="flattened")

    @classmethod
    def from_csv(cls, filepath, **kwargs):
        """
        Create a converter from a flattened CSV file.

        :param filepath: Path to the CSV file or file-like object (e.g., StringIO)
        :param kwargs: Additional arguments (currently unused, for future compatibility)
        :return: MetadataConverter instance

        EXAMPLES::

            >>> converter = MetadataConverter.from_csv('generated/doctests/from_csv_example.csv')
            >>> converter.df.columns.tolist()
            ['Number', 'Key', 'Value']
            >>> len(converter.df)
            5
            >>> converter.df['Key'].tolist()
            ['name', 'value', 'details', 'author', 'year']

            >>> converter.nested_dict
            {'name': 'test', 'value': 42, 'details': {'author': 'John Doe', 'year': 2024}}

        TESTS::

            Test the roundtrip conversion from dict to CSV and back to dict:

            >>> from io import StringIO
            >>> original_data = {'experiment':
            ... [{'A': {'value': 1, 'units': 'mV'}, 'B': 2}, {'A': 3, 'B': 4}]}
            >>> converter = MetadataConverter.from_dict(original_data)
            >>> # Write to StringIO buffer
            >>> csv_buffer = StringIO()
            >>> converter.to_csv(csv_buffer)
            >>> # Read back from the buffer
            >>> csv_buffer.seek(0)
            0
            >>> converter_from_csv = MetadataConverter.from_csv(csv_buffer)
            >>> converter_from_csv.nested_dict == original_data
            True

        """
        # Read CSV manually to preserve types better than pandas
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

        # Convert values to appropriate types (skip header if present)
        if rows and rows[0] and str(rows[0][0]).lower() in ['number', 'num']:
            # Has header, process data rows
            data_rows = [[row[0], row[1], convert_value(row[2])] for row in rows[1:]]
        else:
            data_rows = [[row[0], row[1], convert_value(row[2])] for row in rows]

        return cls(data_rows, source_type="flattened")

    @classmethod
    def from_dataframe(cls, df):
        """
        Create a converter from a pandas DataFrame.

        :param df: DataFrame with columns ['Number', 'Key', 'Value']
        :return: MetadataConverter instance
        """
        return cls(df, source_type="flattened")

    @property
    def flattened(self):
        """
        Get the flattened structure as a list of rows.

        :return: List of [number, key, value] rows

        EXAMPLES::

            >>> data = {'experiment': {'value': 42, 'units': 'mV'}}
            >>> converter = MetadataConverter.from_dict(data)
            >>> converter.flattened # doctest: +NORMALIZE_WHITESPACE
            [['1', 'experiment', '<nested>'],
             ['1.1', 'value', 42],
             ['1.2', 'units', 'mV']]
        """
        if self._flattened is None:
            if self._source_type == "dict":
                self._flattened = flatten(self._source_data)
            else:  # source_type == 'flattened'
                # Convert DataFrame to list of lists if needed
                if isinstance(self._source_data, pd.DataFrame):
                    self._flattened = self._source_data.values.tolist()
                else:
                    self._flattened = self._source_data
        return self._flattened

    @property
    def nested_dict(self):
        """
        Get the nested dictionary structure.

        :return: Nested dictionary

        NOTE: Unflattening is not yet implemented.
        """
        if self._nested is None:
            if self._source_type == "dict":
                self._nested = self._source_data
            else:  # source_type == 'flattened'
                self._nested = unflatten(self.flattened)
        return self._nested

    @property
    def df(self):
        """
        Get the flattened data as a pandas DataFrame.

        :return: DataFrame with columns ['Number', 'Key', 'Value']

        EXAMPLES::

            >>> data = {'name': 'test', 'value': 42}
            >>> converter = MetadataConverter.from_dict(data)
            >>> df = converter.df
            >>> df.columns.tolist()
            ['Number', 'Key', 'Value']
            >>> df['Number'].tolist()
            ['1', '2']
            >>> df['Key'].tolist()
            ['name', 'value']
        """
        if self._df is None:
            if self._source_type == "flattened" and isinstance(
                self._source_data, pd.DataFrame
            ):
                self._df = self._source_data
            else:
                self._df = pd.DataFrame(
                    self.flattened, columns=["Number", "Key", "Value"]
                )
        return self._df

    @property
    def enriched_df(self):
        """
        Get the enriched flattened data as a pandas DataFrame with Example and Description columns.

        Requires schema_dir to be provided during initialization.

        :return: DataFrame with columns ['Number', 'Key', 'Value', 'Example', 'Description']

        EXAMPLES::

            >>> # Example requires schema files
            >>> # converter = MetadataConverter.from_dict(data, schema_dir='schemas/')
            >>> # enriched = converter.enriched_df
            >>> # 'Description' in enriched.columns
            >>> # True
            >>> pass  # Placeholder for schema-based test
        """
        if not self._enricher:
            raise ValueError(
                "Schema enrichment not available. Please provide schema_dir during initialization."
            )

        enriched_rows = self._enricher.enrich_flattened_data(self.flattened)
        return pd.DataFrame(
            enriched_rows, columns=["Number", "Key", "Value", "Example", "Description"]
        )

    def to_dict(self):
        """
        Export to nested dictionary.

        :return: Nested dictionary

        NOTE: Unflattening is not yet implemented.
        """
        return self.nested_dict

    def to_csv(self, filepath, enriched=False, **kwargs):
        """
        Export the flattened data to a CSV file.

        :param filepath: Path to save the CSV file
        :param enriched: If True, include Example and Description columns (requires schema_dir)
        :param kwargs: Additional arguments passed to pandas.DataFrame.to_csv

        EXAMPLES::

            >>> import os
            >>> os.makedirs('generated/doctests', exist_ok=True)
            >>> data = {'experiment': 'test', 'value': 42}
            >>> converter = MetadataConverter.from_dict(data)
            >>> converter.to_csv('generated/doctests/example.csv')
            >>> os.path.exists('generated/doctests/example.csv')
            True
        """
        df = self.enriched_df if enriched else self.df
        df.to_csv(filepath, index=False, **kwargs)

    def to_excel(self, filepath, separate_sheets=False, enriched=False, **kwargs):
        """
        Export the flattened data to an Excel file.

        :param filepath: Path to save the Excel file
        :param separate_sheets: If True, create separate sheets for each top-level key
        :param enriched: If True, include Example and Description columns (requires schema_dir)
        :param kwargs: Additional arguments passed to pandas.DataFrame.to_excel

        When separate_sheets=True, the Excel file will have one sheet per top-level
        key in the nested structure, making it easier to navigate large metadata files.

        EXAMPLES::

            >>> import os
            >>> os.makedirs('generated/doctests', exist_ok=True)
            >>> data = {'experiment': {'value': 42, 'units': 'mV'}, 'source': {'author': 'test'}}
            >>> converter = MetadataConverter.from_dict(data)
            >>> converter.to_excel('generated/doctests/example_single.xlsx')
            >>> os.path.exists('generated/doctests/example_single.xlsx')
            True
            >>> converter.to_excel('generated/doctests/example_multi.xlsx', separate_sheets=True)
            >>> os.path.exists('generated/doctests/example_multi.xlsx')
            True
        """
        df = self.enriched_df if enriched else self.df

        if not separate_sheets:
            # Single sheet export (original behavior)
            df.to_excel(filepath, index=False, **kwargs)
        else:
            # Multi-sheet export: one sheet per top-level key
            with pd.ExcelWriter(filepath, engine="openpyxl") as writer:
                # Group rows by top-level key
                df_copy = df.copy()

                # Extract top-level number (e.g., "1" from "1.2.a")
                df_copy["TopLevel"] = (
                    df_copy["Number"].astype(str).str.split(".").str[0]
                )

                for top_level in df_copy["TopLevel"].unique():
                    # Get all rows for this top-level key
                    sheet_df = df_copy[df_copy["TopLevel"] == top_level].copy()

                    # Get sheet name from the first row's key
                    sheet_name = sheet_df.iloc[0]["Key"]
                    if not sheet_name:  # Handle empty key names
                        sheet_name = f"Sheet_{top_level}"

                    # Sanitize sheet name (Excel limits: 31 chars, no special chars)
                    sheet_name = str(sheet_name)[:31]
                    sheet_name = (
                        sheet_name.replace("/", "_")
                        .replace("\\", "_")
                        .replace("[", "(")
                        .replace("]", ")")
                    )

                    # Remove the TopLevel helper column
                    if enriched:
                        sheet_df = sheet_df[
                            ["Number", "Key", "Value", "Example", "Description"]
                        ]
                    else:
                        sheet_df = sheet_df[["Number", "Key", "Value"]]

                    # Write to sheet
                    sheet_df.to_excel(writer, sheet_name=sheet_name, index=False)

    def to_markdown(self, enriched=False, **kwargs):
        """
        Export the flattened data as a Markdown table.

        :param enriched: If True, include Example and Description columns (requires schema_dir)
        :param kwargs: Additional arguments passed to pandas.DataFrame.to_markdown
        :return: Markdown-formatted string

        EXAMPLES::

            >>> data = {'name': 'test', 'foo': ['a', 'b', 'c']}
            >>> converter = MetadataConverter.from_dict(data)
            >>> print(converter.to_markdown()) # doctest: +NORMALIZE_WHITESPACE
            | Number   | Key   | Value    |
            |:---------|:------|:---------|
            | 1        | name  | test     |
            | 2        | foo   | <nested> |
            | 2.a      |       | a        |
            | 2.b      |       | b        |
            | 2.c      |       | c        |
        """
        df = self.enriched_df if enriched else self.df
        return df.to_markdown(index=False, **kwargs)
