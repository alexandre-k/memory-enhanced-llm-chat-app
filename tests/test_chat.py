import pytest
from server.chat import LlmChat
from server.memory import MemoryCategory


@pytest.mark.parametrize("content, expected", [
    (
        [
            {"content": "old preference.", "category": MemoryCategory.PERSONAL_FACT.value}
        ],
        "You are a helpful assistant with memory of past conversations. Use the settings or context naturally if relevant; don't mention you're using memories.\n            User settings (always apply these):\n            \n            Other relevant context:\n            - old preference.\n            Answer the following message:\n        {user_message}\n        "
    ),
    (
        [
            {"content": "old preference.", "category": MemoryCategory.SETTING.value}
        ],
        "You are a helpful assistant with memory of past conversations. Use the settings or context naturally if relevant; don't mention you're using memories.\n            User settings (always apply these):\n            - old preference.\n            Other relevant context:\n            \n            Answer the following message:\n        {user_message}\n        "
    ),
    (
        [],
        "You are a helpful assistant.\n            Answer the following message:\n        {user_message}\n        "
    )
])
def test_generate_message(content, expected):
    # memories = recall(user_id, user_message, top_k=5)
    llm = LlmChat()
    message = llm.generate_message(content)
    assert message == expected
    test_str = "hello world"
    assert test_str not in message
    message_with_memory = message.format(user_message=test_str)
    assert test_str in message_with_memory