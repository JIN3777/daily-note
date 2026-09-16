"""상한가 / 거래량 1,000만주 이상 종목 스크리닝 순수 로직 (네트워크 의존성 없음, 테스트 가능)."""
import pandas as pd

DEFAULT_LIMIT_UP_THRESHOLD_PCT = 29.5  # 등락률이 이 이상이면 상한가로 간주 (호가 반올림 고려)
DEFAULT_VOLUME_THRESHOLD = 10_000_000  # 거래량 1,000만주


def find_limit_up_and_high_volume(
    snapshot: pd.DataFrame,
    limit_up_threshold_pct: float = DEFAULT_LIMIT_UP_THRESHOLD_PCT,
    volume_threshold: int = DEFAULT_VOLUME_THRESHOLD,
) -> list[dict]:
    """당일 시세 스냅샷에서 상한가 또는 거래량 조건을 만족하는 종목을 찾는다."""
    if snapshot.empty:
        return []

    is_limit_up = snapshot["등락률"] >= limit_up_threshold_pct
    is_high_volume = snapshot["거래량"] >= volume_threshold
    matched = snapshot[is_limit_up | is_high_volume]

    results = []
    for ticker, row in matched.iterrows():
        results.append(
            {
                "ticker": ticker,
                "change_pct": round(float(row["등락률"]), 2),
                "volume": int(row["거래량"]),
                "close": float(row["종가"]),
                "is_limit_up": bool(row["등락률"] >= limit_up_threshold_pct),
                "is_high_volume": bool(row["거래량"] >= volume_threshold),
            }
        )
    results.sort(key=lambda r: r["change_pct"], reverse=True)
    return results
