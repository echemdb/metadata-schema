"""Functions for unflattening tabular data back into nested structures."""

# ********************************************************************
#  This file is part of mdstools.
#
#        Copyright (C) 2026 Albert Engstfeld
#
#  mdstools is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  mdstools is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with mdstools. If not, see <https://www.gnu.org/licenses/>.
# ********************************************************************


def _build_tree(rows):
    r"""
    Build a tree structure from flattened rows, synthesizing missing parents.

    :param rows: List of [number, key, value] rows (no header)
    :return: Tuple of (tree dict, list of root number strings)

    EXAMPLES:

        Simple rows produce a tree with one root::

            >>> from mdstools.converters.unflatten import _build_tree
            >>> rows = [['1', 'name', 'test'], ['2', 'value', 42]]
            >>> tree, roots = _build_tree(rows)
            >>> sorted(roots)
            ['1', '2']
            >>> tree['1']['key']
            'name'

        Missing intermediate ``i<n>`` parents are synthesized automatically::

            >>> rows = [['1', 'items', '<nested>'],
            ...         ['1.i1.1', 'A', 1]]
            >>> tree, roots = _build_tree(rows)
            >>> '1.i1' in tree  # virtual node created
            True
            >>> tree['1.i1']['key']
            ''
    """
    tree = {}
    for number, key, value in rows:
        number = str(number)
        tree[number] = {"key": key, "value": value, "children": {}}

    # Synthesize virtual nodes for missing intermediate i<n> parents.
    # When dict items inside lists are flattened without an explicit row
    # for the list-item index (e.g. "1.i1"), the children ("1.i1.1", ...)
    # would be orphaned.  Create the missing parent so the tree stays
    # connected.
    for number in list(tree.keys()):
        parts = number.split(".")
        if len(parts) > 1:
            parent_number = ".".join(parts[:-1])
            if parent_number not in tree:
                tree[parent_number] = {"key": "", "value": "<nested>", "children": {}}

    # Link parent-child relationships
    for number, node in tree.items():
        parts = number.split(".")
        if len(parts) > 1:
            parent_number = ".".join(parts[:-1])
            if parent_number in tree:
                tree[parent_number]["children"][number] = node

    # Find root entries (no parent or parent not in tree)
    roots = []
    for number in tree:
        parts = number.split(".")
        if len(parts) == 1 or ".".join(parts[:-1]) not in tree:
            roots.append(number)

    return tree, roots


def _is_list_index(s):
    r"""
    Check if string is an item index (``i<n>`` format, e.g. i1, i2, i3).

    The function inspects the last segment of a dotted number to decide
    whether it represents a list item.  Only strings starting with ``i``
    followed by one or more digits are accepted.

    :param s: A string segment (e.g. ``"i1"``, ``"i12"``, ``"3"``)
    :return: ``True`` if *s* matches the ``i<n>`` pattern

    EXAMPLES:

        Valid list indices::

            >>> from mdstools.converters.unflatten import _is_list_index
            >>> _is_list_index('i1')
            True
            >>> _is_list_index('i12')
            True
            >>> _is_list_index('i999')
            True

        Numeric dict keys are **not** list indices::

            >>> _is_list_index('1')
            False
            >>> _is_list_index('10')
            False

        Other non-matching strings::

            >>> _is_list_index('')
            False
            >>> _is_list_index('i')
            False
            >>> _is_list_index('item')
            False
    """
    return len(s) >= 2 and s[0] == "i" and s[1:].isdigit()


def _build_structure(tree, number):
    r"""
    Recursively build a nested structure from a tree node.

    Walks the tree produced by :func:`_build_tree`, returning the
    reconstructed Python object for the subtree rooted at *number*.

    :param tree: The full tree dict (as returned by :func:`_build_tree`)
    :param number: The node number to start building from
    :return: A dict, list, or scalar value

    EXAMPLES:

        Dict node::

            >>> from mdstools.converters.unflatten import _build_tree, _build_structure
            >>> rows = [['1', 'x', '<nested>'], ['1.1', 'a', 1], ['1.2', 'b', 2]]
            >>> tree, roots = _build_tree(rows)
            >>> _build_structure(tree, '1')
            {'a': 1, 'b': 2}

        List node::

            >>> rows = [['1', 'tags', '<nested>'],
            ...         ['1.i1', '', 'alpha'],
            ...         ['1.i2', '', 'beta']]
            >>> tree, roots = _build_tree(rows)
            >>> _build_structure(tree, '1')
            ['alpha', 'beta']

        Leaf node returns the scalar value::

            >>> rows = [['1', 'name', 'test']]
            >>> tree, roots = _build_tree(rows)
            >>> _build_structure(tree, '1')
            'test'
    """
    node = tree[number]
    value = node["value"]
    children = node["children"]

    if not children:
        return value

    child_numbers = sorted(children.keys(), key=lambda x: x.split(".")[-1])
    child_suffixes = [num.split(".")[-1] for num in child_numbers]

    if all(_is_list_index(suffix) for suffix in child_suffixes):
        return [_build_structure(tree, child_num) for child_num in child_numbers]

    result_dict = {}
    for child_num in child_numbers:
        child_node = tree[child_num]
        child_key = child_node["key"]
        child_result = _build_structure(tree, child_num)

        if child_key:
            result_dict[child_key] = child_result
        else:
            result_dict = (
                child_result if isinstance(child_result, dict) else result_dict
            )
    return result_dict


