json_schema_sales_agent = {
    "type": "object",
    "properties": {
        "agent": {
            "type": "string",
            "description": "The agent used to respond.",
        },
        "prompt": {
            "type": "string",
            "description": "The prompt provided by the user.",
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
    "required": ["agent","prompt", "response"],
    "description": "Schema for capturing the Sales Agent's response, including insights, tactics, and recommendations.",
}
