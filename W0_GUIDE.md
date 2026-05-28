# 🛠️ W0 스텝-바이-스텝 실행 가이드

> 사용자(민석)가 직접 따라가며 W0(개발 시작 전 외부 셋업)을 완료하기 위한 매뉴얼.
> 진행도 추적은 [W0_CHECKLIST.md](W0_CHECKLIST.md), 이 문서는 실제 실행 방법.

작성: 2026-05-28

---

## 0. 사전 준비물 (시작 전 확인)

물리·계정 준비물:
- [ ] 본인 신분증 (사업자등록·은행계좌 인증용)
- [ ] **사업장 주소** (자택도 OK — 통신판매업 신고 시 사용)
- [ ] **휴대폰 본인인증 가능** (대부분 KTX 인증 사용)
- [ ] **해외결제 가능 신용카드** (Apple $99, OpenAI, GCP 결제용)
- [ ] **비밀번호 매니저** (1Password / Bitwarden / Apple 키체인) — 시크릿 13개 이상 저장 필요
- [ ] **이메일 1개** — 모든 서비스 가입에 동일 메일 사용 권장
- [ ] **Google 계정** (GCP·Cloudflare 가입에 OAuth로 편함)
- [ ] **Apple ID** (Apple Developer 가입용 — 2FA 필수)
- [ ] **GitHub 계정** (이미 있을 것)

> 💡 모든 외부 서비스 가입 시 **이메일·비밀번호·2FA 백업코드**를 즉시 비밀번호 매니저에 저장. 한 번이라도 빠뜨리면 복구 지옥.

---

## 1. 의존성 그래프 (순서가 중요한 이유)

```
사업자등록 ──────┬──► 카카오톡 채널 ──► 알림톡 발신프로필 심사 (5~10영업일)
                │
                └──► Apple Developer (사업자 옵션 시 DUNS 2주+)
GCP 결제계정 ──────► GCP 프로젝트 ──► Cloud SQL ──► GCE ──► deploy.yml
                                └──► GCS 버킷
                                └──► Service Account (GitHub Actions용)
OpenAI 결제 ──► $5 결제 ──► Tier-1 ──► API 키 발급
도메인 구입 ──► Cloudflare DNS ──► GCE IP A 레코드
Apple Dev ──► App ID ──► Sign In Apple 키 ──► APNs 키
```

**가장 위험한 리드타임**:
- 🔴 카카오 알림톡 발신프로필 심사: **5~10영업일** (가장 일찍 시작)
- 🔴 Apple Developer 사업자 가입 (DUNS 번호 필요): **2주+** → 개인 계정으로 시작 권장
- 🟡 통신판매업 신고: **1~3영업일**
- 🟡 사업자등록증 발급: **1~2일** (홈택스 즉시 발급도 가능)

---

## 2. Day 1 — 결제 계정 3종 + 사업자등록

### Step 1.1. 사업자등록 신청 (홈택스 온라인)

1. **링크**: https://hometax.go.kr → 로그인(공동인증서 또는 간편인증)
2. 상단 메뉴: **신청/제출 → 사업자등록신청·정정 등 → 사업자등록 신청(개인)**
3. 입력:
   - 상호: 예) `s-nail` 또는 본인 결정 상호
   - 업태: `정보통신업` (또는 `서비스업`)
   - 종목: `응용소프트웨어 개발 및 공급업`
   - 업종코드: `722000` (소프트웨어 개발)
   - 사업장 소재지: 자택 주소 가능
   - 개업연월일: 오늘 또는 이번주 월요일
4. 제출 → **즉시 발급** (보통 1시간 내, 늦어도 익일)
5. 발급 후 **사업자등록증 PDF 다운로드** → 비밀번호 매니저 또는 안전한 폴더에 저장

> ⚠️ 통신판매업 신고는 **사업자등록 발급 이후** 가능. Step 2.5에서 진행.

### Step 1.2. GCP 결제 계정 + $300 크레딧

