json_schema = {
    "type": "object",
    "properties": {
        "content": {
            "type": "string",
            "description": "The content or context provided by the user.",
        },
        "timestamp": {
            "type": "integer",
            "description": "The timestamp in milliseconds when the input was generated.",
        },
        "timestamp_hash": {
            "type": "string",
            "description": "A hash derived from the timestamp for integrity checks or uniqueness.",
        },
        "keywords": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Array of keywords related to the content.",
        },
        "related_terms": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Array of terms related to what is being searched.",
        },
        "search_items": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "item_name": {"type": "string", "description": "Name of the item."},
                    "item_title": {
                        "type": "string",
                        "description": "Title of the item.",
                    },
                    "item_description": {
                        "type": "string",
                        "description": "Description of the item.",
                    },
                    "item_source": {
                        "type": "string",
                        "description": "Source of the item.",
                    },
                },
                "required": [
                    "item_name",
                    "item_title",
                    "item_description",
                    "item_source",
                ],
                "description": "Details of a search item.",
            },
            "description": "Array of items related to the search.",
        },
    },
    "required": ["content", "timestamp", "timestamp_hash", "keywords", "related_terms", "search_items"],
    "description": "Schema for providing input context and search-related data.",
}
