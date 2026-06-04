# Streamlit 설정 가이드

## 파일 구조

```
.streamlit/
├── secrets.toml      # 민감한 정보 (API 키, URL 등)
├── config.toml       # Streamlit 애플리케이션 설정
└── README.md         # 이 파일
```

## secrets.toml - 환경변수 설정

Supabase와 연결하기 위한 민감한 정보를 저장합니다.

### 구성 요소

#### supabase_url
- **설명**: Supabase 프로젝트의 API 엔드포인트
- **예시**: `https://ipwbhyigwgwprtqghrdo.supabase.co`
- **위치**: Supabase 대시보드 > Project Settings > API

#### supabase_key
- **설명**: Supabase의 익명(anon) API 키
- **예시**: `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...`
- **위치**: Supabase 대시보드 > Project Settings > API
- **권한**: 공개 데이터에 대한 읽기/쓰기 권한

### 형식

```toml
supabase_url = "YOUR_SUPABASE_URL"
supabase_key = "YOUR_SUPABASE_ANON_KEY"
```

## config.toml - Streamlit 설정

Streamlit 애플리케이션의 동작, 외관, 서버 설정을 정의합니다.

### 주요 섹션

#### [theme]
- 색상 및 폰트 설정
- 대시보드의 시각적 외관 커스터마이징

#### [server]
- `port`: 실행 포트 (기본값: 8501)
- `headless`: 헤드레스 모드 (기본값: false)
- `runOnSave`: 파일 저장 시 자동 재실행 (기본값: true)
- `enableCORS`: CORS 활성화 (기본값: true)

#### [logger]
- `level`: 로깅 수준 (info, debug, warning, error)

## 보안 주의사항

### ⚠️ 중요
- `.streamlit/secrets.toml`은 절대 버전 관리에 포함하면 안 됩니다
- `.gitignore`에 다음을 추가하세요:
  ```
  .streamlit/secrets.toml
  ```

### 권장 사항
1. **로컬 개발**: 위의 `secrets.toml` 파일 사용
2. **프로덕션 배포**: 
   - Streamlit Cloud: 웹 대시보드에서 환경변수 설정
   - 기타 호스팅: 환경변수로 설정

## Streamlit에서 값 읽기

```python
import streamlit as st

# secrets.toml에서 읽기
supabase_url = st.secrets.get("supabase_url")
supabase_key = st.secrets.get("supabase_key")
```

## Supabase 자격증명 얻는 방법

1. [Supabase 대시보드](https://app.supabase.com) 접속
2. 프로젝트 선택
3. **Settings** > **API** 클릭
4. 다음 정보 복사:
   - **Project URL**: `supabase_url`로 사용
   - **anon public key**: `supabase_key`로 사용

## 트러블슈팅

### "⚠️ Supabase 자격증명이 필요합니다" 에러

**원인**: `secrets.toml`이 없거나 설정이 잘못됨

**해결책**:
1. `.streamlit/secrets.toml` 파일 존재 확인
2. `supabase_url`과 `supabase_key` 설정 확인
3. Streamlit 재시작

### CORS 오류

**원인**: Supabase에서 요청 거부

**확인사항**:
1. API 키가 유효한지 확인
2. Supabase RLS(Row Level Security) 정책 확인
3. 요청하는 테이블의 권한 확인

## 추가 설정

필요에 따라 다음을 추가할 수 있습니다:

```toml
# 데이터베이스 설정
[database]
cache_ttl = 60  # 캐시 시간 (초)

# API 설정
[api]
timeout = 30    # 타임아웃 (초)
max_retries = 3 # 최대 재시도 횟수
```

## 참고 자료

- [Streamlit 문서](https://docs.streamlit.io/)
- [Streamlit Secrets 관리](https://docs.streamlit.io/streamlit-community-cloud/deploy-your-app/secrets-management)
- [Supabase 문서](https://supabase.com/docs)
