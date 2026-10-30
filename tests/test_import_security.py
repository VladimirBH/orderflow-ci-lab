import pytest

from orderflow.imports import read_document


def test_read_document_inside_storage(tmp_path):
    storage = tmp_path / "storage"
    documents = storage / "invoices"
    documents.mkdir(parents=True)

    document = documents / "invoice.txt"
    document.write_text("Order #42", encoding="utf-8")

    result = read_document(
        str(storage),
        "invoices",
        "invoice.txt",
    )

    assert result == "Order #42"


def test_rejects_path_traversal(tmp_path):
    storage = tmp_path / "storage"
    storage.mkdir()

    secret = tmp_path / "secret.txt"
    secret.write_text("CONFIDENTIAL", encoding="utf-8")

    with pytest.raises(ValueError):
        read_document(
            str(storage),
            "..",
            "secret.txt",
        )


def test_rejects_missing_document(tmp_path):
    storage = tmp_path / "storage"
    storage.mkdir()

    with pytest.raises(FileNotFoundError):
        read_document(
            str(storage),
            "invoices",
            "missing.txt",
        )