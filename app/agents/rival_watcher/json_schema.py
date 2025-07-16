json_schema_rival_watcher = {
    "type": "object",
    "properties": {
        "agent": {
            "type": "string",
            "description": "Return RIVAL_WATCHER",
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
                    "description": "Raw response to prompt. that includes competitor-related data i.e. links descriptions etc.",
                },
            },
            "required": ["raw_response"],
            "description": "The response object containing competitor-related data.",
        },
    },
    "required": ["agent","prompt", "response"],
    "description": "Schema for providing competitor-related data.",
}
