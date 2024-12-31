json_schema_editor = {
    "type": "object",
    "properties": {
        "context": {
            "type": "string",
            "description": "The original technical piece provided by the user for editing.",
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
                "edited_text": {
                    "type": "string",
                    "description": "The polished version of the original technical piece.",
                },
                "change_summary": {
                    "type": "string",
                    "description": "Summary of changes made to the text, including grammar, tone, and structure improvements.",
                },
                "style_principles_applied": {
                    "type": "array",
                    "items": {
                        "type": "string"
                    },
                    "description": "List of principles or practices applied from 'The Elements of Style' or 'On Writing Well.'",
                },
                "suggested_improvements": {
                    "type": "string",
                    "description": "Additional recommendations for improving clarity, engagement, or persuasiveness.",
                },
                "example_revisions": {
                    "type": "array",
                    "items": {
                        "type": "string"
                    },
                    "description": "Specific examples of revisions made with explanations.",
                },
            },
            "required": ["edited_text", "change_summary"],
            "description": "Details of the edited text, changes made, and additional recommendations.",
        },
    },
    "required": ["context", "timestamp", "response_id", "response"],
    "description": "Schema for capturing the Editor Agent's response, including edited text and applied principles.",
}
