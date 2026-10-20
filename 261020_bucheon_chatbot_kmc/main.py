"""실행 진입점.

    python main.py          웹 화면 (기본)
    python main.py --cli    터미널 챗봇
"""
import argparse
import threading
import webbrowser


def main():
    parser = argparse.ArgumentParser(description="Groq(+Gemini fallback) 챗봇")
    parser.add_argument("--cli", action="store_true", help="웹 대신 터미널에서 실행")
    parser.add_argument("--port", type=int, default=5000, help="웹 서버 포트 (기본 5000)")
    parser.add_argument("--no-browser", action="store_true", help="브라우저를 자동으로 열지 않음")
    args = parser.parse_args()

    if args.cli:
        from chatbot import run_cli
        run_cli()
        return

    from app import app
    url = f"http://127.0.0.1:{args.port}"
    if not args.no_browser:
        threading.Timer(1.0, webbrowser.open, args=(url,)).start()
    print(f"웹 챗봇 실행 중: {url}  (종료: Ctrl+C)")
    app.run(host="127.0.0.1", port=args.port, debug=False)


if __name__ == "__main__":
    main()
