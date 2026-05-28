# 단일 명령 통합 검증 — codex 에이전트가 환경 설정 시행착오 없이 한 줄로 실행
#
# Usage (backend 디렉토리에서):
#   .\scripts\check.ps1            # 정적 검사 + 마이그레이션 + 테스트 전부
#   .\scripts\check.ps1 -SkipDb    # DB 없이 정적 검사만 (ruff + mypy)
#   .\scripts\check.ps1 -Only ruff # 특정 단계만
#
# 자동 처리:
# - .venv 활성화 (PATH에 추가)
# - asyncpg SSL 우회 (Windows 한글 경로 문제)
# - 표준 환경변수 주입 (테스트용 기본값)

param(
    [switch]$SkipDb,
    [ValidateSet("ruff", "format", "mypy", "alembic", "pytest", "all")]
    [string]$Only = "all"
)

$ErrorActionPreference = "Stop"

Push-Location (Join-Path $PSScriptRoot "..")

try {
    # 1) venv 활성화 — codex가 ruff/mypy/alembic을 PATH로 못 찾는 문제 해결
    $venvScripts = Join-Path (Get-Location) ".venv\Scripts"
    if (-not (Test-Path $venvScripts)) {
        Write-Error ".venv가 없습니다. 먼저 다음을 실행: python -m venv .venv && .\.venv\Scripts\pip install -r requirements-dev.txt"
    }
    $env:PATH = "$venvScripts;$env:PATH"

    # 2) 표준 환경변수 — Windows 한글 경로 asyncpg SSL 우회 + 테스트용 기본값
    if (-not $env:ENV)          { $env:ENV          = "local" }
    if (-not $env:DATABASE_URL) { $env:DATABASE_URL = "postgresql+asyncpg://snail:snail@localhost:5432/snail?ssl=disable" }
    if (-not $env:REDIS_URL)    { $env:REDIS_URL    = "redis://localhost:6379/0" }
    if (-not $env:JWT_SECRET)   { $env:JWT_SECRET   = "dev-only-change-me-32-chars-minimum" }

    function Run-Step([string]$Name, [scriptblock]$Cmd) {
        if ($Only -ne "all" -and $Only -ne $Name) { return }
        Write-Host ""
        Write-Host "=== $Name ===" -ForegroundColor Cyan
        & $Cmd
        if ($LASTEXITCODE -ne 0) {
            Write-Error "$Name 실패 (exit $LASTEXITCODE)"
        }
    }

    Run-Step "ruff"   { ruff check . }
    Run-Step "format" { ruff format --check . }
    Run-Step "mypy"   { mypy app }

    if (-not $SkipDb) {
        Run-Step "alembic" { alembic upgrade head }
        Run-Step "pytest"  { pytest -q }
    }

    Write-Host ""
    Write-Host "OK - all checks passed" -ForegroundColor Green
}
finally {
    Pop-Location
}
