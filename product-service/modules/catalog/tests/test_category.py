"""
Test category domain entity.
"""
from modules.catalog.domain.entities.category import Category


def test_category_validation_empty_name():
    c = Category(name='')
    errors = c.validate()
    assert any('name' in e.lower() for e in errors)


def test_category_is_root():
    c = Category(name='Root')
    assert c.is_root is True


def test_category_is_child():
    c = Category(name='Child', parent_id=1)
    assert c.is_root is False
