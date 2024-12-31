json_schema_rival_watcher = {
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
                "competitor_data": {
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "Name of the competitor.",
                        },
                        "location": {
                            "type": "string",
                            "description": "Location of the competitor.",
                        },
                        "website": {
                            "type": "string",
                            "description": "Website of the competitor.",
                        },
                        "description": {
                            "type": "string",
                            "description": "Description of the competitor.",
                        },
                        "competitive_product": {
                            "type": "string",
                            "description": "Competitor's product that competes with yours.",
                        },
                        "articles": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "source_name": {
                                        "type": "string",
                                        "description": "Name of the source for the article.",
                                    },
                                    "link": {
                                        "type": "string",
                                        "description": "Link to the article.",
                                    },
                                },
                                "required": ["source_name", "link"],
                                "description": "Details of an article related to the competitor.",
                            },
                            "description": "Array of articles related to the competitor.",
                        },
                    },
                    "required": [
                        "name",
                        "location",
                        "website",
                        "description",
                        "competitive_product",
                        "articles",
                    ],
                    "description": "Details of a competitor, including related articles.",
                },
            },
            "required": ["competitor_data"],
            "description": "The response object containing competitor-related data.",
        },
    },
    "required": ["context", "timestamp", "response_id", "response"],
    "description": "Schema for providing input context and competitor-related data.",
}
