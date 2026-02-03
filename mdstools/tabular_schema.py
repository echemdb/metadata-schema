import string



# Helper to check if a list contains only primitive values
def is_primitive_list(lst):
    return all(not isinstance(x, (dict, list)) for x in lst)

# Flatten YAML with letters for list items at first sublevel
def flatten_yaml(d, prefix="", parent_key=None):
    rows = []

    if isinstance(d, dict):
        if parent_key:
            rows.append([prefix, parent_key, "<nested>", ""])
        for i, (k, v) in enumerate(d.items(), start=1):
            current_prefix = f"{prefix}.{i}" if prefix else str(i)
            if isinstance(v, dict):
                rows.extend(flatten_yaml(v, current_prefix, k))
            elif isinstance(v, list):
                if is_primitive_list(v):
                    rows.append([current_prefix, k, ", ".join(map(str, v)), ""])
                else:
                    # Use letters for first-level list items
                    for j, item in enumerate(v):
                        letter = string.ascii_lowercase[j]
                        list_prefix = f"{current_prefix}.{letter}"
                        if isinstance(item, dict):
                            rows.append([list_prefix, "", "<nested>", ""])
                            for k_idx, (field, val) in enumerate(item.items(), start=1):
                                field_prefix = f"{list_prefix}.{k_idx}"
                                rows.append([field_prefix, field, val, ""])
                        else:
                            rows.append([list_prefix, "", item, ""])
            else:
                rows.append([current_prefix, k, v, ""])
    elif isinstance(d, list):
        if parent_key:
            rows.append([prefix, parent_key, "<nested>", ""])
        for i, item in enumerate(d):
            current_prefix = f"{prefix}.{i+1}" if prefix else str(i+1)
            if isinstance(item, dict) or isinstance(item, list):
                rows.extend(flatten_yaml(item, current_prefix))
            else:
                rows.append([current_prefix, "", item, ""])
    return rows
