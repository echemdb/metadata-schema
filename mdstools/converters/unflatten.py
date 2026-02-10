"""Functions for unflattening tabular data back into nested structures."""


def unflatten(rows):
    """
    Reconstruct a nested dictionary from flattened rows.

    :param rows: List of [number, key, value] rows
    :return: Reconstructed nested dictionary

    >>> flattened_metadata = [['number', 'key', 'value'],
    ... ['1', 'experiment', '<nested>'],
    ... ['1.a', '', '<nested>'],
    ... ['1.a.1', 'A', '<nested>'],
    ... ['1.a.1.1', 'value', 1],
    ... ['1.a.1.2', 'units', 'mV'],
    ... ['1.a.2', 'B', 2],
    ... ['1.b', '', '<nested>'],
    ... ['1.b.1', 'A', 3],
    ... ['1.b.2', 'B', 4]]
    >>> unflatten(flattened_metadata) # doctest: +ELLIPSIS
    {'experiment': [{'A': {'value': 1, 'units': 'mV'}, 'B': 2}, {'A': 3, 'B': 4}]}

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
    for number in tree:
        parts = number.split(".")
        if len(parts) > 1:
            parent_number = ".".join(parts[:-1])
            if parent_number in tree:
                tree[parent_number]["children"][number] = tree[number]

    # Find root entries (no parent or parent not in tree)
    roots = []
    for number in tree:
        parts = number.split(".")
        if len(parts) == 1 or ".".join(parts[:-1]) not in tree:
            roots.append(number)

    def is_list_index(s):
        """Check if string is a single letter (a-z)"""
        return len(s) == 1 and s.isalpha()

    def build_structure(number):
        """Recursively build the nested structure"""
        node = tree[number]
        key = node["key"]
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
        else:
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
