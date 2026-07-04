from os import getenv
from dotenv import load_dotenv


load_dotenv()

supabase_url = getenv("SUPABASE_URL")
supabase_key = getenv("SUPABASE_KEY")

assert supabase_url is not None
assert supabase_key is not None