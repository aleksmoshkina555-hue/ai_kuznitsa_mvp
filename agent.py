import json
import time
from openai import OpenAI
from mock_db import search_knowledge_base

llm_client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")
MODEL_NAME = "qwen2.5:1.5b"

BLOCKED_PHRASES = ["забудь", "игнорируй", "всю базу", "system prompt", "системный промпт", "ignore"]

SYSTEM_PROMPT = (
    "Ты корпоративный ИИ-агент поиска знаний и обработки почты. "
    "Отвечай СТРОГО по фактам из переданных действующих документов. "
    "Верни ТОЛЬКО JSON без пояснений:\n"
    '{"answer": "точный ответ со ссылкой на документ, ФИО ответственного и предупреждением об устаревших нормах", '
    '"email_draft": "готовый вежливый ответ на письмо сотрудника"}'
)


def process_corporate_query(sender: str, subject: str, body: str) -> dict:
    start_time = time.time()
    trace_logs = []
    query_text = f"{subject} {body}"

    for phrase in BLOCKED_PHRASES:
        if phrase in query_text.lower():
            trace_logs.append(f"Guardrail: заблокирована попытка взлома ('{phrase}')")
            return {
                "blocked": True,
                "reason": f"Обнаружена попытка перехвата инструкций: '{phrase}'",
                "logs": trace_logs,
                "tokens": 0,
                "latency": 0.0
            }
    trace_logs.append("Проверка безопасности пройдена")

    active_docs, outdated_docs = search_knowledge_base(query_text)
    trace_logs.append(f"Найдено действующих источников: {len(active_docs)}, устаревших: {len(outdated_docs)}")

    if outdated_docs:
        for doc in outdated_docs:
            trace_logs.append(f"Исключен устаревший документ: {doc['title']} ({doc['date']})")

    if not active_docs:
        trace_logs.append("Ответ в базе не найден -> автоэскалация ответственному методологу")
        return {
            "blocked": False,
            "found": False,
            "active_docs": [],
            "outdated_docs": outdated_docs,
            "answer": "В актуальной базе приказов, регламентов и почты точный ответ по данному процессу не найден.",
            "responsible": "Дежурный методолог процессов (process@company.ru)",
            "email_draft": (
                f"Здравствуйте, {sender}!\n\n"
                f"Ваш запрос по теме «{subject}» пока не описан в актуальных регламентах. "
                f"Я автоматически направил задачу ответственному методологу для актуализации базы знаний. "
                f"Ожидаемый срок ответа — до 2 рабочих часов."
            ),
            "logs": trace_logs,
            "tokens": 0,
            "latency": round(time.time() - start_time, 2)
        }

    docs_context = "\n".join(
        [f"[{doc['source_type']} | {doc['title']} от {doc['date']} | Отв.: {doc['owner']}]: {doc['content']}" for doc in active_docs]
    )
    outdated_warning = ""
    if outdated_docs:
        outdated_warning = f"\nУСТАРЕВШИЙ ДОКУМЕНТ (не применять!): {outdated_docs[0]['title']} от {outdated_docs[0]['date']}."

    user_prompt = (
        f"Письмо от: {sender}\nТема: {subject}\nВопрос: {body}\n\n"
        f"ДЕЙСТВУЮЩИЕ ИСТОЧНИКИ:\n{docs_context}{outdated_warning}"
    )

    completion = llm_client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.1,
        max_tokens=300
    )

    tokens_used = completion.usage.total_tokens if completion.usage else 0
    raw_output = completion.choices[0].message.content.strip()

    try:
        json_str = raw_output[raw_output.find("{"):raw_output.rfind("}") + 1]
        parsed_data = json.loads(json_str)
        answer = parsed_data.get("answer", active_docs[0]["content"])
        email_draft = parsed_data.get("email_draft", answer)
    except Exception:
        answer = f"Согласно источнику «{active_docs[0]['title']}» (от {active_docs[0]['date']}): {active_docs[0]['content']}"
        email_draft = f"Здравствуйте, {sender}!\n\n{answer}\nОтветственный за этап: {active_docs[0]['owner']}."

    trace_logs.append(f"Ответ сформирован моделью {MODEL_NAME} за {round(time.time() - start_time, 2)} сек")

    return {
        "blocked": False,
        "found": True,
        "active_docs": active_docs,
        "outdated_docs": outdated_docs,
        "answer": answer,
        "responsible": active_docs[0]["owner"],
        "email_draft": email_draft,
        "logs": trace_logs,
        "tokens": tokens_used,
        "latency": round(time.time() - start_time, 2)
    }
