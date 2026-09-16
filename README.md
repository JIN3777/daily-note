# daily-note — 매일 시황 정리 노트

매일 장 마감 후 상한가/거래량 급증 종목과 관련 뉴스·공시를 정리하고, 거래량 폭증 후
급감하는 패턴을 스크리닝해서 `notes/YYYY-MM-DD.md`에 기록해주는 도구입니다.

## 왜 로컬에서 실행하나요?

KRX 시세, DART 공시, 네이버 뉴스 검색 모두 실시간 데이터가 필요합니다. 이 스크립트를
클라우드/샌드박스 환경이 아니라 **인터넷이 정상적으로 열려 있는 본인 PC**에서 실행해야
합니다 (사내망/방화벽 환경도 해당 사이트 접속이 막혀 있다면 동작하지 않습니다).

## 정리 기준

### 1. 상한가 / 거래량 1,000만주 이상 종목
- 당일 등락률이 +29.5% 이상(상한가) 이거나, 거래량이 1,000만주 이상인 종목
- 종목별로 관련 뉴스(네이버 뉴스 검색, 원문 링크 포함)와 공시(DART, 상세 링크 포함)를 함께 기록

### 2. 거래량 폭증 → 급감 패턴 종목
- 어느 날 거래량이 전일 대비 500~1000%로 폭증
- 이후 며칠 내에 거래량이 전일 대비 25% 이하로 급감
- 급감한 날 종가가 5일 이동평균선 위이거나, 아래여도 -3% 이내인 종목만 채택
- 판정 자체는 과거 며칠치 데이터가 필요하지만(내부적으로만 사용), **결과는 항상
  `--date`로 지정한 당일이 급감일인 종목만** 노트에 표시됩니다. 과거 매치까지 전부 보고
  싶다면 `--all-window` 옵션을 사용하세요.

## 설치

```bash
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```

`.env`에 아래 키를 채워 넣습니다.

- `KRX_ID` / `KRX_PW`: https://data.krx.co.kr 무료 회원가입 후 그 아이디/비밀번호. **필수입니다** —
  pykrx가 시세를 조회하려면 KRX 로그인 세션이 있어야 하고, 없으면 모든 조회가
  `Expecting value: line 1 column 1 (char 0)` 에러로 실패합니다.
- `DART_API_KEY`: https://opendart.fss.or.kr (회원가입 후 즉시 발급, 무료)
- `NAVER_CLIENT_ID` / `NAVER_CLIENT_SECRET`: https://developers.naver.com/apps (애플리케이션 등록 → "검색" API 사용 설정, 무료)

## 사용법

```bash
# 특정일 노트 생성 (YYYYMMDD)
python scripts/run_daily.py --date 20260916

# 뉴스/공시 API 키 없이 시세 스크리닝만 먼저 해보고 싶을 때
python scripts/run_daily.py --date 20260916 --no-news --no-disclosures

# 섹션2 패턴 판정용 조회 기간(기본 35일) 조정 - 결과 범위가 아니라 계산용 범위입니다
python scripts/run_daily.py --date 20260916 --lookback-days 60
```

실행하면 `notes/2026-09-16.md`가 생성됩니다.

섹션별로 따로 실행해서 JSON으로 결과만 뽑아볼 수도 있습니다.

```bash
python scripts/section1_limit_up_volume.py --date 20260916 --out /tmp/s1.json
python scripts/section2_volume_pattern.py --date 20260916 --out /tmp/s2.json
python scripts/build_note.py --date 20260916 --section1 /tmp/s1.json --section2 /tmp/s2.json
```

## 매일 자동 실행하기

`cron`(macOS/Linux) 또는 작업 스케줄러(Windows)에 등록해서 장 마감 후(예: 16:00) 자동
실행하도록 만들 수 있습니다. 예시(매 평일 16:00, macOS/Linux):

```cron
0 16 * * 1-5 cd /path/to/daily-note && .venv/bin/python scripts/run_daily.py --date $(date +\%Y\%m\%d) >> logs/run.log 2>&1
```

## 테스트

핵심 스크리닝 로직(`limit_up_logic.py`, `pattern_logic.py`)은 네트워크 없이 단위 테스트로
검증됩니다.

```bash
pip install -r requirements-dev.txt
pytest tests/ -v
```

## 폴더 구조

```
scripts/
  config.py                    # .env 로드
  krx_data.py                  # pykrx 시세 조회
  dart_client.py                # DART 공시 API
  news_client.py                # 네이버 뉴스 검색 API
  limit_up_logic.py             # 섹션1 스크리닝 순수 로직 (테스트됨)
  pattern_logic.py              # 섹션2 스크리닝 순수 로직 (테스트됨)
  section1_limit_up_volume.py   # 섹션1 오케스트레이션
  section2_volume_pattern.py    # 섹션2 오케스트레이션
  build_note.py                 # JSON -> 마크다운 노트
  run_daily.py                  # 전체 실행 진입점
templates/daily-note-template.md  # 수기로 채울 때 참고할 빈 템플릿
notes/YYYY-MM-DD.md               # 생성된 일일 노트
tests/                             # 순수 로직 단위 테스트
```

## 다음에 업그레이드하면 좋을 것들

- 상한가/거래량 기준 종목 중 뉴스·공시가 전혀 없는 경우, 네이버 종목토론방·HTS 특징주
  코멘트 등 보조 소스를 추가로 붙이기
- 섹션2 결과를 차트 이미지(캔들+거래량+5일선)로 자동 캡처해서 노트에 첨부
- 종목별로 과거 유사 패턴(같은 스크리닝에 몇 번 더 걸렸는지) 이력을 함께 표시
- Slack/이메일로 매일 노트 요약 발송
