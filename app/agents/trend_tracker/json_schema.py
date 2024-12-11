json_schema = {
    "type": "object",
    "properties": {
        "context": {
            "type": "string",
            "description": "The context provided by the user.",
        },
        "timestamp": {
            "type": "integer",
            "description": "The timestamp in milliseconds when the input was generated.",
        },
        "response_id": {
            "type": "string",
            "description": "A unique identifier derived from the timestamp for integrity checks or uniqueness.",
        },
        "response": {
            "type": "object",
            "properties": {
                "keywords": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Array of keywords related to the context.",
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
                            "item_name": {
                                "type": "string",
                                "description": "Name of the item.",
                            },
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
            "required": ["keywords", "related_terms", "search_items"],
            "description": "The structured response containing keywords, related terms, and search items.",
        },
    },
    "required": ["context", "timestamp", "response_id", "response"],
    "description": "Schema for providing input context and search-related data.",
}
