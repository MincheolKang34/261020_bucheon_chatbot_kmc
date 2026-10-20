"""긴 대화를 요약해서 모델에 전달할 메시지를 만든다.

모델에는 [시스템 프롬프트] + [오래된 대화의 요약] + [아직 요약되지 않은 최근 메시지] 만 보낸다.
요약은 대화와 함께 data/conversations.json 에 저장되므로 서버를 재시작해도 이어진다.
"""
import store
from chatbot import SYSTEM_PROMPT, ask

KEEP_RECENT = 6      # 요약하지 않고 그대로 보낼 최근 메시지 수
SUMMARIZE_AFTER = 4  # 요약되지 않은 메시지가 KEEP_RECENT + 이 값을 넘으면 요약을 갱신
MAX_CHARS = 2000     # 요약 입력에서 메시지 하나당 최대 글자 수

SUMMARY_PROMPT = (
    "당신은 대화 요약기입니다. '기존 요약'과 '새 대화'를 합쳐 하나의 요약으로 정리하세요.\n"
    "- 사용자의 이름, 사실, 선호, 요청, 결정된 사항, 아직 해결되지 않은 질문을 빠뜨리지 마세요.\n"
    "- 인사말과 군더더기는 버리고 한국어로 400자 이내로 쓰세요.\n"
    "- 요약문만 출력하세요."
)


def _transcript(messages):
    label = {"user": "사용자", "assistant": "챗봇"}
    return "\n".join(f"{label.get(m['role'], m['role'])}: {m['content'][:MAX_CHARS]}" for m in messages)


def _summarize(old_summary, messages):
    text = f"[기존 요약]\n{old_summary or '(없음)'}\n\n[새 대화]\n{_transcript(messages)}"
    answer, _ = ask([
        {"role": "system", "content": SUMMARY_PROMPT},
        {"role": "user", "content": text},
    ])
    return answer.strip()


def build_messages(cid, conv, user_msg):
    """모델에 보낼 메시지 목록을 만든다. 필요하면 요약을 갱신해 저장한다."""
    history = conv["messages"]
    summary = conv.get("summary", "")
    done = conv.get("summarized", 0)  # 요약에 이미 반영된 메시지 수

    if len(history) - done > KEEP_RECENT + SUMMARIZE_AFTER:
        upto = len(history) - KEEP_RECENT
        try:
            summary = _summarize(summary, history[done:upto])
            done = upto
            store.set_summary(cid, summary, done)
        except Exception as e:
            # 요약에 실패해도 대화는 막지 않는다. 요약 갱신 없이 아직 요약되지 않은 메시지를 모두 보낸다.
            print(f"[알림] 대화 요약 실패({type(e).__name__}) → 이전 요약만 사용합니다.")

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    if summary:
        messages.append({
            "role": "system",
            "content": "다음은 이 사용자와 나눈 이전 대화의 요약입니다. 맥락으로 활용하되, "
                       "요약이나 이전 답변이 영어여도 답변은 한국어로 하세요.\n" + summary,
        })
    messages += [{"role": m["role"], "content": m["content"]} for m in history[done:]]
    messages.append(user_msg)
    return messages
