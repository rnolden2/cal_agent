from contextvars import ContextVar

# Define the context variable for the LLM call counter
llm_call_counter: ContextVar[int] = ContextVar('llm_call_counter', default=0)

def increment_llm_call_counter():
    """Increments the LLM call counter by 1."""
    current_count = llm_call_counter.get()
    llm_call_counter.set(current_count + 1)

def get_llm_call_counter() -> int:
    """Returns the current value of the LLM call counter."""
    return llm_call_counter.get()
