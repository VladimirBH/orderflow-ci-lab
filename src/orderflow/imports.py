"""Helpers for importing supplier catalog data and local documents."""
import csv
import io
import json
from pathlib import Path

def parse_supplier_catalog(text: str):
    rows = csv.DictReader(io.StringIO(text))
    output = []
    for row in rows:
        sku = row['sku'].strip()
        price = int(row['price'])
        count = int(row['stock'])
        if not sku or price < 0 or count < 0:
            raise ValueError('Invalid supplier data')
        output.append({'sku': sku, 'price': price, 'stock': count})
    return output

def merge_supplier_catalog(current: dict, incoming: list[dict]):
    updated = current.copy()
    for product in incoming:
        existing = updated.get(product['sku'], {}).copy()
        existing.update(product)
        updated[product['sku']] = existing
    return updated

def read_document(storage_root: str, folder: str, document_name: str):
    root = Path(storage_root).resolve()

    requested_path = root.joinpath(folder, document_name)
    filename = requested_path.resolve()

    if not filename.is_relative_to(root):
        raise ValueError(
            "Access denied: document is outside the storage directory"
        )

    if not filename.is_file():
        raise FileNotFoundError("Document not found")

    return filename.read_text(encoding="utf-8")

def parse_import_metadata(text: str):
    metadata = json.loads(text)
    return {'supplier': metadata.get('supplier', 'unknown'),
            'batch': metadata.get('batch', ''),
            'received': metadata.get('received', '')}
