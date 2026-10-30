from datetime import date
from orderflow.accounts import Account, find_account, verify_webhook
from orderflow.analytics import popular_products, revenue_trend
from orderflow.fulfillment import Basket, Line, calculate_invoice, reserve_items
from orderflow.imports import parse_supplier_catalog, merge_supplier_catalog
from orderflow.promotions import apply_promotions
from orderflow.shipping import delivery_estimate, prepare_shipment


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
