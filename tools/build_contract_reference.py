from __future__ import annotations

import ast
import html
from collections import Counter
from dataclasses import dataclass, field
from datetime import UTC, datetime
from http import HTTPStatus
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
APP_ROOT = ROOT / "backend" / "app"
ENUMS_PATH = APP_ROOT / "models" / "enums.py"
OUTPUT_PATH = ROOT / "docs" / "api_contract_reference.html"


@dataclass(slots=True)
class ErrorOccurrence:
    message: str
    status: int
    location: str


@dataclass(slots=True)
class ErrorEntry:
    code: str
    messages: Counter[str] = field(default_factory=Counter)
    statuses: set[int] = field(default_factory=set)
    locations: list[str] = field(default_factory=list)

    def add(self, occurrence: ErrorOccurrence) -> None:
        if occurrence.message:
            self.messages[occurrence.message] += 1
        self.statuses.add(occurrence.status)
        self.locations.append(occurrence.location)

    @property
    def representative_message(self) -> str:
        if not self.messages:
            return ""
        return self.messages.most_common(1)[0][0]


def _literal_string(node: ast.AST | None) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def _literal_int(node: ast.AST | None) -> int | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, int):
        return node.value
    return None


def _is_app_error_call(node: ast.Call) -> bool:
    if isinstance(node.func, ast.Name):
        return node.func.id == "AppError"
    if isinstance(node.func, ast.Attribute):
        return node.func.attr == "AppError"
    return False


def _keyword_value(node: ast.Call, name: str) -> ast.AST | None:
    for keyword in node.keywords:
        if keyword.arg == name:
            return keyword.value
    return None


def _argument_value(node: ast.Call, index: int, keyword: str) -> ast.AST | None:
    if len(node.args) > index:
        return node.args[index]
    return _keyword_value(node, keyword)


def _status_from_node(node: ast.AST | None) -> int:
    if node is None:
        return int(HTTPStatus.BAD_REQUEST)

    literal = _literal_int(node)
    if literal is not None:
        return literal

    if (
        isinstance(node, ast.Attribute)
        and isinstance(node.value, ast.Name)
        and node.value.id == "HTTPStatus"
    ):
        status = getattr(HTTPStatus, node.attr, None)
        if isinstance(status, HTTPStatus):
            return int(status)

    return int(HTTPStatus.BAD_REQUEST)


def _status_label(status: int) -> str:
    try:
        http_status = HTTPStatus(status)
    except ValueError:
        return str(status)
    return f"{status} {http_status.name}"


def _relative_location(path: Path, line: int) -> str:
    return f"{path.relative_to(ROOT).as_posix()}:{line}"


def collect_errors() -> list[ErrorEntry]:
    entries: dict[str, ErrorEntry] = {}
    for path in sorted(APP_ROOT.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call) or not _is_app_error_call(node):
                continue

            code = _literal_string(_argument_value(node, 0, "code"))
            if code is None:
                continue

            message = _literal_string(_argument_value(node, 1, "message")) or ""
            status = _status_from_node(_argument_value(node, 2, "status_code"))
            occurrence = ErrorOccurrence(
                message=message,
                status=status,
                location=_relative_location(path, node.lineno),
            )
            entries.setdefault(code, ErrorEntry(code=code)).add(occurrence)
    return [entries[code] for code in sorted(entries)]


def collect_enums() -> dict[str, list[str]]:
    tree = ast.parse(ENUMS_PATH.read_text(encoding="utf-8"), filename=str(ENUMS_PATH))
    enums: dict[str, list[str]] = {}
    for node in tree.body:
        if not isinstance(node, ast.ClassDef):
            continue
        base_names = {
            base.id
            for base in node.bases
            if isinstance(base, ast.Name)
        }
        if "StrEnum" not in base_names:
            continue

        values: list[str] = []
        for statement in node.body:
            if not isinstance(statement, ast.Assign):
                continue
            value = _literal_string(statement.value)
            if value is not None:
                values.append(value)
        enums[node.name] = values
    return enums


def _escape(value: Any) -> str:
    return html.escape(str(value), quote=True)


def _code(value: str) -> str:
    return f"<code>{_escape(value)}</code>"


def _render_error_rows(entries: list[ErrorEntry]) -> str:
    rows: list[str] = []
    for entry in entries:
        statuses = ", ".join(_status_label(status) for status in sorted(entry.statuses))
        locations = "<br>".join(_code(location) for location in entry.locations)
        message = entry.representative_message or "-"
        if len(entry.messages) > 1:
            message = f"{message} 외 {len(entry.messages) - 1}개 메시지"
        rows.append(
            "<tr>"
            f"<td>{_code(entry.code)}</td>"
            f"<td>{_escape(statuses)}</td>"
            f"<td>{_escape(message)}</td>"
            f"<td class=\"locations\">{locations}</td>"
            "</tr>"
        )
    return "\n".join(rows)


