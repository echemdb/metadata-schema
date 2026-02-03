import string
import pandas as pd


# Helper to check if a list contains only primitive values
def is_primitive_list(lst):
    return all(not isinstance(x, (dict, list)) for x in lst)


def _process_dict(d, prefix, parent_key, rows):
    """
    Process a dictionary and add rows for its key-value pairs.

    :param d: The dictionary to process
    :param prefix: The current numbering prefix (e.g., "1.2")
    :param parent_key: The parent key name (if nested)
    :param rows: The list to append rows to
    """
    if parent_key:
        rows.append([prefix, parent_key, "<nested>"])

    for i, (k, v) in enumerate(d.items(), start=1):
        current_prefix = f"{prefix}.{i}" if prefix else str(i)

        if isinstance(v, dict):
            _process_dict(v, current_prefix, k, rows)
        elif isinstance(v, list):
            _process_list(v, current_prefix, k, rows)
        else:
            rows.append([current_prefix, k, v])


def _process_list(lst, prefix, parent_key, rows):
    """
    Process a list and add rows for its items.

    :param lst: The list to process
    :param prefix: The current numbering prefix (e.g., "1")
    :param parent_key: The parent key name
    :param rows: The list to append rows to
    """
    # All lists get the parent row with <nested>
    rows.append([prefix, parent_key, "<nested>"])

    # Process each list item with letter suffixes (a, b, c, ...)
    for j, item in enumerate(lst):
        letter = string.ascii_lowercase[j]
        list_prefix = f"{prefix}.{letter}"

        if isinstance(item, dict):
            rows.append([list_prefix, "", "<nested>"])
            for k_idx, (field, val) in enumerate(item.items(), start=1):
                field_prefix = f"{list_prefix}.{k_idx}"
                if isinstance(val, dict):
                    _process_dict(val, field_prefix, field, rows)
                elif isinstance(val, list):
                    _process_list(val, field_prefix, field, rows)
                else:
                    rows.append([field_prefix, field, val])
        elif isinstance(item, list):
            _process_list(item, list_prefix, "", rows)
        else:
            rows.append([list_prefix, "", item])


def flatten_yaml(d, prefix="", parent_key=None):
    """
    Flatten a nested YAML structure into a tabular format with numbered rows.

    :param d: The data structure to flatten (dict or list)
    :param prefix: The current numbering prefix (default: "")
    :param parent_key: The parent key name (default: None)
    :return: A list of rows, each containing [number, key, value]

    EXAMPLES::

    Simple key-value pairs::

        >>> data = {
        ...     'experiment': 'abc'}
        >>> flatten_yaml(data) # doctest: +NORMALIZE_WHITESPACE
        [['1', 'experiment', 'abc']]

        >>> data = {
        ...     'experiment': 'abc',
        ...     'details': 'foo'}
        >>> flatten_yaml(data) # doctest: +NORMALIZE_WHITESPACE
        [['1', 'experiment', 'abc'],
         ['2', 'details', 'foo']]

    Nested dictionaries::

        >>> data = {
        ...     'experiment': {'value': 42, 'units': 'mV'}}
        >>> flatten_yaml(data) # doctest: +NORMALIZE_WHITESPACE
        [['1', 'experiment', '<nested>'],
         ['1.1', 'value', 42],
         ['1.2', 'units', 'mV']]

    Lists of dictionaries::

        >>> data = {
        ...     'experiment': [{'A': 1, 'B': 2}, {'A': 3, 'B': 4}]}
        >>> flatten_yaml(data) # doctest: +NORMALIZE_WHITESPACE
        [['1', 'experiment', '<nested>'],
         ['1.a', '', '<nested>'],
         ['1.a.1', 'A', 1],
         ['1.a.2', 'B', 2],
         ['1.b', '', '<nested>'],
         ['1.b.1', 'A', 3],
         ['1.b.2', 'B', 4]]

    Primitive lists::

        >>> data = {
        ...     'measurements': ['A', 'B', 'C']}
        >>> flatten_yaml(data) # doctest: +NORMALIZE_WHITESPACE
        [['1', 'measurements', '<nested>'],
         ['1.a', '', 'A'],
         ['1.b', '', 'B'],
         ['1.c', '', 'C']]

    Mixed nested structures::

        >>> data = {
        ...     'experiment': [{'A': {'value': 1, 'units': 'mV'}, 'B': 2}, {'A': 3, 'B': 4}]}
        >>> flatten_yaml(data) # doctest: +NORMALIZE_WHITESPACE
        [['1', 'experiment', '<nested>'],
         ['1.a', '', '<nested>'],
         ['1.a.1', 'A', '<nested>'],
         ['1.a.1.1', 'value', 1],
         ['1.a.1.2', 'units', 'mV'],
         ['1.a.2', 'B', 2],
         ['1.b', '', '<nested>'],
         ['1.b.1', 'A', 3],
         ['1.b.2', 'B', 4]]

    """

    rows = []

    if isinstance(d, dict):
        _process_dict(d, prefix, parent_key, rows)
    elif isinstance(d, list):
        _process_list(d, prefix, parent_key if parent_key else "", rows)

    return rows


