from openai import AsyncOpenAI
from config import GROQ_API_KEY

groq = AsyncOpenAI(
    api_key=GROQ_API_KEY,
    base_url="https://api.groq.com/openai/v1",
)
