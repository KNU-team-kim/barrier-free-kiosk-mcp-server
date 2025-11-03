## 종합설계프로젝트2 MCP Server

#### 실행 방법
1. `.env` 파일을 생성 후, 아래와 같이 입력한다.
```bash
OPENAI_API_KEY="ajtlrlajtlrl"
OPENAI_API_URL="https://ajtlrlajtlrl.com"
KIOSK_APP_URL="https://ajtlrlajtlrl.com"
```

2. 아래 명령어를 입력한다.
```bash
uv sync --frozen
uv run python server.py
```