1. **링크**: https://console.cloud.google.com → 로그인
2. 우측 상단 알림에 "Get $300 in free credits" 보이면 클릭. 없으면:
   - 좌측 상단 햄버거 메뉴 → **결제 → 결제 계정 만들기**
   - 약관 동의 → 카드 등록 → 본인인증
3. **프로젝트 생성**:
   - 상단 프로젝트 선택 → **새 프로젝트**
   - 이름: `snail-prod` (Project ID는 자동 또는 직접 지정 — `snail-prod-XXXX`)
   - **Project ID 메모** → 비번 매니저에 `GCP_PROJECT_ID` 항목으로 저장
4. **예산 알림 등록** (꼭!):
   - 좌측 메뉴: **결제 → Budgets & alerts → 예산 만들기**
   - 이름: `snail-monthly`
   - 적용 대상: 방금 만든 프로젝트
   - 예산액: `$100`
   - 알림 임계값: **50% / 80% / 100%** (이메일)
5. **API 활성화**:
   - 좌측 메뉴: **API 및 서비스 → 라이브러리**
   - 다음 4개 검색 후 각각 "사용 설정":
     - Cloud SQL Admin API
     - Cloud Storage API
     - Compute Engine API
     - Artifact Registry API (또는 Container Registry API)

### Step 1.3. Apple Developer Program 결제 ($99/년)

1. **링크**: https://developer.apple.com/programs/enroll/
2. Apple ID 로그인 (2FA 활성화 필수)
3. 등록 유형 선택:
   - **개인(Individual)** 권장 (즉시 시작 가능)
   - 사업자(Organization)는 D-U-N-S 번호 신청 필요 → 2주+ 소요 → MVP 단계에선 개인 추천
4. 결제: $99 USD
5. 보통 24~48시간 내 가입 승인 메일 도착
6. 승인 후 **App Store Connect** 접근 가능 — 이때부터 Step 5.x 진행 가능

### Step 1.4. OpenAI 결제 + Tier-1 진입

1. **링크**: https://platform.openai.com → 로그인 또는 가입
2. 좌측 메뉴: **Settings → Billing**
3. **Add to credit balance**: $10 결제 (Tier-1 진입에 $5 이상 필요, 여유분 포함)
4. 좌측: **Settings → Limits**
   - **Hard limit: $50** 설정 (월간)
   - **Soft limit: $30** (이메일 알림)
5. 좌측: **API keys → Create new secret key**
   - 이름: `snail-prod`
   - 권한: **Restricted → models.read + chat.completions.write + embeddings.write**
   - 발급된 키(`sk-...`) **즉시 비번 매니저에 저장** — 한 번만 보여줌
6. Tier 확인: **Settings → Limits → Current Tier**가 `Tier 1`이 되면 OK (결제 5분 후 자동 승급)

> 💡 OpenAI는 Tier에 따라 동시 요청 수와 토큰/분 제한이 다름. Tier 1 = `gpt-4o-mini` 500 RPM, 200K TPM 정도. MVP 시연에 충분.

---

## 3. Day 2 — 도메인 + Cloudflare + 카카오 채널

### Step 2.1. 도메인 구입

