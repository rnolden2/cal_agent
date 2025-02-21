json_schema_sales_agent = {
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
                "raw_response": {
                    "type": "string",
                    "description": "Raw response to prompt that includes sales strategies, opportunity analysis, sales tactics, market trends, business insights, and recommendations from a sales and business perspective.",
                },
            },
            "required": [
                "raw_response",
            ],
            "description": "Details of the sales strategies and analysis provided by the Sales Agent.",
        },
    },
    "required": ["context", "timestamp", "response_id", "response"],
    "description": "Schema for capturing the Sales Agent's response, including insights, tactics, and recommendations.",
}
