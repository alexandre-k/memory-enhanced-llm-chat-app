import pytest
from server.environment import supabase_key, supabase_url
from server.memory import Memory
from server.store import VectorDatabase

@pytest.mark.parametrize("memories, user_id, category", [
    (
        [
            {
                "content": "The user frequently translates texts from German to other languages.",
                "category": "preference",
                "confidence": 0.95,
                "entities": ["German"]
            },
            {
                "content": "The user frequently translates texts from English to other languages.",
                "category": "preference",
                "confidence": 0.95,
                "entities": ["English"]
            },
            {
                "content": "The user most often converts currency from Swiss Francs (CHF) to US Dollars (USD).",
                "category": "preference",
                "confidence": 0.98,
                "entities": ["CHF", "USD"]
            }
        ],
        "8a13f1f5-9df0-4d31-a137-cb067ae0f855",
        "preference"
    )
]
)
def test_check_conflict(memories, user_id, category):
    db = VectorDatabase(supabase_url, supabase_key)
    mem = Memory()
    mem.save_memories(user_id, memories, {})
    old_memories = db.get_memories_by_category(user_id, category)
    assert len(old_memories) > 0
    mem.save_memories(user_id, memories, {})
    new_memories = db.get_memories_by_category(user_id, category)
    assert len(new_memories) == len(old_memories)


@pytest.mark.parametrize("user_id, content, expected", [
    (
        "8a13f1f5-9df0-4d31-a137-cb067ae0f855",
        "Convert 50.44 to USD",
        "The user most often converts currency from Swiss Francs (CHF) to US Dollars (USD)."
    )
])
def test_recall(user_id, content, expected):
    mem = Memory()
    recalled_memories = mem.recall(user_id, content)
    first_memory = recalled_memories[0]
    assert first_memory["content"] == expected

@pytest.mark.parametrize("user_id, content, expected", [
    (
        "8a13f1f5-9df0-4d31-a137-cb067ae0f855",
        "Convert 50.44 to USD",
        "The user most often converts currency from Swiss Francs (CHF) to US Dollars (USD)."
    )
])
def test_build_prompt(user_id, content, expected):
    mem = Memory()
    recalled_memories = mem.recall(user_id, content)
    first_memory = recalled_memories[0]
    assert first_memory["content"] == expected

def test_is_memory_old():
    pass