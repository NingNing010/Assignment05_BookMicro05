"""
Test product domain entity.
"""
from decimal import Decimal
from modules.catalog.domain.entities.product import Product


def test_product_validation_empty_name():
    p = Product(name='', price=Decimal('10.00'))
    errors = p.validate()
    assert any('name' in e.lower() for e in errors)


def test_product_validation_negative_price():
    p = Product(name='Test', price=Decimal('-5'))
    errors = p.validate()
    assert any('price' in e.lower() for e in errors)


def test_product_stock_decrease():
    p = Product(name='Test', price=Decimal('10'), stock=5)
    p.decrease_stock(3)
    assert p.stock == 2


def test_product_attributes():
    p = Product(name='Book', attributes={'author': 'John', 'isbn': '123'})
    assert p.get_attribute('author') == 'John'
    p.set_attribute('pages', 300)
    assert p.attributes['pages'] == 300
