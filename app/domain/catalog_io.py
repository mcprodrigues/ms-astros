"""Reading catalog CSV files into the canonical movie model."""

from pathlib import Path
from typing import IO

import pandas as pd

from app.domain.errors import InvalidCatalogError
from app.domain.movie import CatalogParseResult, parse_catalog


def read_catalog_csv(source: str | Path | IO) -> CatalogParseResult:
    """
    Read a catalog CSV (path or file-like). Every cell is read as text; blanks stay ''.
    Raises InvalidCatalogError when the file is not a readable UTF-8 CSV.
    """
    try:
        df = pd.read_csv(source, dtype=str, keep_default_na=False, encoding="utf-8")
    except (pd.errors.ParserError, pd.errors.EmptyDataError, UnicodeDecodeError) as e:
        raise InvalidCatalogError(f"Unreadable catalog CSV: {type(e).__name__}") from e
    return parse_catalog(df.columns, df.to_dict(orient="records"))
