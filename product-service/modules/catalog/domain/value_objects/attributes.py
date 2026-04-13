"""
Attributes — Value Object for type-specific product attributes (stored as JSON).
"""
from __future__ import annotations

# Schema describes which keys are expected per ProductType.
PRODUCT_TYPE_ATTRIBUTE_SCHEMA: dict[str, list[str]] = {
    'Book': ['author', 'isbn'],
    'Clothes': ['size', 'color', 'material'],
}


def validate_attributes(product_type_name: str, attributes: dict) -> list[str]:
    """
    Validate that *attributes* contains the expected keys for *product_type_name*.
    Returns a list of warning messages (not hard errors — attributes are flexible).
    """
    warnings: list[str] = []
    expected_keys = PRODUCT_TYPE_ATTRIBUTE_SCHEMA.get(product_type_name, [])
    for key in expected_keys:
        if key not in attributes:
            warnings.append(f'Missing recommended attribute "{key}" for {product_type_name}.')
    return warnings
