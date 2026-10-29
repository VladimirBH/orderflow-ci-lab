from datetime import date
from orderflow.accounts import Account, find_account, verify_webhook
from orderflow.analytics import popular_products, revenue_trend
from orderflow.fulfillment import Basket, Line, calculate_invoice, reserve_items
from orderflow.imports import parse_supplier_catalog, merge_supplier_catalog
from orderflow.promotions import apply_promotions
from orderflow.shipping import delivery_estimate, prepare_shipment
from orderflow.accounts import Account, update_preferences, verify_api_key
import pytest
from orderflow.imports import read_document
import hashlib
import hmac
import json
from dataclasses import asdict
from orderflow.billing import Payment, accept_payment_callback


def test_promotions():
    amount, codes = apply_promotions(4000, ['OFFICE7'], ['office'])
    assert amount == 3720
    assert codes == ['OFFICE7']


def test_shipping():
    assert delivery_estimate('local', 'parcel', 2) == 378
    assert prepare_shipment(17, 'local', 'parcel', 2, date(2026, 2, 1)).tracking_code == 'OF-000017'


def test_account_lookup():
    accounts = [Account(7, 'USER@example.test', 'user')]
    assert find_account(accounts, ' user@EXAMPLE.test ').user_id == 7
    assert not verify_webhook(b'{}', 'not-a-signature', 'secret')


def test_invoice():
    basket = Basket(1, [Line('L1', 2, 2500, 'office')], ['OFFICE7'])
    invoice = calculate_invoice(basket, 'pickup')
    assert invoice['total'] == 4650


def test_reserve():
    stock = {'SKU-1': 10, 'SKU-2': 2}
    assert reserve_items(Basket(1,[Line('SKU-1', 2, 10, 'office')]), stock)
    assert stock['SKU-1'] == 8


def test_catalog_import():
    incoming = parse_supplier_catalog('sku,price,stock\nA1,100,3\n')
    assert merge_supplier_catalog({'A1': {'title': 'X'}}, incoming)['A1']['title'] == 'X'


def test_popular_products():
    orders = [{'lines':[{'product_id':2,'quantity':3}]}]
    assert popular_products(orders) == [(2,3)]

def test_update_preferences_security():
    account = Account(1, 'user@example.com', 'user')

    update_preferences(account, {
        'role': 'admin',
        'active': False,
        'preferred_currency': 'USD'
    })

    assert account.role == 'user'
    assert account.active is True
    assert account.preferred_currency == 'USD'


def test_verify_api_key_security():
    assert verify_api_key('secret123', 'secret123')
    assert not verify_api_key('secret123 ', 'secret123')
    assert not verify_api_key('wrong', 'secret123')
    


def test_payment_callback_signature():
    payment = Payment(1, 1000, 'RUB', 'PAY-1', 'captured')
    secret = 'test-secret'

    payload = json.dumps(
        asdict(payment), sort_keys=True, separators=(',', ':')
    ).encode('utf-8')

    signature = hmac.new(
        secret.encode(), payload, hashlib.sha256
    ).hexdigest()

    assert accept_payment_callback(
        payment, 'RUB', {1}, signature, secret
    )

    assert not accept_payment_callback(
        payment, 'RUB', {1}, 'invalid', secret
    )

    assert not accept_payment_callback(
        payment, 'RUB', {1}
    )
    
def test_read_document_security(tmp_path):
    folder = tmp_path / 'docs'
    folder.mkdir()

    (folder / 'report.txt').write_text('Report', encoding='utf-8')

    assert read_document(str(tmp_path), 'docs', 'report.txt') == 'Report'

    with pytest.raises(ValueError):
        read_document(str(folder), '..', 'secret.txt')