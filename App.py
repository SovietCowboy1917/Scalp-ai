import streamlit as st
import pandas as pd
import numpy as np
import requests
import talib
from datetime import datetime

st.set_page_config(page_title="IA Scalp Trading", layout="wide")

@st.cache(ttl=60)
def fetch_klines(symbol='BTCUSDT', interval='1m', limit=500):
    url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}"
    data = requests.get(url).json()
    df = pd.DataFrame(data, columns=[
        "open_time","open","high","low","close","volume","close_time",
        "quote_asset_volume","number_of_trades","taker_buy_base","taker_buy_quote","ignore"
    ])
    df['open_time'] = pd.to_datetime(df['open_time'], unit='ms')
    df.set_index('open_time', inplace=True)
    df = df.astype(float)
    return df[['open','high','low','close','volume']]

def add_indicators(df):
    df['ema9'] = talib.EMA(df['close'], timeperiod=9)
    df['ema20'] = talib.EMA(df['close'], timeperiod=20)
    df['rsi'] = talib.RSI(df['close'], timeperiod=14)
    macd, macdsignal, _ = talib.MACD(df['close'])
    df['macd'] = macd
    df['macdsignal'] = macdsignal
    upper, middle, lower = talib.BBANDS(df['close'], timeperiod=20)
    df['bb_upper'] = upper
    df['bb_middle'] = middle
    df['bb_lower'] = lower
    return df

def generate_signal(df):
    """Gera sinal simples baseado em EMA crossover e RSI"""
    if len(df) < 20:
        return None, "Dados insuficientes"
    last = df.iloc[-1]
    prev = df.iloc[-2]

    signal = None
    reason = ""

    # Exemplo básico: Compra se EMA9 cruzar EMA20 de baixo para cima e RSI < 70
    if prev['ema9'] < prev['ema20'] and last['ema9'] > last['ema20'] and last['rsi'] < 70:
        signal = "BUY"
        reason = "Cruzamento de EMA9 > EMA20 e RSI abaixo de 70"
    # Venda se EMA9 cruzar EMA20 de cima para baixo e RSI > 30
    elif prev['ema9'] > prev['ema20'] and last['ema9'] < last['ema20'] and last['rsi'] > 30:
        signal = "SELL"
        reason = "Cruzamento de EMA9 < EMA20 e RSI acima de 30"

    return signal, reason

def main():
    st.title("IA Scalp Trading - Cripto")

    symbol = st.sidebar.text_input("Símbolo (Binance)", value="BTCUSDT")
    interval = st.sidebar.selectbox("Intervalo", options=["1m", "3m", "5m", "15m"], index=0)
    limit = st.sidebar.slider("Quantidade de candles", 100, 1000, 500, 100)

    df = fetch_klines(symbol, interval, limit)
    df = add_indicators(df)

    st.subheader(f"Últimos dados para {symbol} - Intervalo {interval}")
    st.line_chart(df[['close', 'ema9', 'ema20']])

    signal, reason = generate_signal(df)

    if signal:
        st.success(f"SINAL GERADO: {signal}")
        st.info(f"Motivo: {reason}")
    else:
        st.warning("Nenhum sinal gerado no momento.")

    st.subheader("Indicadores Técnicos")
    st.dataframe(df.tail(10))

if __name__ == "__main__":
    main()
