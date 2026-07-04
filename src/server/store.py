import json
from typing import Optional, Tuple
from supabase import create_client
from supabase._async.client import AsyncClient as SupabaseClient
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from datetime import datetime
from dateutil.relativedelta import relativedelta
from os import getenv
from .logger import log

class VectorDatabase:

    def __init__(self, supabase_url: str, supabase_key: str):
        self.supabase = SupabaseClient(
            supabase_url=supabase_url,
            supabase_key=supabase_key
        )

    async def save_memory(self, user_id: str, content: str, metadata: dict, embedding: list, confidence: float, entities: list[str], category: str):
        is_conflicting, old_memories = await self.check_conflicting_category(user_id, embedding, category)
        if is_conflicting:
            # Favor new memory over old ones by default.
            # In case of conflict remove old memories to overwrite with new one.
            for memory in old_memories:
                log.warning(f"Remove memory '{memory['content']}' saved for user {memory['user_id']}")
                await self.supabase\
                    .table("memories")\
                    .delete()\
                    .eq("user_id", user_id)\
                    .eq("id", memory["id"])\
                    .execute()

        await self.supabase.table("memories").insert({
            "user_id": user_id,
            "content": content,
            "embedding": embedding,
            "metadata": metadata or {},
            "confidence": confidence,
            "entities": entities,
            "category": category
        }).execute()

    async def save_batch_memories(self, batch: list[dict]):
        return await self.supabase.table("memories").insert(batch).execute()

    async def check_conflicting_category(self, user_id: str, new_embedding: list, category, threshold=0.75) -> Tuple[bool, dict]:
        result = await self.supabase.table("memories").select("*").eq("user_id", user_id).eq("category", category).execute()
        existing = result.data
        conflicting_memories = []
        for old_memory in existing:
            # convert vector from string representing a list of floats
            old_embedding = json.loads(old_memory['embedding'])
            sim = cosine_similarity(np.array(new_embedding).reshape(1, -1), np.array(old_embedding).reshape(1, -1))
            if sim > threshold:
                conflicting_memories.append(old_memory)
        return (len(conflicting_memories) > 0, conflicting_memories)

    @staticmethod
    def is_memory_old(memory: dict):
        current_date = datetime.now()
        created_at = datetime.fromisoformat(memory["created_at"])
        one_year_before = current_date - relativedelta(years=getenv("IGNORE_MEMORY_AFTER_YEAR"))
        return created_at < one_year_before

    async def get_memories_by_category(self, user_id: str, category: Optional[str] = None):
        query = self.supabase.table("memories").select("*").eq("user_id", user_id)
        if category:
            result = await query.eq("category", category).execute()
        else:
            result = await query.execute()
        return result.data

    async def match_memories(self, user_id: str, embedding: list[float], top_k: int = 5):
        result = await self.supabase.rpc("match_memories", {
            "query_embedding": embedding,
            "match_user_id": user_id,
            "match_threshold": 0.5,
            "match_count": top_k
        }).execute()
        if result is None or result.data is None: return []
        return result.data

    # def forget_memory(self, user_id: str, content_to_forget: str, threshold=0.8):
    #     query_vec = self.embed(content_to_forget)
    #     all_mems = self.supabase.table("memories").select("id, content, embedding").eq("user_id", user_id).execute().data

    #     for mem in all_mems:
    #         sim = cosine_sim(query_vec, np.array(mem['embedding']))
    #         if sim > threshold:
    #             self.supabase.table("memories").delete().eq("id", mem['id']).execute()