def unflatten(rows):
    r"""
    Reconstruct a nested dictionary from flattened rows.

    Takes a list of ``[number, key, value]`` rows produced by
    :func:`~mdstools.converters.flatten.flatten` and rebuilds the original
    nested dictionary.  Header rows (``['number', 'key', 'value']``) are
    automatically detected and skipped.

    :param rows: List of [number, key, value] rows
    :return: Reconstructed nested dictionary

    EXAMPLES:

        Simple key-value pairs::

            >>> from mdstools.converters.unflatten import unflatten
            >>> rows = [['1', 'name', 'test'], ['2', 'value', 42]]
            >>> unflatten(rows)
            {'name': 'test', 'value': 42}

        Nested dictionaries::

            >>> rows = [['1', 'experiment', '<nested>'],
            ...         ['1.1', 'value', 42],
            ...         ['1.2', 'units', 'mV']]
            >>> unflatten(rows)
            {'experiment': {'value': 42, 'units': 'mV'}}

        Lists of dictionaries (item-indexed with i<n>)::

            >>> rows = [['1', 'people', '<nested>'],
            ...         ['1.i1.1', 'name', 'Alice'],
            ...         ['1.i1.2', 'role', 'curator'],
            ...         ['1.i2.1', 'name', 'Bob'],
            ...         ['1.i2.2', 'role', 'reviewer']]
            >>> unflatten(rows)
            {'people': [{'name': 'Alice', 'role': 'curator'}, {'name': 'Bob', 'role': 'reviewer'}]}

        Primitive lists::

            >>> rows = [['1', 'tags', '<nested>'],
            ...         ['1.i1', '', 'alpha'],
            ...         ['1.i2', '', 'beta'],
            ...         ['1.i3', '', 'gamma']]
            >>> unflatten(rows)
            {'tags': ['alpha', 'beta', 'gamma']}

        Mixed nested structures (dicts inside lists inside dicts)::

            >>> rows = [['1', 'experiment', '<nested>'],
            ...         ['1.i1.1', 'A', '<nested>'],
            ...         ['1.i1.1.1', 'value', 1],
            ...         ['1.i1.1.2', 'units', 'mV'],
            ...         ['1.i1.2', 'B', 2],
            ...         ['1.i2.1', 'A', 3],
            ...         ['1.i2.2', 'B', 4]]
            >>> unflatten(rows)
            {'experiment': [{'A': {'value': 1, 'units': 'mV'}, 'B': 2}, {'A': 3, 'B': 4}]}

        Header rows are automatically skipped::

            >>> rows = [['number', 'key', 'value'],
            ...         ['1', 'name', 'test']]
            >>> unflatten(rows)
            {'name': 'test'}

        Empty input returns an empty dict::

            >>> unflatten([])
            {}

        Roundtrip with :func:`~mdstools.converters.flatten.flatten`::

            >>> from mdstools.converters.flatten import flatten
            >>> original = {'curation': {'process': [{'role': 'curator', 'name': 'Jane'}]}}
            >>> unflatten(flatten(original)) == original
            True

    """
    if not rows:
        return {}

    # Skip header row if present (check if first row is ['number', 'key', 'value'] or similar)
    if rows and len(rows[0]) >= 2:
        first_row_lower = [str(x).lower() for x in rows[0]]
        if "number" in first_row_lower and "key" in first_row_lower:
            rows = rows[1:]

    if not rows:
        return {}

    result = {}
    tree, roots = _build_tree(rows)

    # Build the root result
    for root_number in roots:
        root_node = tree[root_number]
        root_key = root_node["key"]
        if root_key:
            result[root_key] = _build_structure(tree, root_number)

    return result
