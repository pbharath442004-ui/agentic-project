from app.agent import natural_response


def test_empty_knowledge_does_not_claim_knowledge_is_required():
    result = {"type": "knowledge_context", "results": []}
    message = natural_response(result)
    assert "knowledge" not in message.lower() or "company" not in message.lower()
    assert "gemini" in message.lower()
