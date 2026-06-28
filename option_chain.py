# option_chain.py
# PabbleAI Solution - FnO Option Chain Analyzer
# ================================================

import requests
import pandas as pd
import time

def get_session():
    """NSE ke liye proper session banata hai"""
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "*/*",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Referer": "https://www.nseindia.com/option-chain",
        "X-Requested-With": "XMLHttpRequest",
        "Connection": "keep-alive",
    }
    
    session = requests.Session()
    session.headers.update(headers)
    
    try:
        # Step 1: Home page visit - cookies milenge
        print("🔄 NSE se connect ho raha hai...")
        session.get("https://www.nseindia.com", timeout=15)
        time.sleep(2)
        
        # Step 2: Option chain page visit
        session.get("https://www.nseindia.com/option-chain", timeout=15)
        time.sleep(1)
        
        print("✅ NSE se connected!")
        return session
        
    except Exception as e:
        print(f"❌ Connection error: {e}")
        return None


def get_option_chain(session, symbol="NIFTY"):
    """NSE se live Option Chain data fetch karta hai"""
    
    if symbol == "NIFTY":
        url = "https://www.nseindia.com/api/option-chain-indices?symbol=NIFTY"
    elif symbol == "BANKNIFTY":
        url = "https://www.nseindia.com/api/option-chain-indices?symbol=BANKNIFTY"
    elif symbol == "FINNIFTY":
        url = "https://www.nseindia.com/api/option-chain-indices?symbol=FINNIFTY"
    else:
        url = f"https://www.nseindia.com/api/option-chain-equities?symbol={symbol}"
    
    try:
        response = session.get(url, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ {symbol} data fetch ho gaya!")
            return data
        else:
            print(f"❌ Error: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ Data fetch error: {e}")
        return None

def calculate_pcr(data):
    """Put Call Ratio calculate karta hai"""
    
    if not data:
        return None
    
    try:
        records = data['filtered']['data']
        
        total_call_oi = 0
        total_put_oi = 0
        
        for record in records:
            if 'CE' in record:
                total_call_oi += record['CE'].get('openInterest', 0)
            if 'PE' in record:
                total_put_oi += record['PE'].get('openInterest', 0)
        
        if total_call_oi == 0:
            return 0
            
        pcr = total_put_oi / total_call_oi
        return round(pcr, 2)
        
    except Exception as e:
        print(f"❌ PCR calculation error: {e}")
        return None


def calculate_max_pain(data):
    """Max Pain calculate karta hai"""
    
    if not data:
        return None
    
    try:
        records = data['filtered']['data']
        pain_dict = {}
        
        for record in records:
            strike = record.get('strikePrice', 0)
            pain_dict[strike] = 0
            
            for r in records:
                s = r.get('strikePrice', 0)
                ce_oi = r.get('CE', {}).get('openInterest', 0)
                pe_oi = r.get('PE', {}).get('openInterest', 0)
                
                if strike > s:
                    pain_dict[strike] += ce_oi * (strike - s)
                if strike < s:
                    pain_dict[strike] += pe_oi * (s - strike)
        
        max_pain = min(pain_dict, key=pain_dict.get)
        return max_pain
        
    except Exception as e:
        print(f"❌ Max Pain calculation error: {e}")
        return None


def get_top_oi_strikes(data, top=5):
    """Sabse zyada OI wale strikes dhundta hai"""
    
    if not data:
        return None, None
    
    try:
        records = data['filtered']['data']
        
        ce_oi_list = []
        pe_oi_list = []
        
        for record in records:
            strike = record.get('strikePrice', 0)
            
            if 'CE' in record:
                ce_oi = record['CE'].get('openInterest', 0)
                ce_oi_list.append((strike, ce_oi))
                
            if 'PE' in record:
                pe_oi = record['PE'].get('openInterest', 0)
                pe_oi_list.append((strike, pe_oi))
        
        # Sort by OI
        ce_oi_list.sort(key=lambda x: x[1], reverse=True)
        pe_oi_list.sort(key=lambda x: x[1], reverse=True)
        
        top_ce = ce_oi_list[:top]
        top_pe = pe_oi_list[:top]
        
        return top_ce, top_pe
        
    except Exception as e:
        print(f"❌ OI calculation error: {e}")
        return None, None


def get_signal(pcr, current_price, max_pain):
    """PCR aur Max Pain ke basis pe trading signal deta hai"""
    
    if pcr is None:
        return "⚪ Data unavailable"
    
    signals = []
    
    # PCR Signal
    if pcr > 1.5:
        signals.append("🟢 PCR Bullish")
    elif pcr > 1.2:
        signals.append("🟡 PCR Slightly Bullish")
    elif pcr > 0.8:
        signals.append("🟡 PCR Neutral")
    elif pcr > 0.5:
        signals.append("🔴 PCR Slightly Bearish")
    else:
        signals.append("🔴 PCR Bearish")
    
    # Max Pain Signal
    if max_pain and current_price:
        diff = current_price - max_pain
        if diff > 100:
            signals.append("⬇️ Price Max Pain se upar (Pull possible)")
        elif diff < -100:
            signals.append("⬆️ Price Max Pain se neeche (Push possible)")
        else:
            signals.append("➡️ Price Max Pain ke paas")
    
    return " | ".join(signals)


def get_summary(symbol="NIFTY"):
    """Poora summary return karta hai"""
    
    print("\n" + "="*50)
    print(f"🚀 PabbleAI Solution - Option Chain Analyzer")
    print("="*50)
    
    # Session banao
    session = get_session()
    if not session:
        return None
    
    # Data fetch karo
    data = get_option_chain(session, symbol)
    if not data:
        print("❌ Data fetch nahi hua. NSE band ho sakta hai ya market hours check karo.")
        return None
    
    # Calculations
    pcr = calculate_pcr(data)
    max_pain = calculate_max_pain(data)
    current_price = data['records']['underlyingValue']
    expiry_dates = data['records']['expiryDates']
    nearest_expiry = expiry_dates[0]
    
    # Top OI strikes
    top_ce, top_pe = get_top_oi_strikes(data, top=3)
    
    # Signal
    signal = get_signal(pcr, current_price, max_pain)
    
    summary = {
        "symbol": symbol,
        "current_price": current_price,
        "pcr": pcr,
        "max_pain": max_pain,
        "nearest_expiry": nearest_expiry,
        "signal": signal,
        "top_ce_strikes": top_ce,
        "top_pe_strikes": top_pe,
        "all_expiries": expiry_dates[:4]
    }
    
    return summary


def print_summary(summary):
    """Summary ko nicely print karta hai"""
    
    if not summary:
        return
    
    print("\n" + "="*50)
    print(f"📊 {summary['symbol']} OPTION CHAIN ANALYSIS")
    print("="*50)
    print(f"💰 Current Price  : {summary['current_price']}")
    print(f"📈 PCR            : {summary['pcr']}")
    print(f"🎯 Max Pain       : {summary['max_pain']}")
    print(f"📅 Nearest Expiry : {summary['nearest_expiry']}")
    print(f"\n🚦 SIGNAL: {summary['signal']}")
    
    print("\n📌 Top CE OI Strikes (Resistance):")
    if summary['top_ce_strikes']:
        for strike, oi in summary['top_ce_strikes']:
            print(f"   Strike: {strike} | OI: {oi:,}")
    
    print("\n📌 Top PE OI Strikes (Support):")
    if summary['top_pe_strikes']:
        for strike, oi in summary['top_pe_strikes']:
            print(f"   Strike: {strike} | OI: {oi:,}")
    
    print("\n📅 Upcoming Expiries:")
    for exp in summary['all_expiries']:
        print(f"   {exp}")
    
    print("="*50)
    print("💡 Powered by PabbleAI Solution")
    print("="*50 + "\n")


# ================================================
# MAIN - Yahan se program shuru hota hai
# ================================================

if __name__ == "__main__":
    
    print("\nKaunsa symbol analyze karna hai?")
    print("1. NIFTY")
    print("2. BANKNIFTY") 
    print("3. FINNIFTY")
    
    choice = input("\nChoice enter karo (1/2/3) ya symbol likho: ").strip()
    
    if choice == "1" or choice.upper() == "NIFTY":
        symbol = "NIFTY"
    elif choice == "2" or choice.upper() == "BANKNIFTY":
        symbol = "BANKNIFTY"
    elif choice == "3" or choice.upper() == "FINNIFTY":
        symbol = "FINNIFTY"
    else:
        symbol = choice.upper()
    
    summary = get_summary(symbol)
    print_summary(summary)