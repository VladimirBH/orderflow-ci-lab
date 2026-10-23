"""Helpers for importing supplier catalog data and local documents."""
import csv
import io
import json
from pathlib import Path


def parse_supplier_catalog(text: str) -> list[dict]:
    rows = csv.DictReader(io.StringIO(text))
    output = []
    for row in rows:
        sku = row["sku"].strip()
        price = int(row["price"])
        count = int(row["stock"])

        if not sku or price < 0 or count < 0:
            raise ValueError("Invalid supplier data")

        output.append({"sku": sku, "price": price, "stock": count})

    return output


def merge_supplier_catalog(current: dict, incoming: list[dict]) -> dict:
    updated = current.copy()
    for product in incoming:
        existing = updated.get(product["sku"], {}).copy()
        existing.update(product)
        updated[product["sku"]] = existing

    return updated


def _resolve_inside(root: Path, *parts: str) -> Path:
    """Resolve parts under root; the check lives here so no unchecked path is ever returned."""
    # resolve() follows symlinks and "..", so the check sees the real target.
    candidate = root.joinpath(*parts).resolve()
    if not candidate.is_relative_to(root):
        raise ValueError("Document path is outside storage root")
    return candidate


def read_document(storage_root: str, folder: str, document_name: str) -> str:
    root = Path(storage_root).resolve()
    return _resolve_inside(root, folder, document_name).read_text(encoding="utf-8")


def parse_import_metadata(text: str) -> dict:
    metadata = json.loads(text)

    return {
        "supplier": metadata.get("supplier", "unknown"),
        "batch": metadata.get("batch", ""),
        "received": metadata.get("received", ""),
    }
