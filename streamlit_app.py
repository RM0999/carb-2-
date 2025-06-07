
import streamlit as st
import requests
from datetime import datetime

st.set_page_config(page_title="Crypto Arbitrage Scanner", layout="wide")

st.markdown("<h1 style='text-align: center;'>🔁 Multi-Crypto Arbitrage Scanner</h1>", unsafe_allow_html=True)

USD_TO_AUD = 1.52
EXCHANGES = ["Binance", "Kraken", "CoinSpot", "IndependentReserve"]
CRYPTO_CHOICES = {
    "BTC": {
        "symbol_binance": "BTCUSDT",
        "symbol_kraken": "XBTUSDT",
        "symbol_coinspot": "BTC",
        "symbol_ir": "Xbt",
    },
    "ETH": {
        "symbol_binance": "ETHUSDT",
        "symbol_kraken": "ETHUSDT",
        "symbol_coinspot": "ETH",
        "symbol_ir": "Eth",
    },
    "BNB": {
        "symbol_binance": "BNBUSDT",
        "symbol_kraken": None,
        "symbol_coinspot": "BNB",
        "symbol_ir": None,
    },
    "SOL": {
        "symbol_binance": "SOLUSDT",
        "symbol_kraken": None,
        "symbol_coinspot": "SOL",
        "symbol_ir": None,
    },
    "XRP": {
        "symbol_binance": "XRPUSDT",
        "symbol_kraken": "XRPUSDT",
        "symbol_coinspot": "XRP",
        "symbol_ir": "Xrp",
    }
}

# Sidebar controls
with st.sidebar:
    st.title("⚙️ Settings")
    crypto = st.selectbox("Select Crypto", list(CRYPTO_CHOICES.keys()))
    min_profit = st.slider("Minimum Net Profit (%)", 0.5, 10.0, 2.0)
    investment = st.number_input("Investment (AUD)", min_value=10, value=1000)
    selected_exchanges = st.multiselect("Exchanges", EXCHANGES, default=EXCHANGES)

# API functions
def fetch_binance(symbol):
    try:
        url = f"https://api.binance.com/api/v3/ticker/bookTicker?symbol={symbol}"
        r = requests.get(url).json()
        return {'buy': float(r['askPrice']) * USD_TO_AUD, 'sell': float(r['bidPrice']) * USD_TO_AUD, 'fee': 0.001}
    except:
        return None

def fetch_kraken(symbol):
    try:
        url = f"https://api.kraken.com/0/public/Ticker?pair={symbol}"
        r = requests.get(url).json()
        kraken_data = next(iter(r["result"].values()))
        return {'buy': float(kraken_data["a"][0]) * USD_TO_AUD, 'sell': float(kraken_data["b"][0]) * USD_TO_AUD, 'fee': 0.0026}
    except:
        return None

def fetch_coinspot(symbol):
    try:
        r = requests.get("https://www.coinspot.com.au/pubapi/v2/latest").json()
        ask = float(r['prices'][symbol]['ask'])
        bid = float(r['prices'][symbol]['bid'])
        return {'buy': ask, 'sell': bid, 'fee': 0.01}
    except:
        return None

def fetch_independent_reserve(symbol):
    try:
        url = f"https://api.independentreserve.com/Public/GetMarketSummary?primaryCurrencyCode={symbol}&secondaryCurrencyCode=Aud"
        r = requests.get(url).json()
        ask = float(r['CurrentLowestOfferPrice'])
        bid = float(r['CurrentHighestBidPrice'])
        return {'buy': ask, 'sell': bid, 'fee': 0.005}
    except:
        return None

# Mapping exchange to function and crypto symbol
fetchers = {
    "Binance": lambda sym: fetch_binance(CRYPTO_CHOICES[crypto]["symbol_binance"]) if CRYPTO_CHOICES[crypto]["symbol_binance"] else None,
    "Kraken": lambda sym: fetch_kraken(CRYPTO_CHOICES[crypto]["symbol_kraken"]) if CRYPTO_CHOICES[crypto]["symbol_kraken"] else None,
    "CoinSpot": lambda sym: fetch_coinspot(CRYPTO_CHOICES[crypto]["symbol_coinspot"]) if CRYPTO_CHOICES[crypto]["symbol_coinspot"] else None,
    "IndependentReserve": lambda sym: fetch_independent_reserve(CRYPTO_CHOICES[crypto]["symbol_ir"]) if CRYPTO_CHOICES[crypto]["symbol_ir"] else None,
}

# Fetch and filter data
exchange_data = {ex: fetchers[ex](crypto) for ex in selected_exchanges}
valid_data = {ex: val for ex, val in exchange_data.items() if val}

# Display logic
if valid_data:
    best_buy = min(valid_data.items(), key=lambda x: x[1]['buy'])
    best_sell = max(valid_data.items(), key=lambda x: x[1]['sell'])
    gross_pct = round((best_sell[1]['sell'] - best_buy[1]['buy']) / best_buy[1]['buy'] * 100, 2)
    total_fees_pct = round((best_buy[1]['fee'] + best_sell[1]['fee']) * 100, 2)
    net_pct = round(gross_pct - total_fees_pct, 2)
    profit_aud = round(investment * (net_pct / 100), 2)
    timestamp = datetime.now().strftime("%H:%M:%S")

    if net_pct >= min_profit:
        st.success(f"🚀 {crypto}/AUD Arbitrage Opportunity Found! {timestamp}")
        st.write(f"Buy on **{best_buy[0]}** at **AUD ${best_buy[1]['buy']:.2f}** (Fee: {best_buy[1]['fee']*100:.2f}%)")
        st.write(f"Sell on **{best_sell[0]}** at **AUD ${best_sell[1]['sell']:.2f}** (Fee: {best_sell[1]['fee']*100:.2f}%)")
        st.write(f"**Spread: {gross_pct}%** | **Net Profit: {net_pct}%** | **Profit: AUD ${profit_aud}**")
    else:
        st.warning(f"No arbitrage opportunity above {min_profit}% net for {crypto} right now.")
else:
    st.error(f"No valid data for {crypto} from selected exchanges.")
