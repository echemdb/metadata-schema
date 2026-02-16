"""Functions for flattening nested YAML/dict structures into tabular format."""

import string


# Helper to check if a list contains only primitive values
def is_primitive_list(lst):
    r"""
    Check if a list contains only primitive values (no dicts or lists).

    Returns True if every element is a simple scalar (str, int, float, bool, None),
    and False if any element is a dict or list.

    EXAMPLES::

        Primitive lists::

            >>> from mdstools.converters.flatten import is_primitive_list
            >>> is_primitive_list(['a', 'b', 'c'])
            True
            >>> is_primitive_list([1, 2, 3])
            True
            >>> is_primitive_list([1, 'mixed', 3.14, True, None])
            True

        Non-primitive lists::

            >>> is_primitive_list([{'key': 'value'}])
            False
            >>> is_primitive_list([[1, 2], [3, 4]])
            False
            >>> is_primitive_list([1, {'nested': True}])
            False

        Edge case - empty list::

            >>> is_primitive_list([])
            True
    """
    return all(not isinstance(x, (dict, list)) for x in lst)


def _process_dict(d, prefix, parent_key, rows):
    r"""
    Process a dictionary and add rows for its key-value pairs.

    Appends ``[prefix, parent_key, '<nested>']`` for the dict itself (when
    *parent_key* is set), then recurses into each key-value pair.

    :param d: The dictionary to process
    :param prefix: The current numbering prefix (e.g., "1.2")
    :param parent_key: The parent key name (if nested)
    :param rows: The list to append rows to

    EXAMPLES::

        Top-level dict (no parent_key) — only children are emitted::

            >>> from mdstools.converters.flatten import _process_dict
            >>> rows = []
            >>> _process_dict({'a': 1, 'b': 2}, '', None, rows)
            >>> rows
            [['1', 'a', 1], ['2', 'b', 2]]

        Nested dict — a ``<nested>`` marker row is emitted first::

            >>> rows = []
            >>> _process_dict({'x': 10}, '3', 'parent', rows)
            >>> rows
            [['3', 'parent', '<nested>'], ['3.1', 'x', 10]]

        Dict containing another dict::

            >>> rows = []
            >>> _process_dict({'inner': {'v': 42}}, '1', 'outer', rows)
            >>> rows  # doctest: +NORMALIZE_WHITESPACE
            [['1', 'outer', '<nested>'],
             ['1.1', 'inner', '<nested>'],
             ['1.1.1', 'v', 42]]

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
    r"""
    Process a list and add rows for its items.

    Emits a ``<nested>`` marker row for the list, then processes each item
    with a letter suffix (``a``, ``b``, ``c``, …).

    :param lst: The list to process
    :param prefix: The current numbering prefix (e.g., "1")
    :param parent_key: The parent key name
    :param rows: The list to append rows to

    EXAMPLES::

        Primitive list::

            >>> from mdstools.converters.flatten import _process_list
            >>> rows = []
            >>> _process_list(['x', 'y'], '1', 'tags', rows)
            >>> rows  # doctest: +NORMALIZE_WHITESPACE
            [['1', 'tags', '<nested>'],
             ['1.a', '', 'x'],
             ['1.b', '', 'y']]

        List of dicts::

            >>> rows = []
            >>> _process_list([{'k': 1}, {'k': 2}], '2', 'items', rows)
            >>> rows  # doctest: +NORMALIZE_WHITESPACE
            [['2', 'items', '<nested>'],
             ['2.a', '', '<nested>'],
             ['2.a.1', 'k', 1],
             ['2.b', '', '<nested>'],
             ['2.b.1', 'k', 2]]

        Single-element list::

            >>> rows = []
            >>> _process_list([42], '5', 'single', rows)
            >>> rows
            [['5', 'single', '<nested>'], ['5.a', '', 42]]

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


def flatten(d, prefix="", parent_key=None):
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
        >>> flatten(data) # doctest: +NORMALIZE_WHITESPACE
        [['1', 'experiment', 'abc']]

        >>> data = {
        ...     'experiment': 'abc',
        ...     'details': 'foo'}
        >>> flatten(data) # doctest: +NORMALIZE_WHITESPACE
        [['1', 'experiment', 'abc'],
         ['2', 'details', 'foo']]

    Nested dictionaries::

        >>> data = {
        ...     'experiment': {'value': 42, 'units': 'mV'}}
        >>> flatten(data) # doctest: +NORMALIZE_WHITESPACE
        [['1', 'experiment', '<nested>'],
         ['1.1', 'value', 42],
         ['1.2', 'units', 'mV']]

    Lists of dictionaries::

        >>> data = {
        ...     'experiment': [{'A': 1, 'B': 2}, {'A': 3, 'B': 4}]}
        >>> flatten(data) # doctest: +NORMALIZE_WHITESPACE
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
        >>> flatten(data) # doctest: +NORMALIZE_WHITESPACE
        [['1', 'measurements', '<nested>'],
         ['1.a', '', 'A'],
         ['1.b', '', 'B'],
         ['1.c', '', 'C']]

    Mixed nested structures::

        >>> data = {
        ...     'experiment': [{'A': {'value': 1, 'units': 'mV'}, 'B': 2}, {'A': 3, 'B': 4}]}
        >>> flatten(data) # doctest: +NORMALIZE_WHITESPACE
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
