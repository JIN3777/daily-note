# daily-note — 매일 시황 정리 노트

매일 장 마감 후 상한가/거래량 급증 종목과 관련 뉴스·공시를 정리하고, 거래량 폭증 후
급감하는 패턴을 스크리닝해서 `notes/YYYY-MM-DD.md`에 기록해주는 도구입니다.

## 왜 로컬에서 실행하나요?

KRX 시세, DART 공시, 뉴스 검색 모두 실시간 데이터가 필요합니다. 이 스크립트를
클라우드/샌드박스 환경이 아니라 **인터넷이 정상적으로 열려 있는 본인 PC**에서 실행해야
합니다 (사내망/방화벽 환경도 해당 사이트 접속이 막혀 있다면 동작하지 않습니다).

## 정리 기준

### 1. 상한가 / 거래량 1,000만주 이상 종목
- 당일 등락률이 +29.5% 이상(상한가) 이거나, 거래량이 1,000만주 이상인 종목
- 종목별로 최근 60거래일 캔들+거래량+이동평균선(5/20/60일) 차트, 상승 이유로 가장 근접해
  보이는 기사 1건(신뢰 언론사 우선 선정, 원문 링크), 공시(DART, 상세 링크 포함)를 함께 기록

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

뉴스는 Google News RSS를 사용하므로 별도 키 발급이 필요 없습니다.

## 사용법

```bash
# 특정일 노트 생성 (YYYYMMDD)
python scripts/run_daily.py --date 20260916

# 뉴스/공시 API 키 없이 시세 스크리닝만 먼저 해보고 싶을 때
python scripts/run_daily.py --date 20260916 --no-news --no-disclosures

# 섹션2 패턴 판정용 조회 기간(기본 35일) 조정 - 결과 범위가 아니라 계산용 범위입니다
python scripts/run_daily.py --date 20260916 --lookback-days 60
```

실행하면 `notes/2026-09-16.md`(마크다운)와 `notes/2026-09-16.html`(브라우저용)이 함께 생성되고,
`notes/index.html`(전체 목록 페이지)도 자동으로 갱신됩니다.

**결과 확인은 `notes/index.html`을 더블클릭해서 브라우저로 여세요.** 날짜별 카드 목록이 나오고,
클릭하면 그날의 종목/뉴스/공시가 정리된 페이지로 이동합니다.

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

## 자동 실행 + 항상 같은 주소에서 보기 (GitHub Actions + Pages)

로컬 PC를 안 켜놔도, 평일 16:30(KST)에 자동으로 노트를 생성하고 웹사이트로 게시하도록
설정할 수 있습니다. `.github/workflows/daily-note.yml`이 이미 포함되어 있고, 아래 설정만
GitHub 웹사이트에서 한 번 해주면 됩니다.

> GitHub Pages는 무료 플랜에서 **공개(public) 저장소**에서만 쓸 수 있습니다. 비공개를
> 유지하려면 GitHub Pro(유료)가 필요합니다.

1. **저장소 공개 전환**: 저장소 페이지 → Settings → 맨 아래 "Danger Zone" →
   "Change repository visibility" → Public
2. **Secrets 등록**: Settings → Secrets and variables → Actions → "New repository secret"에서
   아래 3개를 각각 등록 (`.env`에 넣었던 값과 동일)
   - `KRX_ID`
   - `KRX_PW`
   - `DART_API_KEY`
3. **워크플로 최초 1회 수동 실행**: 저장소 상단 "Actions" 탭 → 왼쪽 "Generate daily market
   note" → 오른쪽 "Run workflow" 버튼. 이 실행이 끝나면 `gh-pages` 브랜치가 자동으로 생깁니다.
4. **Pages 활성화**: Settings → Pages → Source를 "Deploy from a branch"로, Branch를
   `gh-pages` / `(root)`로 선택 → Save
5. 몇 분 후 `https://<깃허브아이디>.github.io/daily-note/` 에서 확인 가능합니다.

이후로는 평일 16:30(KST)마다 자동으로 그날 노트가 추가되고, 같은 주소에 계속 누적됩니다.
Actions 탭에서 실행 이력과 실패 여부를 확인할 수 있습니다.

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
  news_client.py                # Google News RSS 검색, 원문 링크 (키 불필요)
  chart_client.py                # 종목별 캔들+거래량 차트 생성 (mplfinance)
  limit_up_logic.py             # 섹션1 스크리닝 순수 로직 (테스트됨)
  pattern_logic.py              # 섹션2 스크리닝 순수 로직 (테스트됨)
  section1_limit_up_volume.py   # 섹션1 오케스트레이션
  section2_volume_pattern.py    # 섹션2 오케스트레이션
  build_note.py                 # JSON -> 마크다운(.md) + 브라우저용(.html) 노트
  build_index.py                # notes/index.html(전체 목록 페이지) 생성/갱신
  run_daily.py                  # 전체 실행 진입점
templates/daily-note-template.md  # 수기로 채울 때 참고할 빈 템플릿
notes/index.html                   # 날짜별 노트 목록 (더블클릭해서 열기)
notes/YYYY-MM-DD.md, .html         # 생성된 일일 노트 (마크다운 / 브라우저용)
tests/                             # 순수 로직 단위 테스트
```

## 다음에 업그레이드하면 좋을 것들

- 상한가/거래량 기준 종목 중 뉴스·공시가 전혀 없는 경우, 네이버 종목토론방·HTS 특징주
  코멘트 등 보조 소스를 추가로 붙이기
- 섹션2 결과를 차트 이미지(캔들+거래량+5일선)로 자동 캡처해서 노트에 첨부
- 종목별로 과거 유사 패턴(같은 스크리닝에 몇 번 더 걸렸는지) 이력을 함께 표시
- Slack/이메일로 매일 노트 요약 발송
