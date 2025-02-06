# utils/helpers.py
def is_help_request(prompt):
    """Check if the user is asking for help."""
    help_keywords = ["help", "emergency", "assist", "support", "urgent"]
    prompt_lower = prompt.lower()
    return any(keyword in prompt_lower for keyword in help_keywords)