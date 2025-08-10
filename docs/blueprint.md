# Albion Beacon — Project Blueprint  
**Version:** v3.2.1  
**Date:** 2025-08-10  

---

## 0) Snapshot
- **OS/Runtime**: Windows 10/11, Python 3.10, **Npcap 필수**
- **Packaging**: PyInstaller (`AlbionBeacon.spec` 존재)
- **Repo markers**: `settings.json`, `src/`, `tools/`, `releases/`
- **Versioning**: `VERSION`(예: `v3.2.1`) — 수동 증가, 릴리즈는 Draft/Pre-release 유지
- **Workflows 상태**: CI/Release = 수동 실행(보류), Lint & Autofix/Watch/Health = 활성

---

## 1) 목적(Goals) & 비범위(Non-Goals)
**Goals**
1) Albion UDP 트래픽 캡처 → **지역/파티 규모 등 핵심 이벤트 자동 추출**
2) **실시간 위치 공유**(선택적 업로드) & 맵 기반 **근접 매칭 보조**
3) **간편한 사용 경험**: 인터페이스 자동 감지, Npcap 미설치 시 친절 안내, 원클릭 실행

**Non-Goals**
- 게임 클라이언트 메모리 조작, 패킷 인젝션 등 **ToS 위반 요소 일체 제외**
- 공공 대규모 상용 배포 전까지 **배포 자동화 최소화**

---

## 2) 최종 산출물(Deliverables)
1) **Windows .exe** (PyInstaller 원파일)
2) **내부 API 서버**(단순 인증/위치 집계, SQLite)
3) **사용자 가이드**(설치·설정·문제해결)
4) **테스트 리소스**(샘플 PCAP, 단위/통합 테스트)

---

## 3) 시스템 구조(High-level)
- **Client (PyQt5)**
  - `env_guard`: Npcap 확인(레지스트리/DLL), `ensure_npcap()` 예외
  - `network_listener`: scapy 캡처 스레드 + Stop 이벤트 + 예외 격리
  - `parser`: Raw→ParsedEvent(region, ts, session, group_size)
  - `api_client`: 서버 업로드(재시도/백오프)
  - `offline_analyzer`: PCAP 파일 로드→파싱만 수행(테스트/디버깅)

- **Server (Flask)**
  - `POST /loc`: {user, zone, group_size, ts}
  - `GET /nearby?zone=…`: 인접/규모 기준 목록
  - DB: SQLite (유저/길드/최근 위치 테이블)

- **Config**
  - `settings.json`: UI/네트워크 기본값(민감값 제외)
  - `.env`: 서버 엔드포인트 등 비민감 런타임 값
  - `config/settings.py`: pydantic-settings로 통합 로딩

---

## 4) 데이터 흐름(Data Flow)
1) **Live Capture**  
   Adapter auto-detect → UDP 5055 필터 → Packet buffer → `parser` → GUI 표시 + (선택) 서버 업로드
2) **Offline Analyze**  
   파일 선택(PCAP) → Batch 파싱 → 요약/내보내기(JSON/CSV)
3) **Server**  
   수신 → upsert(사용자별 최근 위치) → 근접/규모 필터 조회

---

## 5) 모듈 설계(파일 레벨, 제안)
src/
core/
env_guard.py # has_npcap(), ensure_npcap(), @requires_npcap
network_listener.py # start/stop, thread, queue, retries
parser.py # parse(raw)->ParsedEvent
map_logic.py # zone graph, distance
client/
gui.py # signals/slots, toggle capture, log pane
api_client.py # POST /loc, GET /nearby
main.py # entrypoint
server/
run_server.py # Flask app
database.py # models/tables
config/
settings.py # pydantic-settings loader

---

## 6) 동작/품질 기준(Acceptance Criteria)
**Capture**
- Npcap 미설치 시 실행 차단 + 설치 안내 메시지
- 캡처 시작/중지 100% 안정(Stop 이벤트로 즉시 종료)
- 예외 발생 시 UI 로그에 즉시 표시, 프로세스는 생존

**Parser**
- 샘플 PCAP 3~5개로 **예상 이벤트**가 JSON 스냅샷과 **완전 일치**
- 처리 속도: PCAP 10MB를 3초 이내 파싱(오프라인)

**Server**
- `POST /loc` 평균 응답 < 150ms(로컬), 5xx 없음
- `GET /nearby` 응답에 zone/거리/그룹 인원 포함

**Build**
- PyInstaller onefile 생성 성공, 실행 즉시 GUI 표시 < 2초
- `settings.json` 없이도 기본값으로 정상 기동

**Docs**
- Quick Start, 문제 해결(Npcap, 드라이버 권한, 방화벽), 퍼머링크 사용법 수록

---

## 7) 환경 요구(Prereqs)
- Npcap (WinPcap API compatible) — 설치 필수
- 관리자 권한 필요할 수 있음(인터페이스 열람/바인딩)
- Windows Defender/방화벽 예외(필요 시 안내)

---

## 8) 워크플로우 정책
- **배포 보류**: Release/CI 자동 트리거 비활성(수동 실행만)
- **품질 유지**: Lint & Autofix(ruff) 유지, Watchers(가이드라인/블루프린트) 유지, Repo Health 주간 리포트
- **브랜치 전략**: `main`(안정)/`dev`(통합)/`feature/*`

---

## 9) 보안/개인정보
- 위치 데이터는 **옵트인** 전송, 최소한의 식별자만 저장
- 토큰/키는 Secrets로만, 코드 내 하드코딩 금지

---

## 10) 로드맵(4주 기준, 예시)
**W1 — 안정화 기반**
- `core/env_guard.py` 도입, GUI 예외 팝업 연결
- `network_listener` 스레드/Stop/retry/exception-queue
- pytest 마커(`requires_npcap`) 도입, CI 스킵

**W2 — 파서 & 테스트**
- `parser.py` 스켈레톤 + PCAP 샘플/골든 스냅샷
- `offline_analyzer`(CLI/GUI 메뉴) 1차

**W3 — 서버 & 거리**
- `run_server.py` 간단한 API
- `map_logic.py` 재도입(거리/인접 zone)

**W4 — 빌드 & UX**
- PyInstaller spec 정비(onefile, 아이콘/리소스)
- Quick Start/문제 해결 문서 업데이트

---

## 11) 작업 체크리스트(Next actions)
- [ ] `core/env_guard.py` 추가 → `network_listener`/GUI 연결
- [ ] `parser.py` 생성 → 샘플 PCAP + 테스트 통과
- [ ] `settings.sample.json` 추가(+ README 가이드)
- [ ] `AlbionBeacon.spec` 검토: onefile/add-data/icon/UPX 옵션 조정
- [ ] `docs/PROJECT_GUIDELINES.md` / `docs/blueprint.md` 저장소 관리 + Watchers 유지

