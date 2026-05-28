# 로컬 온보딩

이 문서는 앱/웹 개발자가 로컬 백엔드에 붙어 토큰을 받고 인증 호출까지 확인하는 최소 절차입니다.

## 주소

- API base URL: `http://localhost:8000/api/v1`
- Swagger UI: `http://localhost:8000/docs`
- Health check: `GET http://localhost:8000/api/v1/health`

`/docs`는 로컬/스테이징에서만 열립니다. prod 런타임 OpenAPI는 닫혀 있고, 정적 계약은 `docs/openapi.json`과 `docs/api_reference.html`을 사용합니다.

## 기동

Repo 루트(`c:\projects\backend specification`)에서 실행합니다.

```powershell
docker compose -f backend/docker/docker-compose.yml up --build
```

다른 터미널에서 헬스체크를 확인합니다.

```powershell
Invoke-RestMethod http://localhost:8000/api/v1/health
```

응답의 `status`가 `ok`이면 DB/Redis까지 연결된 상태입니다.

## 사장님 개발 토큰 받기

로컬 DB에는 기본 계정이 자동 생성되지 않습니다. 사장님 계정을 한 번 가입한 뒤 로그인해서 토큰을 받습니다.

```powershell
$base = "http://localhost:8000/api/v1"
$email = "owner.local+$([DateTimeOffset]::UtcNow.ToUnixTimeSeconds())@example.com"
$password = "Password123!"

Invoke-RestMethod `
  -Method Post `
  -Uri "$base/auth/owner/signup" `
  -Headers @{ "Idempotency-Key" = [guid]::NewGuid().ToString() } `
  -ContentType "application/json" `
  -Body (@{
    email = $email
    password = $password
    representative_name = "로컬 사장님"
    phone_number = "010-0000-0000"
    accepted_terms_version = "2026-05-28"
    accepted_privacy_version = "2026-05-28"
  } | ConvertTo-Json)

$tokens = Invoke-RestMethod `
  -Method Post `
  -Uri "$base/auth/owner/login" `
  -Headers @{ "Idempotency-Key" = [guid]::NewGuid().ToString() } `
  -ContentType "application/json" `
  -Body (@{
    email = $email
    password = $password
  } | ConvertTo-Json)

$accessToken = $tokens.access_token
```

인증 호출 예시:

```powershell
Invoke-RestMethod `
  -Method Get `
  -Uri "$base/owners/me" `
  -Headers @{ Authorization = "Bearer $accessToken" }
```

## 앱 유저 토큰

앱 유저 로그인 엔드포인트는 `POST /api/v1/auth/apple`입니다. 요청에는 실제 Apple `id_token`이 필요하며, 외부에서 호출 가능한 로컬 mock Apple 로그인 경로는 현재 없습니다. 테스트 코드 내부 fixture만 Apple 검증을 mock합니다.

```json
{
  "id_token": "<apple-id-token>",
  "accepted_terms_version": "2026-05-28",
  "accepted_privacy_version": "2026-05-28",
  "nonce": "<optional>"
}
```

이 요청도 `Idempotency-Key` 헤더가 필요합니다. 응답은 `{ "tokens": { ... }, "user": { ... } }` 형태이며, 이후 유저 API에는 `tokens.access_token`을 `Authorization: Bearer <token>`으로 보냅니다.

## Idempotency-Key

`POST`, `PATCH`, `DELETE` 변이 요청은 `Idempotency-Key: <uuid-or-unique-string>` 헤더를 붙입니다. 같은 key와 같은 body를 재시도하면 서버가 저장된 응답을 재사용합니다.

## 커서 페이지네이션

목록 응답의 `page.next_cursor`가 있으면 다음 요청에 `?cursor=<next_cursor>&limit=<1..50>`로 전달합니다. 커서는 서버가 만든 불투명 문자열이므로 클라이언트에서 파싱하지 않습니다.

## 로컬 CORS

기본 허용 origin은 `localhost`/`127.0.0.1`의 `3000`, `5173`, `19006`, `8081`입니다. `allow_credentials=True` 때문에 `*`는 사용하지 않습니다. 다른 포트를 쓰는 웹앱은 `.env`의 `CORS_ORIGINS`를 JSON 배열 형식으로 추가합니다.

```env
CORS_ORIGINS=["http://localhost:3000","http://localhost:5173","http://127.0.0.1:3001"]
```