def _render_enum_rows(enums: dict[str, list[str]]) -> str:
    rows: list[str] = []
    for enum_name, values in enums.items():
        value_html = " ".join(f"<span class=\"pill\">{_escape(value)}</span>" for value in values)
        rows.append(
            "<tr>"
            f"<td>{_code(enum_name)}</td>"
            f"<td>{value_html}</td>"
            "</tr>"
        )
    return "\n".join(rows)


def _render_html(entries: list[ErrorEntry], enums: dict[str, list[str]]) -> str:
    return f"""<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Snail API 계약 레퍼런스</title>
  <style>
    :root {{
      --bg: #f6f7f9;
      --panel: #ffffff;
      --line: #d7dde6;
      --text: #17202a;
      --muted: #667485;
      --accent: #0f766e;
      --accent-weak: #e7f4f1;
      --blue-weak: #edf3ff;
      --blue: #1d4ed8;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      background: var(--bg);
      color: var(--text);
      font-family: Arial, "Malgun Gothic", sans-serif;
      font-size: 14px;
    }}
    header {{
      background: var(--panel);
      border-bottom: 1px solid var(--line);
      padding: 18px 22px;
    }}
    main {{
      max-width: 1180px;
      margin: 0 auto;
      padding: 24px 20px 48px;
    }}
    h1 {{ margin: 0 0 5px; font-size: 22px; letter-spacing: 0; }}
    h2 {{ margin: 0 0 10px; font-size: 18px; letter-spacing: 0; }}
    p {{ margin: 0; color: var(--muted); line-height: 1.55; }}
    a {{ color: var(--blue); text-decoration: none; }}
    a:hover {{ text-decoration: underline; }}
    code {{
      font-family: Consolas, "Courier New", monospace;
      font-size: 12px;
      background: #f1f5f9;
      border-radius: 4px;
      padding: 1px 4px;
    }}
    .meta {{ color: var(--muted); font-size: 12px; line-height: 1.45; }}
    .section {{
      border: 1px solid var(--line);
      background: var(--panel);
      border-radius: 6px;
      padding: 18px;
      margin-bottom: 14px;
    }}
    .grid {{
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 12px;
    }}
    .note {{
      border: 1px solid #bfdbfe;
      background: var(--blue-weak);
      color: #1e3a8a;
      border-radius: 6px;
      padding: 10px;
      line-height: 1.55;
      margin: 10px 0 0;
    }}
    ul {{ margin: 8px 0 0; padding-left: 18px; line-height: 1.7; }}
    table {{
      width: 100%;
      border-collapse: collapse;
      table-layout: fixed;
    }}
    th, td {{
      border-bottom: 1px solid var(--line);
      padding: 9px 10px;
      text-align: left;
      vertical-align: top;
      line-height: 1.5;
      word-break: break-word;
    }}
    th {{
      background: #fafbfc;
      color: var(--muted);
      font-size: 12px;
      font-weight: 700;
    }}
    tr:last-child td {{ border-bottom: 0; }}
    .locations code {{ display: inline-block; margin: 0 0 3px; }}
    .pill {{
      display: inline-block;
      border: 1px solid var(--line);
      background: var(--accent-weak);
      color: var(--accent);
      border-radius: 999px;
      padding: 2px 8px;
      margin: 0 4px 4px 0;
      font-family: Consolas, "Courier New", monospace;
      font-size: 12px;
    }}
    .compact td:first-child, .compact th:first-child {{ width: 230px; }}
    @media (max-width: 820px) {{
      main {{ padding: 18px 12px 36px; }}
      .grid {{ grid-template-columns: 1fr; }}
      table {{ table-layout: auto; }}
      th, td {{ min-width: 140px; }}
      .table-wrap {{ overflow-x: auto; }}
    }}
  </style>
</head>
<body>
  <header>
    <h1>Snail API 계약 레퍼런스</h1>
    <div class="meta">코드에서 자동 추출 · 에러는 <code>AppError(...)</code>, enum은 <code>app/models/enums.py</code> 기준</div>
  </header>
  <main>
    <section class="section">
      <h2>① 에러코드 카탈로그</h2>
      <p><code>backend/app/**/*.py</code>의 <code>AppError("CODE", "메시지", HTTPStatus.X)</code> 호출을 AST로 스캔해 생성합니다. 문자열 리터럴 code만 표에 포함됩니다.</p>
      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th style="width: 230px;">code</th>
              <th style="width: 160px;">HTTP status</th>
              <th>의미</th>
              <th style="width: 360px;">발생 위치</th>
            </tr>
          </thead>
          <tbody>
            {_render_error_rows(entries)}
          </tbody>
        </table>
      </div>
    </section>

    <div class="grid">
      <section class="section">
        <h2>② 인증 계약</h2>
        <p>인증은 <code>Authorization: Bearer &lt;access_token&gt;</code> 헤더를 사용합니다.</p>
        <ul>
          <li>토큰이 없거나 유효하지 않으면 <code>UNAUTHORIZED</code> / 401.</li>
          <li>토큰의 <code>type</code>은 <code>access</code>여야 하며, 아니면 <code>INVALID_TOKEN_TYPE</code> / 401.</li>
          <li><code>current_user_id</code>는 <code>actor_type=user</code>, <code>current_owner_id</code>는 <code>actor_type=owner</code>만 허용합니다.</li>
          <li>로그인은 되어 있지만 actor가 맞지 않거나 소유권이 없으면 <code>FORBIDDEN</code> / 403.</li>
          <li>공개 조회 일부는 인증 없이 접근하며, 선택 인증은 user 토큰일 때만 viewer id를 사용합니다.</li>
        </ul>
        <div class="note">actor 범위: <code>anonymous</code>, <code>user</code>, <code>owner</code>, <code>admin</code>, <code>system</code>. 현재 API 의존성은 user/owner 중심입니다.</div>
      </section>

      <section class="section">
        <h2>③ 페이지네이션(커서)</h2>
        <p>커서는 클라이언트가 해석하지 않는 opaque string입니다.</p>
        <ul>
          <li>요청 파라미터: <code>cursor</code> optional, <code>limit</code> 기본 20, 허용 범위 1..50.</li>
          <li>첫 요청은 cursor 없이 호출하고, 다음 페이지는 응답의 <code>next_cursor</code>를 그대로 전달합니다.</li>
          <li>일반 리스트 응답은 <code>data</code>, <code>page.next_cursor</code>, <code>page.has_next</code>, <code>request_id</code> 형태입니다.</li>
          <li>일부 피드 응답은 <code>items</code>, <code>next_cursor</code> 형태의 <code>PageResult</code>를 사용합니다.</li>
          <li>잘못된 cursor는 <code>INVALID_CURSOR</code> / 400.</li>
        </ul>
      </section>
    </div>

    <section class="section">
      <h2>④ Idempotency-Key</h2>
      <p>모든 변이 요청은 <code>Idempotency-Key</code> 헤더가 필요합니다.</p>
      <ul>
        <li>대상: 상태를 바꾸는 POST/PATCH/PUT/DELETE 계열 요청.</li>
        <li>누락 또는 빈 값이면 <code>IDEMPOTENCY_KEY_REQUIRED</code> / 400.</li>
        <li>같은 actor, 같은 key, 같은 method/path/body는 저장된 응답을 재사용합니다.</li>
        <li>같은 key로 다른 요청 본문을 보내면 <code>IDEMPOTENCY_MISMATCH</code> / 409.</li>
        <li>클라이언트는 재시도 가능한 요청마다 UUID 등 충분히 고유한 key를 생성해야 합니다.</li>
      </ul>
    </section>

    <section class="section">
      <h2>⑤ Enum 값 표</h2>
      <p>API 문서와 JSON payload는 enum의 소문자 <code>value</code>를 사용합니다. DB enum 컬럼은 SQLAlchemy <code>native_enum=False</code> 특성상 대문자 NAME이 저장될 수 있으므로, 클라이언트 계약은 아래 값만 기준으로 봅니다.</p>
      <div class="table-wrap">
        <table class="compact">
          <thead>
            <tr>
              <th>Enum</th>
              <th>API values</th>
            </tr>
          </thead>
          <tbody>
            {_render_enum_rows(enums)}
          </tbody>
        </table>
      </div>
    </section>
  </main>
</body>
</html>
"""


def main() -> None:
    entries = collect_errors()
    enums = collect_enums()
    OUTPUT_PATH.write_text(_render_html(entries, enums), encoding="utf-8")
    print(
        f"generated_at={datetime.now(UTC).isoformat()} "
        f"errors={len(entries)} enums={len(enums)} output={OUTPUT_PATH}"
    )


if __name__ == "__main__":
    main()
