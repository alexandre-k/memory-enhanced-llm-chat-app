
from enum import StrEnum, auto
import json
import os
from huggingface_hub import snapshot_download
from sentence_transformers import SentenceTransformer
from .store import VectorDatabase
from .environment import supabase_key, supabase_url
from .logger import log
# from sklearn.feature_extraction.text import TfidfVectorizer
# # from sklearn.metrics.pairwise import cosine_similarity
# from sklearn.metrics.pairwise import linear_kernel
# import numpy as np


class MemoryCategory(StrEnum):
    SETTING = auto()
    PREFERENCE = auto()
    PERSONAL_FACT = auto()
    GOAL = auto()
    RELATIONSHIP = auto()
    EVENT = auto()


class Memory:
    EXTRACTION_PROMPT = """You extract memorable facts from conversation text for a long-term memory system.

Analyze the text and extract discrete facts worth remembering. For each fact, classify it.

Categories: "preference", "personal_fact", "setting", "goal", "relationship", "event"

Return ONLY valid JSON, no preamble, no markdown fences, in this exact format:
{{
  "memories": [
    {{
      "content": "concise standalone fact, rephrased clearly",
      "category": "one of the categories above",
      "confidence": 0.0 to 1.0,
      "entities": ["relevant", "named", "entities"]
    }}
  ]
}}

If there is nothing worth remembering, return {{"memories": []}}.
Also infer implicit preferences and defaults from the user's requests, even if they are not stated directly.

Text to analyze:
\"\"\"{text}\"\"\"
"""
    def __init__(self):
        model_name = os.getenv("MEMORY_GENERATOR_MODEL")
        assert model_name is not None
        if not Memory.is_model_cached(model_name):
            snapshot_download(repo_id=model_name, local_dir="./models/qwen-embedding")
        self.model = SentenceTransformer("./models/qwen-embedding", local_files_only=True, device="cpu")
        try:
            assert supabase_url
            assert supabase_key
            self.db = VectorDatabase(supabase_url, supabase_key)
        except (EnvironmentError, AssertionError) as err:
            log.error(f"Missing database URL/API key: {err}")
            raise

    @staticmethod
    def is_model_cached(repo_id: str) -> bool:
        """
        Checks whether snapshot_download would actually need to fetch anything.
        Returns True if the repo revision is fully cached locally.
        """
        try:
            # This will resolve to the local cache path if the repo exists,
            # and raises an error if it does not.
            snapshot_download(
                repo_id,
                local_files_only=True,  # <-- never hits the network
            )
            return True
        except Exception:
            # LocalFilesOnlyError or FileNotFoundError means not cached
            return False

    def embed(self, text: str) -> list[float]:
        vec = self.model.encode(text, normalize_embeddings=True)  # normalize for cosine similarity
        return vec.tolist()

    def extract_memories(self, data) -> list[dict]:
        try:
            parsed = json.loads(data)
            return parsed.get('memories', [])
        except json.JSONDecodeError:
            return []  # log this for debugging — model occasionally misbehaves

    def seed_data(self):
        # Example memory store
        memories = [
            {"id": "0586fa3f-73ba-4686-9461-b4aee3ea9d8b", "text": "User prefers concise answers, minimal explanation.", "metadata": {"created_at": "2026-06-10T00:00:00+00:00", "type": "setting"}},
            {"id": "0562ad71-ca78-430f-8f1c-95cee2516880", "text": "They are using Python for chat memory semantic retrieval.", "metadata": {}},
            {"id": "39890fe5-f183-4110-b330-4c466c73a082", "text": "They simulate springs in 2D using Hooke's law concepts.", "metadata": {}},
        ]


    async def save_memories(self, user_id: str, memories: list, metadata):
        for m in memories:
            embedding = self.embed(m["content"])
            await self.db.save_memory(user_id, m["content"], metadata, embedding, m["confidence"], m["entities"], m["category"].upper())

    async def recall(self, user_id: str, content: str):
        log.info(f"Recall memory for user {user_id}: '{content}'")
        embedding = self.embed(content)
        return await self.db.match_memories(user_id, embedding)
