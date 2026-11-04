import os
import re
import sys
from pathlib import Path

import clickhouse_connect
from anthropic import Anthropic

MODEL = os.getenv("CLAUDE_MODEL", "claude-haiku-5-5")
SYSTEM_PROMPT = Path(__file__).with_name("system_prompt.md").read_text(encoding="utf-8")

client = Anthropic()  # reads ANTHROPIC_API_KEY from the environment
ch = clickhouse_connect.get_client(
    host=os.getenv("CH_HOST", "localhost"),
    username=os.getenv("CH_READONLY_USER", "readonly"),
    password=os.getenv("CH_READONLY_PASSWORD", ""),
)

FORBIDDEN = re.compile(
    r"\b(insert|update|delete|drop|alter|create|attach|detach|truncate|grant)\b",
    re.IGNORECASE,
)


def is_safe_select(sql: str) -> bool:
    cleaned = sql.strip().rstrip(";")
    return (
        cleaned.lower().startswith("select")
        and ";" not in cleaned
        and not FORBIDDEN.search(cleaned)
    )


def question_to_sql(question: str) -> str:
    response = client.messages.create(
        model=MODEL,
        max_tokens=400,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": question}],
    )
    return response.content[0].text.strip().strip("`")


if __name__ == "__main__":
    question = " ".join(sys.argv[1:]) or input("Question: ")
    sql = question_to_sql(question)
    print("SQL:", sql)

    if sql == "UNSUPPORTED":
        sys.exit("The question is outside the telemetry table.")
    if not is_safe_select(sql):
        sys.exit("The generated query was rejected by the safety check.")

    result = ch.query(sql.rstrip(";"))
    for row in result.result_rows[:50]:
        print(row)
