import os
from huggingface_hub import snapshot_download


model_name = os.getenv("MEMORY_GENERATOR_MODEL")
snapshot_download(repo_id=model_name, local_dir="./models/qwen-embedding")