1. **추천 등록사**:
   - **Cloudflare Registrar** (https://dash.cloudflare.com) — 도매가, 자동갱신, DNS 통합
   - 가비아 (https://gabia.com) — 한국 결제 편리
   - Namecheap — 가격 저렴
2. 도메인 선택: 예) `snail.app`, `snail-kr.com` 등
3. WHOIS Privacy ON (개인정보 보호)
4. 결제 후 등록 완료 → 보통 즉시 활성화 (`.app`은 HTTPS 강제 — Caddy 자동 발급되니 OK)

### Step 2.2. Cloudflare DNS 연결 (Cloudflare Registrar로 샀으면 자동, 다른 곳이면 이전 필요)

1. **링크**: https://dash.cloudflare.com → 로그인 (없으면 가입)
2. **Add a Site** → 도메인 입력 → 무료 플랜 선택
3. Cloudflare가 알려준 **네임서버 2개**를 등록사 사이트에서 변경
   - 가비아: 도메인 관리 → 네임서버 변경
4. 전파 확인: `nslookup -type=NS yourdomain.com` (보통 30분~24시간)
5. DNS 레코드 추가:
   - 일단은 placeholder 잡고, GCE IP 발급 후(Step 5.x) 업데이트
   - `Type: A, Name: api, IPv4: 1.1.1.1 (placeholder), Proxy: OFF (DNS only)`
6. **SSL/TLS 설정**: 좌측 메뉴 → SSL/TLS → Overview → **Full (strict)** 선택
   - Caddy가 GCE에서 Let's Encrypt 인증서 자체 발급 → Cloudflare는 통과만

### Step 2.3. 카카오톡 채널 개설

1. **링크**: https://center-pf.kakao.com → 카카오 계정 로그인
2. 우측 상단 **새 채널 만들기**
3. 입력:
   - 채널명: `s-nail` (서비스명과 동일)
   - 검색용 ID: `@snail` 같은 영문 ID
   - 카테고리: `생활/여가 → 미용`
   - 소개글, 프로필 이미지 (1:1, 640x640 권장)
4. 개설 완료 → 채널 ID와 검색용 ID 메모 (비번 매니저)

### Step 2.4. 알림톡 발송 대행사 가입 (Bizppurio 추천)

1. **링크**: https://www.bizppurio.com → 회원가입
2. 사업자 회원으로 가입 (사업자등록증 PDF 업로드)
3. 가입 승인 대기 (보통 즉일~1영업일)
4. 승인 후 **API 사용자 ID + API Key 발급** → 비번 매니저 저장

> 대안: Aligo (https://smartsms.aligo.in), NHN Cloud, SOLAPI 등. Bizppurio가 알림톡 점유율 1위라서 자료 많음.

### Step 2.5. 통신판매업 신고 (사업자등록증 발급 후 가능)

1. **링크**: https://www.easylaw.go.kr → 통신판매업 신고 검색, 또는 정부24
2. 거주지 시·군·구청 민원실 방문도 가능 (1시간 내 발급)
3. 필요서류: 사업자등록증, 통신판매업 신고서 (현장 작성)
4. 발급 후 통신판매업 신고증 PDF 보관

---

## 4. Day 3 — 알림톡 발신프로필 + 템플릿 심사

### Step 3.1. 발신프로필 등록 (Bizppurio → 카카오 심사)

1. Bizppurio 콘솔 로그인 → **알림톡 → 발신프로필 신청**
2. 카카오톡 채널 연동 (Step 2.3에서 만든 채널 검색)
3. 사업자등록증 업로드
4. 신청 → **카카오 심사 대기 3~7영업일**
5. 승인 메일 도착하면 **발신프로필 키(`pfId` 또는 `senderKey`)** 발급 → 비번 매니저 저장
   - `.env`의 `KAKAO_SENDER_KEY` 값이 이것

### Step 3.2. 알림톡 템플릿 사전 심사

> 알림톡은 사전 심사된 템플릿 코드로만 발송 가능. 자유문구 금지.

1. Bizppurio 콘솔 → **알림톡 → 템플릿 신청**
2. MVP에 필요한 템플릿 7개 신청 (각각 따로 등록):

| 템플릿 코드 | 내용 |
|---|---|
| `RESERVATION_REQUESTED` | (사장님 수신) #{유저닉네임}님이 #{날짜} #{시간}에 예약을 요청하셨어요. 인박스에서 확인해주세요. |
| `RESERVATION_CONFIRMED` | (유저 수신) #{샵명} 예약이 확정되었어요. #{날짜} #{시간}에 만나요. |
| `RESERVATION_PAYMENT_REQUIRED` | (유저 수신) 예약금 #{금액}원을 #{은행} #{계좌번호} (예금주 #{예금주})로 입금해주세요. |
| `RESERVATION_REJECTED` | (유저 수신) #{샵명} 예약이 거절되었어요. 사유: #{사유} |
| `RESERVATION_CANCELLED_BY_SHOP` | (유저 수신) #{샵명}에서 예약을 취소했어요. 사유: #{사유} |
| `RESERVATION_REMINDER` | (유저 수신) 내일 #{시간}에 #{샵명} 시술이 예정되어 있어요. |
| `RESERVATION_COMPLETED` | (유저 수신) 시술이 완료되었어요. 후기를 남겨주세요. |

3. 각 템플릿 등록 후 카카오 심사 **2~5영업일**
4. 심사 통과 후 **템플릿 코드** 발급 → 비번 매니저에 7개 모두 저장

> ⚠️ 광고성 문구 금지 (예: "할인", "이벤트", "혜택" 등). 정보성만. 거부되면 문구 수정 후 재신청.

---

## 5. Day 4 — 법무 검토 + GitHub 셋업

### Step 4.1. 법무 초안 마무리

1. `legal/privacy_policy.draft.md` 와 `legal/terms_of_service.draft.md` 열기
2. 모든 `{{...}}` placeholder 채우기:
   - 회사명, 사업자등록번호, 대표자명
   - 이메일, 전화번호, 주소
   - 수집 항목, 보유 기간
3. 변호사 검토 의뢰 (비용 5~30만원, 1~3영업일)
   - 추천: 로톡(https://lawtalk.co.kr) 또는 지인 변호사
4. 검토 완료 후 `legal/privacy_policy.md`, `legal/terms_of_service.md` (draft 제외) 파일로 확정
5. 두 파일을 **GitHub Pages 또는 정적 호스팅**에 공개 (앱스토어 심사 시 URL 필요)
   - 빠른 방법: `legal/` 폴더를 GitHub Pages로 publish

### Step 4.2. GitHub 저장소 + Secrets 13종 등록

1. 기존 repo 사용 또는 신규 repo 생성 (`snail-backend` 이름 권장)
2. **Settings → Secrets and variables → Actions → New repository secret** 으로 다음 13개 모두 등록:

| 시크릿 이름 | 값 | 출처 |
|---|---|---|
| `GCP_PROJECT_ID` | `snail-prod-XXXX` | Step 1.2 |
| `GCP_SA_KEY` | 서비스 계정 JSON 전체 | Step 5.2에서 발급 |
| `GCE_HOST` | GCE 외부 IP | Step 5.4에서 발급 |
| `GCE_USER` | `ubuntu` (또는 SSH 사용자) | Step 5.4 |
| `GCE_SSH_PRIVATE_KEY` | SSH private key 전체 | Step 5.4 |
| `CLOUD_SQL_INSTANCE_CONNECTION_NAME` | `프로젝트:리전:인스턴스` | Step 5.3 |
| `API_DOMAIN` | `api.snail.app` 등 | Step 2.1 |
| `JWT_SECRET` | 32자 이상 랜덤 문자열 | `openssl rand -hex 32` |
| `OPENAI_API_KEY` | `sk-...` | Step 1.4 |
| `KAKAO_SENDER_KEY` | `pfId...` | Step 3.1 |
| `BIZPPURIO_USER_ID` | Bizppurio API ID | Step 2.4 |
| `BIZPPURIO_API_KEY` | Bizppurio API Key | Step 2.4 |
| `SENTRY_DSN` | Sentry DSN (선택) | https://sentry.io 가입 후 |

3. **Branch protection (main)**:
   - Settings → Branches → Add rule
   - Branch: `main`
   - ☑ Require pull request before merging
   - ☑ Require status checks (ci.yml의 모든 job 선택)
4. 로컬에 pre-commit 설치:
   ```powershell
   cd backend
   pip install pre-commit
   pre-commit install
   ```

---

## 6. Day 5 — GCP 리소스 + Apple 키

### Step 5.1. GCP CLI 설치 (한 번만)

1. **링크**: https://cloud.google.com/sdk/docs/install
2. Windows: `GoogleCloudSDKInstaller.exe` 다운 → 설치
3. PowerShell 재시작 후:
   ```powershell
   gcloud auth login
   gcloud config set project $env:GCP_PROJECT_ID    # Step 1.2에서 받은 ID
   ```

### Step 5.2. 서비스 계정 + GCR/Artifact Registry 권한

```powershell
# 서비스 계정 생성
gcloud iam service-accounts create snail-deploy --display-name="Snail Deploy SA"

# 권한 부여 (GCR push + GCE 관리 + Cloud SQL client)
$SA = "snail-deploy@$($env:GCP_PROJECT_ID).iam.gserviceaccount.com"
gcloud projects add-iam-policy-binding $env:GCP_PROJECT_ID --member="serviceAccount:$SA" --role="roles/storage.admin"
gcloud projects add-iam-policy-binding $env:GCP_PROJECT_ID --member="serviceAccount:$SA" --role="roles/compute.instanceAdmin.v1"
gcloud projects add-iam-policy-binding $env:GCP_PROJECT_ID --member="serviceAccount:$SA" --role="roles/cloudsql.client"

# JSON 키 발급
gcloud iam service-accounts keys create snail-deploy-key.json --iam-account=$SA
```

발급된 `snail-deploy-key.json` 내용 전체를 GitHub Secret `GCP_SA_KEY`에 붙여넣기. **로컬 파일은 즉시 삭제** (`.gitignore`에 포함되지만 안전).

### Step 5.3. Cloud SQL (PostgreSQL 16 + pgvector) 인스턴스

1. **링크**: https://console.cloud.google.com/sql/instances → **인스턴스 만들기**
2. PostgreSQL 선택
3. 설정:
   - 인스턴스 ID: `snail-pg-prod`
   - 비밀번호: 강력한 랜덤 (16자+, 비번 매니저 저장)
   - 데이터베이스 버전: **PostgreSQL 16**
   - 리전: `asia-northeast3` (서울)
   - Zonal availability: **Single zone** (MVP는 비용 ↓)
   - Machine: **db-perf-optimized-N-1** (vCPU 1, RAM 8GB) — 또는 `db-f1-micro` 비용 최소화
   - 스토리지: SSD 10GB, 자동 증가 ON
4. 만들기 → 10~15분 대기
5. 인스턴스 클릭 → **연결 → 연결 이름 복사** (`프로젝트:리전:인스턴스`)
   → GitHub Secret `CLOUD_SQL_INSTANCE_CONNECTION_NAME` 등록
6. 데이터베이스 + 사용자 생성:
   ```powershell
   gcloud sql databases create snail --instance=snail-pg-prod
   gcloud sql users create snail --instance=snail-pg-prod --password=YOUR_PASSWORD
   ```
7. **pgvector 확장 활성화**:
   - Cloud Console에서 인스턴스 → **Flags → 새 플래그 추가**
   - 플래그: `cloudsql.enable_pgvector` → 값: `on`
   - 인스턴스 재시작

### Step 5.4. GCE 인스턴스 (운영 서버)

```powershell
# e2-small (vCPU 2, RAM 2GB) — MVP 최소 사양
gcloud compute instances create snail-api `
    --zone=asia-northeast3-a `
    --machine-type=e2-small `
    --image-family=ubuntu-2204-lts `
    --image-project=ubuntu-os-cloud `
    --boot-disk-size=20GB `
    --tags=http-server,https-server

# 외부 IP 확인 → GitHub Secret GCE_HOST 등록
gcloud compute instances describe snail-api --zone=asia-northeast3-a --format="get(networkInterfaces[0].accessConfigs[0].natIP)"

# 방화벽 규칙 (80/443 오픈)
gcloud compute firewall-rules create allow-https --allow=tcp:443,tcp:80 --target-tags=http-server,https-server
```

SSH 키 생성 + 등록:
```powershell
# 로컬에서 SSH 키 생성 (Windows OpenSSH)
ssh-keygen -t ed25519 -f $HOME\.ssh\snail_gce -C "snail-deploy"

# 공개키를 GCE 메타데이터에 등록
gcloud compute instances add-metadata snail-api --zone=asia-northeast3-a `
    --metadata-from-file ssh-keys="$HOME\.ssh\snail_gce.pub"

# private key 내용을 GitHub Secret GCE_SSH_PRIVATE_KEY에 등록
Get-Content $HOME\.ssh\snail_gce
# → 출력 전체(BEGIN ~ END 포함)를 복사해서 secret에 붙여넣기
```

GCE 첫 SSH 접속 + Docker 설치:
```powershell
ssh -i $HOME\.ssh\snail_gce ubuntu@$GCE_HOST
```

GCE 인스턴스 내부에서:
```bash
# Docker 설치
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker $USER
sudo systemctl enable docker

# 디렉토리 생성
sudo mkdir -p /opt/snail
sudo chown $USER:$USER /opt/snail

# 재로그인 (그룹 적용)
exit
```

### Step 5.5. .env.prod 파일 GCE에 업로드 (수동, 한 번만)

로컬에서:
```powershell
# .env.prod 파일 만들기 (gitignore에 포함됨, 절대 commit X)
# backend/.env.example을 복사해서 모든 값을 실제 운영 값으로 채움
cd backend
Copy-Item .env.example .env.prod

# 편집 — 모든 시크릿 채우기 (JWT, OpenAI, Kakao, Bizppurio, Apple, DATABASE_URL 등)
# DATABASE_URL은: postgresql+asyncpg://snail:비번@cloud-sql-proxy:5432/snail
# (compose에서 cloud-sql-proxy 서비스명을 호스트로 사용)
notepad .env.prod

# GCE로 업로드
scp -i $HOME\.ssh\snail_gce .env.prod ubuntu@${GCE_HOST}:/opt/snail/.env
```

> ⚠️ `.env.prod`는 로컬에 둬도 되지만 **절대 git에 안 들어가게** 주의. `.gitignore`에 `.env*` 패턴이 있는지 재확인.

### Step 5.6. GCS 버킷

```powershell
gcloud storage buckets create gs://snail-designs-prod --location=asia-northeast3 --uniform-bucket-level-access

# CORS 설정 (앱에서 직접 업로드)
@'
[
  {
    "origin": ["https://yourdomain.com", "capacitor://localhost", "ionic://localhost"],
    "method": ["GET", "PUT", "POST"],
    "responseHeader": ["Content-Type", "x-goog-content-length-range"],
    "maxAgeSeconds": 3600
  }
]
'@ | Out-File cors.json -Encoding utf8

gcloud storage buckets update gs://snail-designs-prod --cors-file=cors.json
Remove-Item cors.json
```

### Step 5.7. Apple Sign In + APNs 키 발급

> Apple Developer 가입 승인(Step 1.3) 완료 후 진행.

1. **링크**: https://developer.apple.com/account → Certificates, Identifiers & Profiles
2. **App ID 생성**:
   - Identifiers → **+ → App IDs → App**
   - Description: `Snail App`
   - Bundle ID: `com.snail.app` (또는 본인 도메인 역순)
   - Capabilities: ☑ **Sign In with Apple**, ☑ **Push Notifications**
3. **Services ID** (Sign In with Apple용):
   - Identifiers → **+ → Services IDs**
   - Description: `Snail Sign In Service`
   - Identifier: `com.snail.app.signin`
   - ☑ Sign In with Apple → Configure → Primary App ID 선택 → Domains/Return URLs (앱이라 비워도 OK)
4. **APNs Auth Key (.p8) 발급**:
   - Keys → **+ → Apple Push Notifications service (APNs)**
   - 이름: `Snail APNs Key`
   - 다운로드 → **AuthKey_XXXXX.p8** 저장
   - **Key ID 메모** (한 번만 보여줌)
5. **Sign In with Apple 키도 동일 방식으로 발급** (APNs 키와 별도)
   - Keys → **+ → Sign In with Apple**
   - Primary App ID 선택
   - 다운로드 → `AuthKey_YYYYY.p8` 저장
6. **Team ID 확인**: 우측 상단 사용자명 옆에 표시 (`Membership` 페이지에도 있음)
7. 비번 매니저에 저장:
   - `APPLE_TEAM_ID`
   - `APPLE_CLIENT_ID = com.snail.app.signin` (Services ID)
   - `APPLE_KEY_ID` (Sign In with Apple 키)
   - `APNS_KEY_ID`, `APNS_TEAM_ID = APPLE_TEAM_ID`, `APNS_BUNDLE_ID = com.snail.app`
   - 두 `.p8` 파일은 안전한 폴더에 보관 (GCE의 `/opt/snail/secrets/`에 scp로 업로드)

---

## 7. Day 6 — 로컬 검증

### Step 6.1. Docker Desktop 설치

1. **링크**: https://www.docker.com/products/docker-desktop/
2. Windows installer 다운 → 설치
3. 설치 중 **WSL2 백엔드** 선택 (또는 설치 후 Settings에서 활성화)
4. 재부팅 후 Docker Desktop 실행 → 우측 하단 고래 아이콘 녹색 확인
5. PowerShell:
   ```powershell
   docker --version
   docker compose version
   ```

### Step 6.2. 로컬 인프라 기동 + 통합 테스트

```powershell
cd "c:\projects\backend specification\backend"

# Postgres + Redis만 띄움 (API는 venv에서 직접 실행)
docker compose -f docker/docker-compose.yml up -d postgres redis

# 통합 테스트 한 번 (이게 통과해야 운영 배포도 안전)
.\scripts\check.ps1
```

기대 결과: `93 passed`. 실패하면 stop — 코드 문제이지 W0 문제 아님.

### Step 6.3. 첫 commit + 푸시

```powershell
git add .
git commit -m "chore: W0 setup complete"
git push origin main
```

→ GitHub Actions **ci.yml** 자동 실행. 5~10분 후 녹색 체크 확인.

---

## 8. Day 7 — deploy.yml 첫 시도

### Step 7.1. 파이프라인 점검 항목 (먼저 수정 필요)

[deploy.yml](backend/.github/workflows/deploy.yml) 현재 상태에서 다음 5개 수정 필요 (D1~D5):

1. **D1 Caddyfile 도메인 변수화**:
   - [Caddyfile](backend/docker/Caddyfile) 첫 줄을 `{$API_DOMAIN} {` 로 변경
   - `docker-compose.prod.yml`의 caddy 서비스에 `environment: API_DOMAIN: ${API_DOMAIN}` 추가
2. **D2 .env 사전 배포**:
   - Step 5.5에서 이미 `/opt/snail/.env`로 업로드 완료. OK.
3. **D3 arq worker 컨테이너 추가**:
   - `docker-compose.prod.yml`에 새 서비스 추가:
     ```yaml
     worker:
       image: gcr.io/${GCP_PROJECT_ID}/snail-backend:${IMAGE_TAG:-latest}
       restart: unless-stopped
       env_file: /opt/snail/.env
       depends_on: [redis, cloud-sql-proxy]
       command: ["arq", "app.workers.main.WorkerSettings"]
     ```
4. **D4 alembic을 별도 step으로 분리**:
   - deploy.yml의 `docker compose ... up -d` 다음에:
     ```yaml
     docker compose -f docker-compose.prod.yml run --rm api alembic upgrade head
     ```
5. **D5 health check 60초로 연장**:
   - deploy.yml health check `for i in 1 2 3 4 5` → `for i in $(seq 1 12)` (60초)

이 5개는 codex 미니 패치로 한 번에 처리 가능. A5 진행과 별개로 W0 막바지에 패치하면 됨.

### Step 7.2. main 푸시 → 첫 배포 시도

deploy.yml 패치 머지 후 main에 푸시 → Actions 탭에서 진행 관찰.

**기대 흐름**:
```
build-push (3~5분) → deploy (2~3분) → health check (10초)
```

성공하면:
```powershell
curl https://api.snail.app/api/v1/health
# {"status":"ok"} 응답
```

### Step 7.3. Cloudflare DNS 업데이트 (실 GCE IP로)

Step 2.2에서 placeholder로 둔 A 레코드를 진짜 GCE IP(Step 5.4에서 받은 값)로 교체.

```
A   api    34.64.XXX.XXX   DNS only (proxy OFF)
```

→ 1~5분 후 `https://api.snail.app` 정상 접근.

---

## 9. 마무리 검증 체크리스트

W0 완료 정의 = 다음 11개가 모두 OK:

- [ ] 사업자등록증 PDF 보유
- [ ] 통신판매업 신고증 PDF 보유
- [ ] 법무 검토 완료된 `legal/privacy_policy.md`, `legal/terms_of_service.md` GitHub Pages 공개
- [ ] GCP 프로젝트 + 예산 알림 설정됨
- [ ] OpenAI API 키 발급 + Hard limit $50
- [ ] Apple Developer 가입 승인 + App ID + Sign In Key + APNs Key
- [ ] 도메인 + Cloudflare DNS + Caddy HTTPS 정상
- [ ] 카카오 채널 + Bizppurio 가입 + **발신프로필 심사 통과**
- [ ] 알림톡 템플릿 7개 심사 통과 (또는 진행 중)
- [ ] GitHub Secrets 13개 모두 등록
- [ ] **`curl https://api.snail.app/api/v1/health`가 `{"status":"ok"}` 반환**

이 11개가 다 되면 **W1 시작 = A5 codex 작업 재개**해도 안전.

---

## 10. 자주 막히는 곳 (트러블슈팅)

### "Cloud SQL Auth Proxy 연결 안 됨"
- GCE 인스턴스 서비스 계정이 Cloud SQL Client 권한 있는지 확인
- 또는 `--private-ip` 빼고 public IP 사용 (단 비용·보안 ↓)

### "Caddy SSL 발급 실패"
- DNS A 레코드가 GCE IP로 정확히 가리키는지 (`dig api.snail.app +short`)
- Cloudflare proxy(주황 구름)가 **OFF (회색)** 인지 — Let's Encrypt가 직접 GCE 80포트 검증함
- GCE 방화벽 80/443 열려있는지

### "alembic upgrade head 실패"
- `cloudsql.enable_pgvector` 플래그 켰는지
- DATABASE_URL의 비밀번호 URL-encoding (`@`, `:` 같은 특수문자 escape)

### "OpenAI 호출 실패 — 429 / quota_exceeded"
- Tier 1 진입했는지 (결제 5분 후 자동)
- Hard limit 도달 안 했는지 → Settings → Limits에서 확인

### "카카오 알림톡 심사 거부"
- 문구에 광고성 단어 (할인/이벤트/혜택) 들어가면 거부
- 변수 `#{변수명}` 형식 정확히 지켰는지
- 정보성으로만 작성하고 재신청

### "GitHub Actions에서 SSH 접속 실패"
- Secret에 등록한 private key 전체(`-----BEGIN OPENSSH PRIVATE KEY-----` 포함, 마지막 빈 줄까지) 복사했는지
- GCE 인스턴스 메타데이터에 공개키 등록 → 사용자명 = 키 comment 부분 (`ssh-keygen -C`로 지정한 값)

---

## 11. 비용 예상 (월간, MVP 기준)

| 항목 | 비용 |
|---|---|
| GCE e2-small | $13~15 |
| Cloud SQL db-f1-micro 또는 N-1 | $9~25 |
| Cloud Storage (디자인 이미지 50GB) | $1 |
| GCR / Artifact Registry | $0~1 |
| 도메인 (1년 기준 월할) | $1~2 |
| Cloudflare | $0 (무료 플랜) |
| OpenAI (디자인 500개 × 분석) | $5~15 (1회 한정) + 운영 중 $5~20/월 |
| Apple Developer (월할) | $8.25 |
| 카카오 알림톡 (월 1000건) | $5~10 |
| Sentry (Free tier) | $0 |
| **합계 (MVP)** | **약 $45~95/월** |

> GCP $300 크레딧으로 3~6개월 운영 가능.

---

## 12. 도움 요청 시 빠른 자료 정리

내가(Claude) 막힐 때 다음 정보 한 번에 주면 진단 빠름:
- 어느 Step에서 막혔는지 (예: "Step 5.4 SSH 접속")
- 정확한 에러 메시지 전체 복붙
- `gcloud --version`, `docker --version`, `git status` 출력
- 어떤 명령을 어떤 디렉토리에서 실행했는지

---

## 13. 변경 이력

- 2026-05-28: 초안 작성. deploy.yml D1~D5 패치 항목 포함.
