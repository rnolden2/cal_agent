"""
Injects context into agent prompts.
"""
from typing import List

class ContextInjector:
    """
    Injects various types of context into agent prompts.
    """

    def inject_context(self, prompt: str, context: List[str]) -> str:
        """
        Injects a list of context strings into the prompt.
        """
        if not context:
            return prompt

        context_str = "\n".join(f"- {c}" for c in context)
        return f"ADDITIONAL CONTEXT:\n{context_str}\n\nORIGINAL PROMPT:\n{prompt}"
