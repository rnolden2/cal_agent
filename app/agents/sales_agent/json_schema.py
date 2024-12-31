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
                "opportunity_analysis": {
                    "type": "string",
                    "description": "Insights into untapped opportunities or weaknesses in the current approach.",
                },
                "sales_tactics": {
                    "type": "array",
                    "items": {
                        "type": "string"
                    },
                    "description": "List of suggested sales strategies tailored to government and defense industries.",
                },
                "follow_up_recommendations": {
                    "type": "array",
                    "items": {
                        "type": "string"
                    },
                    "description": "Suggested steps for follow-ups to optimize sales potential.",
                },
                "market_trends": {
                    "type": "string",
                    "description": "Analysis of relevant market trends or emerging opportunities.",
                },
            },
            "required": [
                "opportunity_analysis",
                "sales_tactics",
                "follow_up_recommendations",
                "market_trends",
            ],
            "description": "Details of the sales strategies and analysis provided by the Sales Agent.",
        },
    },
    "required": ["context", "timestamp", "response_id", "response"],
    "description": "Schema for capturing the Sales Agent's response, including insights, tactics, and recommendations.",
}
