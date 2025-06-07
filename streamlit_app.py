
import streamlit as st
import requests
from datetime import datetime

USD_TO_AUD = 1.52

st.set_page_config(page_title="Crypto Arbitrage Scanner", layout="wide")
st.title("🔍 Crypto Arbitrage Scanner (Live)")

# Sidebar
with st.sidebar:
    st.title("⚙️ Settings")
    pair = st.selectbox("Trading Pair", ["BTC/USDT", "ETH/USDT", "BNB/USDT", "SOL/USDT", "XRP/USDT"])
    min_profit = st.slider("Minimum Profit (%)", 0.5, 10.0, 2.0)
    investment = st.number_input("Investment (AUD)", min_value=10, value=1000)
    exchanges = st.multiselect("Exchanges", [
        "Binance", "Kraken", "CoinSpot", "IndependentReserve",
        "Bybit", "Crypto.com", "KuCoin", "OKX", "Bitget"
    ], default=["Binance", "CoinSpot", "IndependentReserve", "Kraken"])

# API fetchers
def fetch_binance(symbol):  # symbol: BTCUSDT
    r = requests.get(f"https://api.binance.com/api/v3/ticker/bookTicker?symbol={symbol}").json()
    return {'buy': float(r['askPrice']) * USD_TO_AUD, 'sell': float(r['bidPrice']) * USD_TO_AUD, 'fee': 0.001}

def fetch_kraken(symbol):
    symbol_map = {"BTCUSDT": "XXBTZUSD", "ETHUSDT": "XETHZUSD", "BNBUSDT": "XBNZUSD", "SOLUSDT": "SOLUSD", "XRPUSDT": "XXRPZUSD"}
    key = symbol_map.get(symbol, "XXBTZUSD")
    r = requests.get(f"https://api.kraken.com/0/public/Ticker?pair={symbol}").json()
    data = r["result"][key]
    return {'buy': float(data["a"][0]) * USD_TO_AUD, 'sell': float(data["b"][0]) * USD_TO_AUD, 'fee': 0.0026}

def fetch_coinspot(symbol):
    sym = symbol.split("USDT")[0]
    r = requests.get("https://www.coinspot.com.au/pubapi/v2/latest").json()
    data = r["prices"].get(sym, {})
    return {'buy': float(data.get('ask', 0)), 'sell': float(data.get('bid', 0)), 'fee': 0.01}

def fetch_independent(symbol):
    code = symbol.replace("USDT", "").capitalize()
    r = requests.get(f"https://api.independentreserve.com/Public/GetMarketSummary?primaryCurrencyCode={code}&secondaryCurrencyCode=Aud").json()
    return {'buy': float(r['CurrentLowestOfferPrice']), 'sell': float(r['CurrentHighestBidPrice']), 'fee': 0.005}

def fetch_bybit(symbol):
    r = requests.get(f"https://api.bybit.com/v2/public/tickers?symbol={symbol}").json()
    t = r['result'][0]
    return {'buy': float(t['ask_price']) * USD_TO_AUD, 'sell': float(t['bid_price']) * USD_TO_AUD, 'fee': 0.001}

def fetch_kucoin(symbol):
    r = requests.get(f"https://api.kucoin.com/api/v1/market/orderbook/level1?symbol={symbol.replace('/', '-')}" ).json()
    t = r['data']
    return {'buy': float(t['askPrice']) * USD_TO_AUD, 'sell': float(t['bidPrice']) * USD_TO_AUD, 'fee': 0.001}

def fetch_okx(symbol):
    r = requests.get(f"https://www.okx.com/api/v5/market/ticker?instId={symbol.replace('/', '-')}" ).json()
    t = r['data'][0]
    return {'buy': float(t['askPx']) * USD_TO_AUD, 'sell': float(t['bidPx']) * USD_TO_AUD, 'fee': 0.001}

def fetch_crypto(symbol):
    r = requests.get(f"https://api.crypto.com/v2/public/get-ticker?instrument_name={symbol.replace('/', '_')}").json()
    t = r['result']['data']
    return {'buy': float(t['a']) * USD_TO_AUD, 'sell': float(t['b']) * USD_TO_AUD, 'fee': 0.001}

fetchers = {
    "Binance": fetch_binance,
    "Kraken": fetch_kraken,
    "CoinSpot": fetch_coinspot,
    "IndependentReserve": fetch_independent,
    "Bybit": fetch_bybit,
    "Crypto.com": fetch_crypto,
    "KuCoin": fetch_kucoin,
    "OKX": fetch_okx,
    "Bitget": fetch_bybit
}

symbol = pair.replace("/", "")

prices = {}
for ex in exchanges:
    try:
        data = fetchers[ex](symbol)
        if data["buy"] > 0 and data["sell"] > 0:
            prices[ex] = data
    except:
        continue

if prices:
    best_buy = min(prices.items(), key=lambda x: x[1]["buy"])
    best_sell = max(prices.items(), key=lambda x: x[1]["sell"])
    spread = round(best_sell[1]["sell"] - best_buy[1]["buy"], 2)
    gross_pct = round((best_sell[1]["sell"] - best_buy[1]["buy"]) / best_buy[1]["buy"] * 100, 2)
    total_fees = round((best_buy[1]["fee"] + best_sell[1]["fee"]) * 100, 2)
    net_pct = round(gross_pct - total_fees, 2)
    profit = round(investment * (net_pct / 100), 2)
    st.subheader("📈 Arbitrage Opportunity")
    st.success(f"Buy from **{best_buy[0]}** at **AUD ${best_buy[1]['buy']:.2f}**")
    st.success(f"Sell to **{best_sell[0]}** at **AUD ${best_sell[1]['sell']:.2f}**")
    st.write(f"💹 Gross Spread: **{gross_pct}%** | Net Profit: **{net_pct}%**")
    st.write(f"💸 Estimated AUD Profit: **${profit}**")
else:
    st.warning("⚠️ No valid arbitrage opportunity found from selected exchanges.")
