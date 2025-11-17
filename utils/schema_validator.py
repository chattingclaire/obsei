"""
Schema Validator
Validates data against defined schemas
"""

import logging
from typing import Dict, List, Optional, Any
import jsonschema
from jsonschema import validate, ValidationError

logger = logging.getLogger(__name__)


class SchemaValidator:
    """Validates data structures against JSON schemas"""

    # Raw item schema
    RAW_ITEM_SCHEMA = {
        "type": "object",
        "required": ["source", "title"],
        "properties": {
            "source": {"type": "string"},
            "source_id": {"type": "string"},
            "source_url": {"type": "string"},
            "title": {"type": "string"},
            "description": {"type": "string"},
            "content": {"type": "string"},
            "author": {"type": "string"},
            "published_at": {"type": ["string", "null"]},
            "metadata": {"type": "object"},
            "media": {"type": "object"},
            "raw_data": {"type": "object"}
        }
    }

    # Classified item schema
    CLASSIFIED_ITEM_SCHEMA = {
        "type": "object",
        "required": ["category_l1", "category_l2", "category_l3", "confidence"],
        "properties": {
            "category_l1": {"type": "string"},
            "category_l2": {"type": "string"},
            "category_l3": {"type": "string"},
            "confidence": {"type": "number", "minimum": 0.0, "maximum": 1.0},
            "summary": {"type": "string"},
            "keywords": {"type": "array", "items": {"type": "string"}}
        }
    }

    @staticmethod
    def validate_raw_item(data: Dict[str, Any]) -> bool:
        """Validate raw item data"""
        try:
            validate(instance=data, schema=SchemaValidator.RAW_ITEM_SCHEMA)
            return True
        except ValidationError as e:
            logger.error(f"Raw item validation error: {e}")
            return False

    @staticmethod
    def validate_classified_item(data: Dict[str, Any]) -> bool:
        """Validate classified item data"""
        try:
            validate(instance=data, schema=SchemaValidator.CLASSIFIED_ITEM_SCHEMA)
            return True
        except ValidationError as e:
            logger.error(f"Classified item validation error: {e}")
            return False
