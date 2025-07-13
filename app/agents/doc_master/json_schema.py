json_schema_doc_master = {
    "type": "object",
    "properties": {
        "agent": {
            "type": "string",
            "description": "Return DOC_MASTER",
        },
        "prompt": {
            "type": "string",
            "description": "The prompt or document retrieval task provided by the user.",
        },
        "response": {
            "type": "object",
            "properties": {
                "retrieved_documents": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of documents retrieved relevant to the user request.",
                },
                "document_metadata": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "title": {
                                "type": "string",
                                "description": "Title of the document.",
                            },
                            "author": {
                                "type": "string",
                                "description": "Author or source of the document.",
                            },
                            "publication_date": {
                                "type": "string",
                                "format": "date-time",
                                "description": "The publication date of the document.",
                            },
                            "summary": {
                                "type": "string",
                                "description": "A brief summary of the document content.",
                            },
                        },
                        "required": ["title", "author"],
                    },
                    "description": "Metadata for the retrieved documents.",
                },
                "retrieval_notes": {
                    "type": "string",
                    "description": "Additional notes or insights about the document retrieval process.",
                },
            },
            "required": ["retrieved_documents"],
            "description": "Details of the documents retrieved, metadata, and notes.",
        },
    },
    "required": ["agent","prompt", "response"],
    "description": "Schema for capturing the Doc_Master Agent's response, including retrieved documents, metadata, and process insights.",
}
