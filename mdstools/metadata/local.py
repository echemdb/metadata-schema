"""Shared utilities for loading and saving metadata to local files."""

import os
import pandas as pd


def load_excel_all_sheets(filepath: str, **kwargs) -> pd.DataFrame:
    """
    Load an Excel file, automatically handling both single-sheet and multi-sheet files.

    If the file has multiple sheets, reads all sheets and concatenates them into
    a single DataFrame. All sheets must have the same column structure.

    :param filepath: Path to Excel file
    :param kwargs: Additional arguments passed to pandas.read_excel
    :return: DataFrame with all data (single sheet or concatenated from multiple sheets)

    EXAMPLES::

        >>> import pandas as pd
        >>> from mdstools.metadata.local import load_excel_all_sheets, save_excel_multi_sheet
        >>> import os
        >>> # Create and save multi-sheet Excel file
        >>> data = {
        ...     'Number': ['1', '1.1', '2', '2.1', '2.2'],
        ...     'Key': ['experiment', 'value', 'source', 'author', 'year'],
        ...     'Value': ['<nested>', 42, '<nested>', 'John', 2024]
        ... }
        >>> df = pd.DataFrame(data)
        >>> save_excel_multi_sheet(df, 'tests/generated/docstrings/multi_load_test.xlsx',
        ...                         ['Number', 'Key', 'Value'])
        >>> # Load it back (automatically handles multiple sheets)
        >>> loaded_df = load_excel_all_sheets('tests/generated/docstrings/multi_load_test.xlsx')
        >>> len(loaded_df) == len(df)
        True
        >>> list(loaded_df.columns) == ['Number', 'Key', 'Value']
        True
    """
    # Read Excel file to check number of sheets
    excel_file = pd.ExcelFile(filepath)
    sheet_names = excel_file.sheet_names

    if len(sheet_names) == 1:
        # Single sheet - read normally
        return pd.read_excel(filepath, **kwargs)

    # Multiple sheets - read and concatenate all
    dfs = []
    for sheet_name in sheet_names:
        df = pd.read_excel(filepath, sheet_name=sheet_name, **kwargs)
        dfs.append(df)

    # Concatenate all sheets into a single DataFrame
    combined_df = pd.concat(dfs, ignore_index=True)
    return combined_df


def save_excel_multi_sheet(df: pd.DataFrame, filepath: str, column_order: list[str]):
    """
    Save a DataFrame to Excel with separate sheets for each top-level key.

    This function groups rows by their top-level number (e.g., "1" from "1.2.a")
    and creates a separate sheet for each group, using the top-level key as the sheet name.

    :param df: DataFrame with columns ['Number', 'Key', 'Value', ...optional enrichment columns]
    :param filepath: Path to save the Excel file
    :param column_order: List of column names in the desired order (e.g., ['Number', 'Key', 'Value'])

    EXAMPLES::

        >>> import pandas as pd
        >>> from mdstools.metadata.local import save_excel_multi_sheet
        >>> import os
        >>> # Create sample flattened data with multiple top-level keys
        >>> data = {
        ...     'Number': ['1', '1.1', '2', '2.1', '2.2'],
        ...     'Key': ['experiment', 'value', 'source', 'author', 'year'],
        ...     'Value': ['<nested>', 42, '<nested>', 'John', 2024]
        ... }
        >>> df = pd.DataFrame(data)
        >>> save_excel_multi_sheet(df, 'tests/generated/docstrings/multi_sheet_save.xlsx',
        ...                         ['Number', 'Key', 'Value'])
        >>> os.path.exists('tests/generated/docstrings/multi_sheet_save.xlsx')
        True
    """
    # Create parent directory if needed
    if isinstance(filepath, str):
        os.makedirs(os.path.dirname(filepath) or ".", exist_ok=True)

    with pd.ExcelWriter(filepath, engine="openpyxl") as writer:
        # Extract top-level number (e.g., "1" from "1.2.a")
        df_copy = df.copy()
        df_copy["TopLevel"] = df_copy["Number"].astype(str).str.split(".").str[0]

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

            # Remove the TopLevel helper column and reorder
            sheet_df = sheet_df[column_order]

            # Write to sheet
            sheet_df.to_excel(writer, sheet_name=sheet_name, index=False)


def save_csv_with_path_creation(
    df: pd.DataFrame, filepath: str, **kwargs
) -> None:
    """
    Save a DataFrame to CSV with automatic parent directory creation.

    :param df: DataFrame to save
    :param filepath: Path to save CSV file
    :param kwargs: Additional arguments passed to pandas.DataFrame.to_csv
    """
    if isinstance(filepath, str):
        os.makedirs(os.path.dirname(filepath) or ".", exist_ok=True)
    df.to_csv(filepath, index=False, **kwargs)


def save_excel_with_optional_sheets(
    df: pd.DataFrame,
    filepath: str,
    column_order: list[str],
    separate_sheets: bool = False,
    **kwargs,
) -> None:
    """
    Save a DataFrame to Excel, optionally with separate sheets per top-level key.

    :param df: DataFrame to save
    :param filepath: Path to save Excel file
    :param column_order: List of column names in desired order
    :param separate_sheets: If True, create separate sheets for each top-level key
    :param kwargs: Additional arguments passed to pandas.DataFrame.to_excel
    """
    if not separate_sheets:
        # Single sheet export
        if isinstance(filepath, str):
            os.makedirs(os.path.dirname(filepath) or ".", exist_ok=True)
        df.to_excel(filepath, index=False, **kwargs)
    else:
        # Multi-sheet export: one sheet per top-level key
        save_excel_multi_sheet(df, filepath, column_order)
