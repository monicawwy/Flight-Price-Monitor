from amadeus import Client, ResponseError
import os
import pandas as pd
from datetime import datetime, timedelta

# 從 GitHub Secrets 讀取 API credentials
amadeus = Client(
    client_id=os.environ.get('AMADEUS_API_KEY'),
    client_secret=os.environ.get('AMADEUS_API_SECRET')
)

def find_cheap_destinations(origin='HKG', departure_date=None, max_price=5000):
    """搵從香港出發嘅平機票目的地"""
    
    try:
        params = {
            'origin': origin,
            'maxPrice': max_price,
            'viewBy': 'DESTINATION'
        }
        
        if departure_date:
            params['departureDate'] = departure_date
        
        # 呼叫 Flight Inspiration Search API
        response = amadeus.shopping.flight_destinations.get(**params)
        return response.data
        
    except ResponseError as error:
        print(f"錯誤: {error}")
        return None

def save_results_to_csv(data, filename='cheap_flights.csv'):
    """將結果儲存到 CSV"""
    
    if not data:
        print("冇數據可以儲存")
        return None
    
    flights = []
    for flight in data:
        flights.append({
            'destination': flight.get('destination'),
            'departure_date': flight.get('departureDate'),
            'return_date': flight.get('returnDate'),
            'price': flight.get('price', {}).get('total'),
            'search_date': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
    
    df = pd.DataFrame(flights)
    df = df.sort_values('price')
    
    # 儲存或附加到 CSV
    if os.path.exists(filename):
        df.to_csv(filename, mode='a', header=False, index=False)
    else:
        df.to_csv(filename, index=False)
    
    print(f"✓ 已儲存 {len(flights)} 個航班到 {filename}")
    
    # 顯示最平嘅 10 個
    print("\n=== 最抵機票 TOP 10 ===")
    top_10 = df.head(10)
    for idx, row in top_10.iterrows():
        print(f"{idx+1}. {row['destination']} - HKD ${row['price']} ({row['departure_date']})")
    
    return df

# 主程式
if __name__ == "__main__":
    print("🔍 開始搜尋從香港出發嘅平機票...")
    
    # 搜尋未來 7-180 日內嘅航班
    departure_date = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
    
    results = find_cheap_destinations(
        origin='HKG',
        departure_date=departure_date,
        max_price=3000  # 最多 $3000 港幣
    )
    
    if results:
        print(f"✓ 搵到 {len(results)} 個目的地！")
        save_results_to_csv(results)
    else:
        print("❌ 搵唔到結果")
