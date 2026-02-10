"""Metadata classes for handling nested and tabular metadata structures."""

from mdstools.metadata.metadata import Metadata
from mdstools.metadata.flattened_metadata import FlattenedMetadata
from mdstools.metadata.enriched_metadata import EnrichedFlattenedMetadata

__all__ = ['Metadata', 'FlattenedMetadata', 'EnrichedFlattenedMetadata']
