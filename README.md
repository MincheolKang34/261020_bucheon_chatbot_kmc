# 부천 챗봇 (Groq + Gemini fallback)

Groq API로 대화하는 챗봇입니다. 기본은 웹 화면이며 터미널 모드도 지원합니다.
Groq 호출이 실패하거나 할당량이 소진되면 Gemini API로 자동 전환됩니다.

## 주요 기능
- **웹 채팅 화면**(기본)과 **터미널 모드** 지원
- **대화 저장**: 이전 대화를 목록에서 골라 이어서 대화, 새 대화 시작, 삭제
- **긴 대화 요약**: 대화가 길어지면 오래된 부분을 요약해 저장하고, 요약 + 최근 메시지만 모델에 전달 (서버를 재시작해도 요약이 유지되어 이어서 대화 가능)
- **API 키 입력 UI**: 웹 설정 창 또는 터미널 프롬프트에서 입력하고, 저장 전에 키가 유효한지 확인
- **자동 전환**: Groq 실패 시 Gemini로 답변 (답변에 `groq` / `gemini` 표시)

## 준비
1. Python 3.8 이상
2. API 키 발급
   - Groq: https://console.groq.com/keys
   - Gemini: https://aistudio.google.com/apikey

## 설치
### 1) 저장소 가져오기
```bash
git clone https://github.com/MincheolKang34/261020_bucheon_chatbot_kmc.git
cd 261020_bucheon_chatbot_kmc
```
저장소 안에 같은 이름의 하위 폴더가 한 번 더 있고, 실제 코드는 그 안에 있습니다.
```bash
cd 261020_bucheon_chatbot_kmc
```
(git이 없다면 GitHub 페이지의 `Code` → `Download ZIP` 으로 받아 압축을 풀어도 됩니다.)

### 2) 라이브러리 설치
```bash
pip install -r requirements.txt
```

### 사용 라이브러리
`requirements.txt` 에 아래 4개가 명시되어 있습니다.

| 라이브러리 | 요구 버전 | 확인한 버전 | 용도 |
|---|---|---|---|
| `groq` | >=0.9.0 | 0.33.0 | Groq API 호출, 키 검증 |
| `python-dotenv` | >=1.0.0 | 1.0.1 | `.env` 읽기/쓰기 |
| `requests` | >=2.31.0 | 2.32.4 | Gemini REST API 호출, 키 검증 |
| `flask` | >=3.0.0 | 3.0.3 | 웹 서버 |

그 외 `argparse`, `json`, `threading`, `getpass`, `webbrowser` 등은 파이썬 기본 모듈이라 설치가 필요 없습니다.

## 실행
```bash
python main.py            # 웹 화면 (기본) - 브라우저가 자동으로 열립니다 (http://127.0.0.1:5000)
python main.py --cli      # 터미널 챗봇
```

| 옵션 | 설명 |
|---|---|
| `--cli` | 웹 대신 터미널에서 실행 |
| `--port 8000` | 웹 서버 포트 변경 (기본 5000) |
| `--no-browser` | 브라우저 자동 실행 끄기 |

종료는 웹 모드에서는 터미널에서 `Ctrl+C`, 터미널 모드에서는 `quit` / `exit` / `종료` 입력입니다.

## 웹 화면 사용법
- **대화 전환**: 왼쪽 목록에서 이전 대화를 누르면 그 대화로 전환되어 이어서 대화할 수 있습니다.
- **새 대화**: `＋ 새 대화` 버튼. 첫 메시지를 보낼 때 목록에 추가되고, 제목은 첫 메시지로 자동 지정됩니다.
- **삭제**: 목록 항목의 `✕` 버튼 (확인창이 뜹니다).
- **다시 열기**: 마지막에 보던 대화가 자동으로 열립니다.
- **API 키 변경**: 상단 `⚙ API 키` 버튼. 비워 두면 기존 값을 유지합니다.
- 모바일 등 좁은 화면에서는 `☰` 버튼으로 대화 목록을 열고 닫습니다.

## 대화 요약 (이어가기)
모델에는 전체 기록 대신 `시스템 프롬프트 + 이전 대화 요약 + 최근 메시지`를 보냅니다.
- 요약되지 않은 메시지가 10개를 넘으면(최근 6개는 원문 유지) 오래된 부분을 기존 요약과 합쳐 다시 요약합니다.
- 요약은 `data/conversations.json` 의 해당 대화에 함께 저장되므로, 서버를 껐다 켜도 이전 맥락을 기억합니다.
- 요약 호출이 실패해도 대화는 막히지 않고, 요약되지 않은 메시지를 그대로 보냅니다.
- 요약 기준은 `memory.py` 의 `KEEP_RECENT`, `SUMMARIZE_AFTER` 로 조절합니다.
- 화면에는 원문 대화가 그대로 표시됩니다. (요약은 모델에게 보내는 용도)

## API 키 설정
`.env` 가 없어도 됩니다. 처음 실행하면 키 입력 창(웹) 또는 프롬프트(터미널)가 나옵니다.
- 입력한 키는 저장 전에 실제로 유효한지 확인하며, 거부된 키는 저장하지 않습니다.
- 터미널 입력은 화면에 보이지 않고, 입력 후 `gsk_****abcd (56자)` 형태로 확인용 미리보기를 보여줍니다.
- 키는 `.env` 에 저장됩니다.

직접 설정하려면 `.env.example` 을 `.env` 로 복사해 값을 채우세요.
```bash
copy .env.example .env     # Windows
cp .env.example .env       # macOS / Linux
```

| 변수 | 설명 | 기본값 |
|---|---|---|
| `GROQ_API_KEY` | Groq API 키 | - |
| `GEMINI_API_KEY` | Gemini API 키 (fallback) | - |
| `GROQ_MODEL` | Groq 모델 | openai/gpt-oss-20b |
| `GEMINI_MODEL` | Gemini 모델 | gemini-2.5-flash |

둘 중 하나만 있어도 동작합니다. (Groq 키만 있으면 fallback 없이 Groq만 사용)

## 저장되는 파일과 보안
| 파일 | 내용 | GitHub |
|---|---|---|
| `.env` | API 키 | 제외 (`.gitignore`) |
| `data/conversations.json` | 웹 대화 내용 (평문 JSON) | 제외 (`.gitignore`) |

- 터미널 모드의 대화는 저장되지 않습니다.
- 서버는 `127.0.0.1` (내 PC)에서만 접속됩니다. 같은 주소로 접속하는 사람은 키 설정을 바꿀 수 있으므로 외부에 공개하는 용도로 쓰지 마세요.

## 파일 구성
아래 파일은 모두 `261020_bucheon_chatbot_kmc/` 폴더 안에 있습니다.

| 파일 | 설명 |
|---|---|
| `main.py` | 실행 진입점 (웹 / `--cli`) |
| `chatbot.py` | 챗봇 핵심 로직 (Groq → Gemini fallback, 키 검증/저장, 터미널 모드) |
| `app.py` | 웹 서버 (Flask) API |
| `store.py` | 대화 저장소 (`data/conversations.json`) |
| `memory.py` | 긴 대화 요약 및 모델 전달용 메시지 구성 |
| `templates/index.html` | 웹 채팅 화면 + 키 설정 창 |
| `requirements.txt` | 필요 라이브러리 |
| `.env.example` | 환경변수 템플릿 |
