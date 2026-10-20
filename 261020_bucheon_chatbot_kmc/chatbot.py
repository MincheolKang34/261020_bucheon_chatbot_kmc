"""챗봇 핵심 로직. Groq 호출이 실패(할당량 소진 등)하면 Gemini로 자동 전환한다.

웹/터미널 실행은 main.py 를 사용한다.
"""
import getpass
import os
import sys

import requests
from dotenv import load_dotenv, set_key
from groq import AuthenticationError, Groq, GroqError, PermissionDeniedError

ENV_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
SYSTEM_PROMPT = "당신은 친절한 한국어 챗봇입니다. 간결하고 정확하게 답하세요."

GROQ_API_KEY = GEMINI_API_KEY = GROQ_MODEL = GEMINI_MODEL = None
groq_client = None


def reload_config():
    """.env 를 다시 읽어 키/모델 설정을 갱신한다."""
    global GROQ_API_KEY, GEMINI_API_KEY, GROQ_MODEL, GEMINI_MODEL, groq_client
    load_dotenv(ENV_PATH, override=True)
    GROQ_API_KEY = os.getenv("GROQ_API_KEY") or None
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or None
    GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")
    GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    groq_client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None


def has_keys():
    return bool(GROQ_API_KEY or GEMINI_API_KEY)


def mask(key):
    """입력 확인용 미리보기. 예: gsk_****abcd (56자)"""
    if len(key) <= 8:
        return f"{'*' * len(key)} ({len(key)}자)"
    return f"{key[:4]}****{key[-4:]} ({len(key)}자)"


def check_groq(key):
    """True=유효, False=거부됨, None=네트워크 등으로 확인 불가"""
    try:
        Groq(api_key=key).models.list()
        return True
    except (AuthenticationError, PermissionDeniedError):
        return False
    except GroqError:
        return None


def check_gemini(key):
    try:
        res = requests.get(
            "https://generativelanguage.googleapis.com/v1beta/models",
            headers={"x-goog-api-key": key}, timeout=10,
        )
    except requests.RequestException:
        return None
    if res.status_code == 200:
        return True
    return False if res.status_code in (400, 401, 403) else None


PROVIDERS = {
    "groq": ("GROQ_API_KEY", check_groq),
    "gemini": ("GEMINI_API_KEY", check_gemini),
}


def save_keys(keys):
    """{'groq': 키, 'gemini': 키} 를 검증 후 .env 에 저장한다. 빈 값은 기존 값 유지.

    반환: {provider: 'ok' | 'unverified' | 'rejected'} (입력된 키만 포함)
    거부된 키는 저장하지 않는다.
    """
    results = {}
    for name, key in keys.items():
        key = (key or "").strip()
        if not key:
            continue
        env_name, checker = PROVIDERS[name]
        ok = checker(key)
        if ok is False:
            results[name] = "rejected"
            continue
        results[name] = "ok" if ok else "unverified"
        if not os.path.exists(ENV_PATH):
            open(ENV_PATH, "w", encoding="utf-8").close()
        set_key(ENV_PATH, env_name, key, quote_mode="never")
    reload_config()
    return results


def ask_groq(messages):
    res = groq_client.chat.completions.create(model=GROQ_MODEL, messages=messages)
    return res.choices[0].message.content


def ask_gemini(messages):
    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"{GEMINI_MODEL}:generateContent"
    )
    contents = [
        {"role": "model" if m["role"] == "assistant" else "user",
         "parts": [{"text": m["content"]}]}
        for m in messages if m["role"] != "system"
    ]
    body = {
        "system_instruction": {"parts": [{"text": SYSTEM_PROMPT}]},
        "contents": contents,
    }
    res = requests.post(url, headers={"x-goog-api-key": GEMINI_API_KEY}, json=body, timeout=60)
    res.raise_for_status()
    return res.json()["candidates"][0]["content"]["parts"][0]["text"]


def ask(messages):
    """Groq 우선, 실패 시 Gemini 사용."""
    if groq_client:
        try:
            return ask_groq(messages), "groq"
        except GroqError as e:
            print(f"[알림] Groq 호출 실패({type(e).__name__}) → Gemini로 전환합니다.")
    if not GEMINI_API_KEY:
        raise RuntimeError("사용 가능한 API 키가 없습니다. 키를 설정해 주세요.")
    return ask_gemini(messages), "gemini"


# ---------- 터미널 모드 ----------

def ask_key_cli(name, label):
    """키를 입력받아 마스킹 표시 + 유효성 검사. Enter 만 누르면 건너뜀."""
    while True:
        key = getpass.getpass(f"{label}: ").strip()
        if not key:
            return ""
        print(f"  입력값: {mask(key)}  → 확인 중...")
        ok = PROVIDERS[name][1](key)
        if ok:
            print(f"  ✅ {name} 키가 확인되었습니다.")
            return key
        if ok is None:
            print(f"  ⚠️ {name} 키를 검증하지 못했습니다(네트워크 문제 등). 그대로 저장합니다.")
            return key
        print(f"  ❌ {name} 키가 거부되었습니다. 다시 입력하거나 Enter 로 건너뛰세요.")


def setup_cli():
    print("API 키가 없어 초기 설정을 진행합니다. (건너뛰려면 Enter, 입력은 화면에 보이지 않습니다)")
    keys = {
        "groq": ask_key_cli("groq", "GROQ_API_KEY"),
        "gemini": ask_key_cli("gemini", "GEMINI_API_KEY (Groq 소진 시 대체용)"),
    }
    if not any(keys.values()):
        sys.exit("키가 하나도 입력되지 않았습니다. 다시 실행해 주세요.")
    # 이미 CLI 에서 검증했으므로 저장만 한다.
    for name, key in keys.items():
        if key:
            if not os.path.exists(ENV_PATH):
                open(ENV_PATH, "w", encoding="utf-8").close()
            set_key(ENV_PATH, PROVIDERS[name][0], key, quote_mode="never")
    reload_config()
    print(f".env 저장 완료: {ENV_PATH}\n")


def run_cli():
    reload_config()
    if not has_keys():
        if not sys.stdin.isatty():
            sys.exit(".env 에 GROQ_API_KEY 또는 GEMINI_API_KEY 를 설정하세요. (.env.example 참고)")
        setup_cli()

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    print("챗봇 시작! 종료: quit / exit / 종료")
    while True:
        try:
            user = input("\n나> ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not user:
            continue
        if user.lower() in ("quit", "exit", "종료"):
            break
        messages.append({"role": "user", "content": user})
        try:
            answer, provider = ask(messages)
        except Exception as e:
            messages.pop()
            print(f"[오류] {e}")
            continue
        messages.append({"role": "assistant", "content": answer})
        print(f"\n봇({provider})> {answer}")
    print("\n안녕히 가세요!")


reload_config()
