"""Metadata class for handling nested dictionary/YAML metadata structures."""

import os

import yaml

from mdstools.converters.flatten import flatten


class Metadata:
    """
    Wrapper for nested dictionary metadata structures.

    Provides methods to load from YAML and convert to flattened tabular format.

    EXAMPLES::

        >>> from mdstools.metadata.metadata import Metadata
        >>> data = {'name': 'test', 'value': 42}
        >>> metadata = Metadata(data)
        >>> isinstance(metadata.data, dict)
        True
        >>> metadata.data['name']
        'test'
    """

    def __init__(self, metadata: dict):
        """
        Initialize with a nested dictionary.

        :param metadata: Nested dictionary containing metadata
        """
        if not isinstance(metadata, dict):
            raise TypeError(f"Expected dict, got {type(metadata).__name__}")
        self._data = metadata

    @property
    def data(self) -> dict:
        """Get the underlying metadata dictionary."""
        return self._data

    @classmethod
    def from_yaml(cls, filepath: str):
        """
        Load metadata from a YAML file.

        :param filepath: Path to YAML file
        :return: Metadata instance

        EXAMPLES::

            >>> # metadata = Metadata.from_yaml('examples/objects/system.yaml')
            >>> # isinstance(metadata, Metadata)
            >>> # True
            >>> pass  # Placeholder for file-based test
        """
        with open(filepath, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return cls(data)

    def flatten(self):
        """
        Convert to flattened tabular representation.

        :return: FlattenedMetadata instance

        EXAMPLES::

            Nested dictionaries:

            >>> from mdstools.metadata.metadata import Metadata
            >>> data = {'experiment': {'value': 42, 'units': 'mV'}}
            >>> metadata = Metadata(data)
            >>> flattened = metadata.flatten()
            >>> flattened.rows # doctest: +NORMALIZE_WHITESPACE
            [['1', 'experiment', '<nested>'],
             ['1.1', 'value', 42],
             ['1.2', 'units', 'mV']]

            Lists of dictionaries:

            >>> data = {'measurements': [{'A': 1, 'B': 2}, {'A': 3, 'B': 4}]}
            >>> metadata = Metadata(data)
            >>> flattened = metadata.flatten()
            >>> len(flattened.rows)
            7
            >>> flattened.rows[0]
            ['1', 'measurements', '<nested>']
        """
        from mdstools.metadata.flattened_metadata import FlattenedMetadata

        rows = flatten(self._data)
        return FlattenedMetadata(rows)

    def to_yaml(self, filepath: str):
        """
        Save metadata to a YAML file.

        :param filepath: Path to save YAML file

        EXAMPLES::

            Basic save:\n\n            >>> from mdstools.metadata.metadata import Metadata
            >>> import os
            >>> data = {'name': 'test', 'value': 42}
            >>> metadata = Metadata(data)
            >>> metadata.to_yaml('tests/generated/docstrings/test_metadata.yaml')
            >>> os.path.exists('tests/generated/docstrings/test_metadata.yaml')
            True

            Test roundtrip (dict → YAML → dict):

            >>> data = {'experiment': {'value': 42, 'units': 'mV'}, 'author': 'test'}
            >>> metadata = Metadata(data)
            >>> metadata.to_yaml('tests/generated/docstrings/roundtrip.yaml')
            >>> loaded = Metadata.from_yaml('tests/generated/docstrings/roundtrip.yaml')
            >>> loaded.data == data
            True
        """
        if isinstance(filepath, str):
            os.makedirs(os.path.dirname(filepath) or ".", exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            yaml.safe_dump(self._data, f, default_flow_style=False, sort_keys=False)