def unflatten_yaml(rows):
    """
    Reconstruct a nested dictionary from flattened rows.

    :param rows: List of [number, key, value] rows
    :return: Reconstructed nested dictionary

    NOTE: This is a placeholder for the reverse conversion.
    Implementation will be added in a future iteration.
    """
    # TODO: Implement the reverse logic
    raise NotImplementedError("Unflattening logic not yet implemented")


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

    def __init__(self, source_data, source_type='dict'):
        """
        Initialize converter with data from either format.

        :param source_data: The data to convert (dict, list, or DataFrame)
        :param source_type: 'dict' for nested dict/list, 'flattened' for tabular data
        """
        self._source_data = source_data
        self._source_type = source_type
        self._flattened = None
        self._nested = None
        self._df = None

    @classmethod
    def from_dict(cls, data):
        """
        Create a converter from a nested dictionary.

        :param data: The nested dictionary to convert
        :return: MetadataConverter instance

        EXAMPLES::

            >>> data = {'name': 'test', 'value': 123}
            >>> converter = MetadataConverter.from_dict(data)
            >>> isinstance(converter, MetadataConverter)
            True
            >>> len(converter.flattened)
            2
        """
        return cls(data, source_type='dict')

    @classmethod
    def from_excel(cls, filepath, **kwargs):
        """
        Create a converter from a flattened Excel file.

        :param filepath: Path to the Excel file
        :param kwargs: Additional arguments passed to pandas.read_excel
        :return: MetadataConverter instance

        EXAMPLES::

            >>> # Assuming 'metadata.xlsx' exists with proper format
            >>> # converter = MetadataConverter.from_excel('metadata.xlsx')
            >>> # isinstance(converter, MetadataConverter)
            >>> # True
            >>> pass  # Placeholder for file-based test
        """
        df = pd.read_excel(filepath, **kwargs)
        return cls(df, source_type='flattened')

    @classmethod
    def from_csv(cls, filepath, **kwargs):
        """
        Create a converter from a flattened CSV file.

        :param filepath: Path to the CSV file
        :param kwargs: Additional arguments passed to pandas.read_csv
        :return: MetadataConverter instance
        """
        df = pd.read_csv(filepath, **kwargs)
        return cls(df, source_type='flattened')

    @classmethod
    def from_dataframe(cls, df):
        """
        Create a converter from a pandas DataFrame.

        :param df: DataFrame with columns ['Number', 'Key', 'Value']
        :return: MetadataConverter instance
        """
        return cls(df, source_type='flattened')

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
            if self._source_type == 'dict':
                self._flattened = flatten_yaml(self._source_data)
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
            if self._source_type == 'dict':
                self._nested = self._source_data
            else:  # source_type == 'flattened'
                self._nested = unflatten_yaml(self.flattened)
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
            if self._source_type == 'flattened' and isinstance(self._source_data, pd.DataFrame):
                self._df = self._source_data
            else:
                self._df = pd.DataFrame(
                    self.flattened,
                    columns=['Number', 'Key', 'Value']
                )
        return self._df

    def to_dict(self):
        """
        Export to nested dictionary.

        :return: Nested dictionary

        NOTE: Unflattening is not yet implemented.
        """
        return self.nested_dict

    def to_csv(self, filepath, **kwargs):
        """
        Export the flattened data to a CSV file.

        :param filepath: Path to save the CSV file
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
        self.df.to_csv(filepath, index=False, **kwargs)

    def to_excel(self, filepath, separate_sheets=False, **kwargs):
        """
        Export the flattened data to an Excel file.

        :param filepath: Path to save the Excel file
        :param separate_sheets: If True, create separate sheets for each top-level key
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
        if not separate_sheets:
            # Single sheet export (original behavior)
            self.df.to_excel(filepath, index=False, **kwargs)
        else:
            # Multi-sheet export: one sheet per top-level key
            with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
                # Group rows by top-level key
                df = self.df.copy()

                # Extract top-level number (e.g., "1" from "1.2.a")
                df['TopLevel'] = df['Number'].astype(str).str.split('.').str[0]

                for top_level in df['TopLevel'].unique():
                    # Get all rows for this top-level key
                    sheet_df = df[df['TopLevel'] == top_level].copy()

                    # Get sheet name from the first row's key
                    sheet_name = sheet_df.iloc[0]['Key']
                    if not sheet_name:  # Handle empty key names
                        sheet_name = f"Sheet_{top_level}"

                    # Sanitize sheet name (Excel limits: 31 chars, no special chars)
                    sheet_name = str(sheet_name)[:31]
                    sheet_name = sheet_name.replace('/', '_').replace('\\', '_').replace('[', '(').replace(']', ')')

                    # Remove the TopLevel helper column
                    sheet_df = sheet_df[['Number', 'Key', 'Value']]

                    # Write to sheet
                    sheet_df.to_excel(writer, sheet_name=sheet_name, index=False)

    def to_markdown(self, **kwargs):
        """
        Export the flattened data as a Markdown table.

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
        return self.df.to_markdown(index=False, **kwargs)
