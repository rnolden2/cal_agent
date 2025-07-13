json_schema_tech_wiz = {
    "type": "object",
    "properties": {
        "agent": {
            "type": "string",
            "description": "Return TECH_WIZ",
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
                    "description": "Raw response to prompt that includes technical insights, solutions, recommendations, and resources. Write a bullet point list, a paragraph, and a full report.",
                },
            },
            "required": ["raw_response"],
            "description": "The structured response including bullet points, a paragraph, and a report.",
        },
    },
    "required": ["agent","prompt", "response"],
    "description": "Schema for capturing the Tech Wiz Agent's response, including technical insights, solutions, and recommendations.",
}
