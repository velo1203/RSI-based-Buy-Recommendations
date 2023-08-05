import pyupbit
from cachetools import cached, TTLCache
import pandas as pd

# 캐시 설정 (최대 100개 항목, 300초 동안 유효)
cache = TTLCache(maxsize=100, ttl=300)

# RSI(상대강도지수)계산 함수
def calculate_rsi(data, window=14):
    delta = data.diff()  # 각 일자별 종가의 차이를 계산하여 양수인 경우에는 gain, 음수인 경우에는 loss로 분류
    gain = (delta.where(delta > 0, 0)).fillna(0)  # gain: 양수인 경우 delta 값을 그대로 사용, 음수인 경우 0으로 채움
    loss = (-delta.where(delta < 0, 0)).fillna(0)  # loss: 음수인 경우 delta 값을 그대로 사용, 양수인 경우 0으로 채움

    avg_gain = gain.rolling(window=window, min_periods=1).mean()  # 이동평균을 활용하여 window 기간동안의 평균 gain 계산
    avg_loss = loss.rolling(window=window, min_periods=1).mean()  # 이동평균을 활용하여 window 기간동안의 평균 loss 계산

    rs = avg_gain / avg_loss  # RS (Relative Strength) 계산
    rsi = 100 - (100 / (1 + rs))  # RSI (Relative Strength Index) 계산

    return rsi

@cached(cache)  # 캐시 데코레이터를 활용하여 API 호출 결과를 캐시에 저장하여 중복 호출을 방지
def get_price(ticker, interval="day", count=30):
    try:
        df = pyupbit.get_ohlcv(ticker, interval=interval, count=count)  # OHLCV 데이터를 가져옴
        if df is not None:
            return df['close']  # 종가 정보만 반환
    except Exception as e:
        print(f"Error fetching price for {ticker}: {e}")

def get_all_tickers():
    return pyupbit.get_tickers(fiat="KRW")  # 한화 거래 시장의 모든 가상화폐의 티커를 가져옴

def get_buy_recommendations():
    recommendations = []  # 매수 추천 리스트 초기화
    for ticker in get_all_tickers():  # 모든 가상화폐 티커에 대해 반복
        prices = get_price(ticker, count=40)  # 해당 가상화폐의 최근 40일 동안의 종가 데이터를 가져옴 (count=40으로 설정)

        if prices is not None:
            current_price = prices.iloc[-1]  # 최근 종가 (가장 마지막 데이터)
            moving_average = prices.mean()  # 최근 40일 동안의 종가의 평균을 구함
            standard_deviation = prices.std()  # 최근 40일 동안의 종가의 표준 편차를 구함

            threshold_price = moving_average - standard_deviation * 0.4  # 평균에서 표준 편차의 40% 만큼 빼서 임계값을 설정

            rsi_values = calculate_rsi(prices, window=5)  # 최근 5일 동안의 RSI를 계산
            current_rsi = rsi_values.iloc[-1]  # 최근 RSI 값 (가장 마지막 데이터)

            # 조건 확인
            if current_price < threshold_price and current_rsi < 30:  # 현재 가격이 임계값보다 낮고, RSI가 30보다 낮으면 추천 리스트에 추가
                recommendations.append((ticker, current_price))

    return recommendations  # 매수 추천 리스트 반환

recommendations = get_buy_recommendations()  # 매수 추천 리스트를 받아옴
for ticker, buy_price in recommendations:  # 추천 리스트에서 티커와 매수 가격을 가져와 출력
    print(f"Buy {ticker} at {buy_price}")  # 매수 추천 정보 출력
