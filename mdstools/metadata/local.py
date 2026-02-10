"""Shared utilities for loading and saving metadata to local files."""

import os
import pandas as pd


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
        >>> save_excel_multi_sheet(df, 'tests/generated/docstrings/multi_sheet_test.xlsx',
        ...                         ['Number', 'Key', 'Value'])
        >>> os.path.exists('tests/generated/docstrings/multi_sheet_test.xlsx')
        True
    """
    # Create parent directory if needed
    if isinstance(filepath, str):
        os.makedirs(os.path.dirname(filepath) or '.', exist_ok=True)

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
