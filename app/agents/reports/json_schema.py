json_schema_report = {
    "type": "object",
    "properties": {
        "title": {
            "type": "string",
            "description": "The title of the report."
        },
        "executiveSummary": {
            "type": "string",
            "description": "A high-level overview of the report's key findings and purpose."
        },
        "sections": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "sectionTitle": {
                        "type": "string",
                        "description": "The title of the section (e.g., 'Market Size & Growth Projections', 'Key Drivers & Trends')."
                    },
                    "content": {
                        "type": "string",
                        "description": "The detailed content of the section, formatted as Markdown if needed."
                    },
                    "subsections": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "subsectionTitle": {"type": "string"},
                                "content": {"type": "string"}
                            },
                            "required": ["subsectionTitle", "content"]
                        },
                        "description": "Optional subsections for more detailed breakdowns."
                    }
                },
                "required": ["sectionTitle", "content"]
            },
            "description": "An array of main report sections."
        },
        "recommendations": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "details": {"type": "string"}
                },
                "required": ["title", "details"]
            },
            "description": "A list of actionable recommendations."
        },
        "conclusion": {
            "type": "string",
            "description": "Final thoughts and summary."
        },
        "metadata": {
            "type": "object",
            "properties": {
                "sources": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of sources used in the report."
                },
                "date": {"type": "string", "description": "Report generation date."}
            },
            "description": "Additional metadata for verification and tracking."
        }
    },
    "required": ["title", "executiveSummary", "sections"]
}
