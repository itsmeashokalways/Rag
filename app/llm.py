import time
from config import LLM_API_KEY, LLM_MODEL
from openai import OpenAI

# INIT CLIENT
client = OpenAI(
    api_key=LLM_API_KEY,
    base_url="https://api.groq.com/openai/v1"
)

model = LLM_MODEL


# SAFE API CALL
def safe_generate(prompt, retries=3, delay=2):
    for attempt in range(retries):
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,
                max_tokens=1200
            )
            return response.choices[0].message.content

        except Exception as e:
            print(f"Retry {attempt+1} failed: {e}")
            time.sleep(delay)

    return None


# FORMAT CONTEXT
def format_context(chunks):
    if not chunks:
        return "No relevant context found."

    parts = []
    for chunk in chunks:
        parts.append(
            f"[Source: {chunk['source_file']}]\n{chunk['content']}"
        )

    return "\n\n".join(parts)


# GENERATE ANSWER (YOUR PROMPT + FIX)
def generate_answer(user_question, relevant_chunks):

    # HARD BLOCK
    if not relevant_chunks:
        return "I could not find the answer in the provided documents."

    context = format_context(relevant_chunks)

    prompt = f"""
    You are a STRICT document-based AI assistant.

    Your task is to EXTRACT and ORGANIZE information ONLY from the provided CONTEXT.

    ---------------------
    CRITICAL RULES:
    ---------------------
    1. Use ONLY the information explicitly present in CONTEXT.
    2. Do NOT use external knowledge.
    3. Do NOT guess, infer, or add missing details.
    4. Do NOT modify meaning of the original content.
    5. You may rephrase ONLY for clarity, without adding new information.

    6. If the answer is NOT found in CONTEXT:
    → Respond EXACTLY:
    "I could not find the answer in the provided documents."
    → DO NOT include sources.

    ---------------------
    FORMATTING RULES:
    ---------------------
    - If multiple items → use TABLE
    - If list → use BULLETS
    - If simple → short paragraph
    - If query needs a specific format,provide in that format
    ---------------------
    SOURCE RULES:
    ---------------------
    - Use ONLY sources from CONTEXT
    - Do NOT invent sources
    - Include sources ONLY when a valid answer is provided

    STRICT RULE:
    - Each source must appear ONLY ONCE (no duplicates)
    - Even if multiple chunks come from same file → show it ONLY once

    - Sources MUST be at the end
    - Each source on a NEW LINE
    - NEVER include sources inside tables

    Format:
    <answer>

    (Source: filename)
    (Source: filename)

    ---------------------
    CONTEXT:
    ---------------------
    {context}

    ---------------------
    QUESTION:
    ---------------------
    {user_question}

    ---------------------
    ANSWER:
    ---------------------
    """

    response = safe_generate(prompt)

    if not response:
        return " System is busy. Please try again."

    answer = response.strip()

    #  FINAL SAFETY FIX (CRITICAL)
    if "I could not find the answer" in answer:
        return "I could not find the answer in the provided documents."

    return answer


# FORMAT CHAT HISTORY
def format_chat_history(chat_history):
    if not chat_history:
        return ""

    return "\n".join(
        f"{role}: {msg}"
        for role, msg in chat_history
    )


# QUERY REWRITE
def rewrite_query(user_question, chat_history):

    if not chat_history:
        return user_question

    history_text = format_chat_history(chat_history)

    prompt = f"""
    You are a query rewriting assistant.

    Your job is to convert the user question into a clear standalone query.

    RULES:
    - Resolve references (it, they, that, them)
    - Use chat history only to identify subject
    - Preserve meaning
    - Do NOT add new info
    - If clear → return unchanged
    - Output ONLY query

    CHAT HISTORY:
    {history_text}

    QUESTION:
    {user_question}

    QUERY:
    """

    response = safe_generate(prompt)

    return response.strip() if response else user_question


# OPTIONAL
def needs_rewrite(query):
    trigger_words = ["it", "they", "that", "those", "he", "she", "this", "them"]
    return any(word in query.lower() for word in trigger_words)