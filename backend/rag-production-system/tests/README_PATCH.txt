EVALUATION MODEL SEPARATION PATCH
=================================

What changed:

NORMAL CHAT
-----------
CHAT_PROVIDER=groq
    -> normal RagService.llm
    -> Groq

EVALUATION ANSWER GENERATION
----------------------------
evaluation=True
    -> RagService._get_evaluation_llm()
    -> DeepSeek V4 Flash

DEEPEVAL JUDGE
--------------
EVAL_JUDGE=deepseek
    -> DeepSeek V4 Flash

Therefore evaluation no longer uses Groq for answer generation.

Required dependency:
    pip install -U langchain-openai

Expected .env:
    CHAT_PROVIDER=groq
    GROQ_API_KEY=...

    EVAL_JUDGE=deepseek
    EVAL_DEEPSEEK_API_KEY=...
    EVAL_DEEPSEEK_BASE_URL=https://api.deepseek.com
    EVAL_DEEPSEEK_MODEL=deepseek-v4-flash

The SambaNova key remains available as a secondary judge.

Do not change CHAT_PROVIDER just to run evaluation.
