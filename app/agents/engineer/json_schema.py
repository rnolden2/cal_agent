json_schema_engineer = {
    "type": "object",
    "properties": {
        "context": {
            "type": "string",
            "description": "The context or engineering problem provided by the user.",
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
                "concepts_explained": {
                    "type": "array",
                    "items": {
                        "type": "string"
                    },
                    "description": "List of engineering concepts, terms, or equations relevant to the task.",
                },
                "recommended_resources": {
                    "type": "array",
                    "items": {
                        "type": "string"
                    },
                    "description": "Suggested books, research papers, or courses for deepening understanding.",
                },
                "engineering_practices": {
                    "type": "array",
                    "items": {
                        "type": "string"
                    },
                    "description": "Best practices or methodologies applicable to the task.",
                },
                "big_picture_analysis": {
                    "type": "string",
                    "description": "Overview of how the task fits into broader engineering principles.",
                },
                "task_specific_guidance": {
                    "type": "string",
                    "description": "Recommendations tailored to the specific engineering problem.",
                },
            },
            "required": ["concepts_explained"],
            "description": "Details of the engineering concepts, resources, and recommendations.",
        },
    },
    "required": ["context", "timestamp", "response_id", "response"],
    "description": "Schema for capturing the Engineer Agent's response, including concepts, resources, and analysis.",
}
