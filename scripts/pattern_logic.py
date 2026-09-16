"""거래량 폭증→급감 + 5일선 이격 스크리닝 순수 로직 (네트워크 의존성 없음, 테스트 가능)."""
import pandas as pd

DEFAULT_SPIKE_MIN = 5.0  # 전일 대비 500%
DEFAULT_SPIKE_MAX = 10.0  # 전일 대비 1000%
DEFAULT_CRASH_MAX_RATIO = 0.25  # 전일 대비 25% 이하
DEFAULT_CRASH_WINDOW_DAYS = 10  # 폭증일 이후 며칠 안에 급감을 찾을지
DEFAULT_MA5_TOLERANCE = 0.03  # 5일선 아래로 -3%까지 허용


def build_ticker_panel(snapshots: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """{날짜(YYYYMMDD): 시세 스냅샷} -> (티커, 날짜) 기준 롱 포맷 패널."""
    frames = []
    for date, snap in snapshots.items():
        if snap.empty:
            continue
        tmp = snap[["종가", "거래량"]].copy()
        tmp["날짜"] = date
        tmp["티커"] = tmp.index
        frames.append(tmp)
    if not frames:
        return pd.DataFrame(columns=["티커", "날짜", "종가", "거래량"])
    panel = pd.concat(frames, ignore_index=True)
    panel["날짜"] = pd.to_datetime(panel["날짜"], format="%Y%m%d")
    panel = panel.sort_values(["티커", "날짜"]).reset_index(drop=True)
    return panel


def find_volume_spike_crash_patterns(
    panel: pd.DataFrame,
    spike_min: float = DEFAULT_SPIKE_MIN,
    spike_max: float = DEFAULT_SPIKE_MAX,
    crash_max_ratio: float = DEFAULT_CRASH_MAX_RATIO,
    crash_window_days: int = DEFAULT_CRASH_WINDOW_DAYS,
    ma5_tolerance: float = DEFAULT_MA5_TOLERANCE,
) -> list[dict]:
    """조건을 만족하는 (폭증일, 급감일) 쌍을 종목별로 찾는다.

    - 폭증일: 거래량이 전일 대비 spike_min~spike_max 배
    - 급감일: 폭증일 이후 crash_window_days 거래일 이내에, 거래량이 전일 대비
      crash_max_ratio 이하로 급감한 날
    - 급감일 종가가 5일선 위이거나, 5일선 아래로 ma5_tolerance 이내인 경우만 채택
    """
    results = []
    for ticker, g in panel.groupby("티커", sort=False):
        g = g.sort_values("날짜").reset_index(drop=True)
        g["거래량_전일비"] = g["거래량"] / g["거래량"].shift(1)
        g["MA5"] = g["종가"].rolling(5).mean()

        used_crash_positions: set[int] = set()
        spike_positions = g.index[
            (g["거래량_전일비"] >= spike_min) & (g["거래량_전일비"] <= spike_max)
        ].tolist()

        for spike_pos in spike_positions:
            window_end = min(spike_pos + crash_window_days, len(g) - 1)
            crash_pos = None
            for pos in range(spike_pos + 1, window_end + 1):
                if pos in used_crash_positions:
                    continue
                ratio = g.loc[pos, "거래량_전일비"]
                if pd.notna(ratio) and ratio <= crash_max_ratio:
                    crash_pos = pos
                    break
            if crash_pos is None:
                continue

            ma5 = g.loc[crash_pos, "MA5"]
            close = g.loc[crash_pos, "종가"]
            if pd.isna(ma5):
                continue
            gap_pct = (close - ma5) / ma5 * 100
            if close < ma5 * (1 - ma5_tolerance):
                continue  # 5일선 아래로 -3% 초과 이탈 -> 제외

            used_crash_positions.add(crash_pos)
            results.append(
                {
                    "ticker": ticker,
                    "spike_date": g.loc[spike_pos, "날짜"].strftime("%Y-%m-%d"),
                    "spike_volume": int(g.loc[spike_pos, "거래량"]),
                    "spike_ratio_pct": round(g.loc[spike_pos, "거래량_전일비"] * 100, 1),
                    "crash_date": g.loc[crash_pos, "날짜"].strftime("%Y-%m-%d"),
                    "crash_volume": int(g.loc[crash_pos, "거래량"]),
                    "crash_ratio_pct": round(g.loc[crash_pos, "거래량_전일비"] * 100, 1),
                    "crash_close": float(close),
                    "crash_ma5": round(float(ma5), 2),
                    "ma5_gap_pct": round(float(gap_pct), 2),
                }
            )
    return results
