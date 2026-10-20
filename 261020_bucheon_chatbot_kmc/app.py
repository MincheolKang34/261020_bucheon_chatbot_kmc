"""웹 UI 서버. chatbot.py 의 로직을 재사용한다. 실행은 main.py 를 사용한다."""
from flask import Flask, jsonify, render_template, request

import chatbot
import memory
import store
from chatbot import ask

app = Flask(__name__)


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/api/status")
def status():
    """키 설정 여부만 알려준다. 키 값 자체는 절대 내보내지 않는다."""
    return jsonify(
        groq=chatbot.mask(chatbot.GROQ_API_KEY) if chatbot.GROQ_API_KEY else None,
        gemini=chatbot.mask(chatbot.GEMINI_API_KEY) if chatbot.GEMINI_API_KEY else None,
    )


@app.post("/api/setup")
def setup():
    data = request.get_json(silent=True) or {}
    keys = {"groq": data.get("groq"), "gemini": data.get("gemini")}
    if not any((v or "").strip() for v in keys.values()):
        return jsonify(error="키를 하나 이상 입력하세요."), 400
    results = chatbot.save_keys(keys)
    return jsonify(results=results, configured=chatbot.has_keys())


@app.get("/api/conversations")
def conversations():
    return jsonify(store.list_conversations())


@app.post("/api/conversations")
def new_conversation():
    return jsonify(id=store.create())


@app.get("/api/conversations/<cid>")
def get_conversation(cid):
    conv = store.get(cid)
    if conv is None:
        return jsonify(error="대화를 찾을 수 없습니다."), 404
    return jsonify(id=cid, title=conv["title"], messages=conv["messages"])


@app.delete("/api/conversations/<cid>")
def delete_conversation(cid):
    if not store.delete(cid):
        return jsonify(error="대화를 찾을 수 없습니다."), 404
    return jsonify(ok=True)


@app.post("/api/chat")
def chat():
    data = request.get_json(silent=True) or {}
    cid, text = data.get("conversation_id"), (data.get("message") or "").strip()
    if not text:
        return jsonify(error="메시지가 없습니다."), 400
    conv = store.get(cid)
    if conv is None:
        return jsonify(error="대화를 찾을 수 없습니다."), 404
    if not chatbot.has_keys():
        return jsonify(error="API 키가 설정되지 않았습니다.", need_setup=True), 400
    user_msg = {"role": "user", "content": text}
    messages = memory.build_messages(cid, conv, user_msg)
    try:
        answer, provider = ask(messages)
    except Exception as e:
        return jsonify(error=str(e)), 500
    # 성공했을 때만 사용자 메시지와 답변을 함께 저장한다.
    conv = store.append(cid, user_msg,
                        {"role": "assistant", "content": answer, "provider": provider})
    return jsonify(answer=answer, provider=provider, title=conv["title"])
