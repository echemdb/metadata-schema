"""Functions for unflattening tabular data back into nested structures."""


def unflatten(rows):
    r"""
    Reconstruct a nested dictionary from flattened rows.

    Takes a list of ``[number, key, value]`` rows produced by
    :func:`~mdstools.converters.flatten.flatten` and rebuilds the original
    nested dictionary.  Header rows (``['number', 'key', 'value']``) are
    automatically detected and skipped.

    :param rows: List of [number, key, value] rows
    :return: Reconstructed nested dictionary

    EXAMPLES::

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
            ...         ['1.i1', '', '<nested>'],
            ...         ['1.i1.1', 'name', 'Alice'],
            ...         ['1.i1.2', 'role', 'curator'],
            ...         ['1.i2', '', '<nested>'],
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
            ...         ['1.i1', '', '<nested>'],
            ...         ['1.i1.1', 'A', '<nested>'],
            ...         ['1.i1.1.1', 'value', 1],
            ...         ['1.i1.1.2', 'units', 'mV'],
            ...         ['1.i1.2', 'B', 2],
            ...         ['1.i2', '', '<nested>'],
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

    # Build a tree structure from the rows
    tree = {}
    for number, key, value in rows:
        # Ensure number is a string (pandas may read as float)
        number = str(number)
        tree[number] = {"key": key, "value": value, "children": {}}

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

    def is_list_index(s):
        """Check if string is an item index (i<n> format, e.g. i1, i2, i3)."""
        return len(s) >= 2 and s[0] == 'i' and s[1:].isdigit()

    def build_structure(number):
        """Recursively build the nested structure"""
        node = tree[number]
        _key = node["key"]  # Extracted but not used in this function
        value = node["value"]
        children = node["children"]

        if not children:
            # Leaf node - return the value
            return value

        # Check if children are list items (have letter suffixes)
        child_numbers = sorted(children.keys(), key=lambda x: x.split(".")[-1])
        child_suffixes = [num.split(".")[-1] for num in child_numbers]

        if all(is_list_index(suffix) for suffix in child_suffixes):
            # This is a list
            result_list = []
            for child_num in child_numbers:
                child_result = build_structure(child_num)
                result_list.append(child_result)
            return result_list

        # This is a dict
        result_dict = {}
        for child_num in child_numbers:
            child_node = tree[child_num]
            child_key = child_node["key"]
            child_result = build_structure(child_num)

            if child_key:  # Non-empty key
                result_dict[child_key] = child_result
            else:  # Empty key means inherit from parent or it's a list item
                # This shouldn't happen at dict level, but handle it
                result_dict = (
                    child_result if isinstance(child_result, dict) else result_dict
                )
        return result_dict

    # Build the root result
    for root_number in roots:
        root_node = tree[root_number]
        root_key = root_node["key"]
        if root_key:
            result[root_key] = build_structure(root_number)

    return result
