json_schema_trend_tracker = {
    "type": "object",
    "properties": {
        "agent": {
            "type": "string",
            "description": "Return TREND_TRACKER",
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
                    "description": "Raw response to prompt that includes deep research on trends, insights, and recommendations related. Provide kewords, related terms, and sources.",
                },
            },
            "required": ["raw_response"],
            "description": "A structured response.",
        },
    },
    "required": ["agent","prompt", "response"],
    "description": "Schema for providing deep research on trends, insights, and recommendations.",
}
