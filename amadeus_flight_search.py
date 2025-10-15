"""
香港機票價格監察器
自動搜尋從香港出發嘅平價機票
"""

from amadeus import Client, ResponseError
import os
import pandas as pd
from datetime import datetime, timedelta
import traceback

# 從 GitHub Secrets 讀取 API credentials
try:
    amadeus = Client(
        client_id=os.environ.get('AMADEUS_API_KEY'),
        client_secret=os.environ.get('AMADEUS_API_SECRET')
    )
    print("✓ Amadeus API 連接成功")
except Exception as e:
    print(f"❌ Amadeus API 連接失敗: {e}")
    exit(1)


def find_cheap_destinations(origin='HKG', departure_date=None, max_price=5000, duration=None):
    """
    搵從香港出發嘅平機票目的地
    
    參數:
    - origin: 出發地（預設係 HKG = 香港）
    - departure_date: 出發日期 (YYYY-MM-DD 格式)
    - max_price: 最高價格（港幣）
    - duration: 旅程日數（例如 7 表示住 7 日）
    
    返回:
    - 航班數據列表，或 None（如果出錯）
    """
    
    try:
        print(f"\n🔍 搜尋參數:")
        print(f"   出發地: {origin}")
        print(f"   出發日期: {departure_date if departure_date else '任何日期'}")
        print(f"   最高價格: HKD ${max_price}")
        print(f"   旅程日數: {duration if duration else '任何日數'}")
        
        # 設定搜尋參數
        params = {
            'origin': origin,
            'maxPrice': max_price,
            'viewBy': 'DESTINATION'
        }
        
        if departure_date:
            params['departureDate'] = departure_date
        
        if duration:
            params['duration'] = duration
        
        # 呼叫 Flight Inspiration Search API
        print("\n📡 正在連接 Amadeus API...")
        response = amadeus.shopping.flight_destinations.get(**params)
        
        print(f"✓ API 請求成功")
        return response.data
        
    except ResponseError as error:
        print(f"❌ API 錯誤: {error}")
        
        # 顯示更詳細嘅錯誤資訊
        if hasattr(error, 'response'):
            print(f"   狀態碼: {error.response.status_code}")
            print(f"   錯誤訊息: {error.response.body}")
        
        return None
    
    except Exception as e:
        print(f"❌ 未預期嘅錯誤: {e}")
        traceback.print_exc()
        return None


def search_cheapest_dates(origin='HKG', destination='TYO', departure_date=None):
    """
    搵去某個目的地嘅最平日期（進階功能）
    
    參數:
    - origin: 出發地（預設 HKG）
    - destination: 目的地 IATA code（例如 TYO = 東京）
    - departure_date: 出發日期（YYYY-MM-DD）
    
    返回:
    - 航班數據列表，或 None（如果出錯）
    """
    
    try:
        print(f"\n🔍 搜尋最平日期:")
        print(f"   {origin} → {destination}")
        
        params = {
            'origin': origin,
            'destination': destination
        }
        
        if departure_date:
            params['departureDate'] = departure_date
        
        response = amadeus.shopping.flight_dates.get(**params)
        print(f"✓ 搵到 {len(response.data)} 個日期選項")
        return response.data
        
    except ResponseError as error:
        print(f"❌ API 錯誤: {error}")
        return None


def save_results_to_csv(data, filename='cheap_flights.csv'):
    """
    將結果儲存到 CSV 檔案
    
    參數:
    - data: 航班數據列表
    - filename: CSV 檔案名稱
    
    返回:
    - pandas DataFrame 或 None
    """
    
    print(f"\n💾 儲存結果到 {filename}...")
    
    # 處理冇數據嘅情況
    if not data or len(data) == 0:
        print("⚠️  冇搵到航班數據，建立空記錄")
        
        # 建立一個空記錄（避免 git commit 錯誤）
        df = pd.DataFrame([{
            'destination': 'No data found',
            'departure_date': '',
            'return_date': '',
            'price': 0,
            'search_date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'note': 'Test environment or no results available'
        }])
        
        df.to_csv(filename, index=False)
        print(f"✓ 已建立空記錄檔案")
        return df
    
    # 處理正常數據
    try:
        flights = []
        
        for flight in data:
            flights.append({
                'destination': flight.get('destination', 'Unknown'),
                'departure_date': flight.get('departureDate', ''),
                'return_date': flight.get('returnDate', ''),
                'price': flight.get('price', {}).get('total', 0),
                'search_date': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
        
        df = pd.DataFrame(flights)
        
        # 按價格排序
        df = df.sort_values('price')
        
        # 決定係新建立定係附加到現有檔案
        if os.path.exists(filename):
            print(f"   檔案已存在，附加新數據...")
            df.to_csv(filename, mode='a', header=False, index=False)
        else:
            print(f"   建立新檔案...")
            df.to_csv(filename, index=False)
        
        print(f"✓ 成功儲存 {len(flights)} 個航班記錄")
        
        return df
        
    except Exception as e:
        print(f"❌ 儲存檔案時出錯: {e}")
        traceback.print_exc()
        return None


def analyze_and_display(df):
    """
    分析並顯示最抵嘅機票
    
    參數:
    - df: pandas DataFrame
    """
    
    if df is None or len(df) == 0:
        print("\n⚠️  冇數據可以顯示")
        return
    
    # 移除 "No data" 記錄
    df_valid = df[df['destination'] != 'No data found']
    
    if len(df_valid) == 0:
        print("\n⚠️  冇有效航班數據")
        return
    
    print("\n" + "="*70)
    print("🎉 最抵機票 TOP 10 🎉")
    print("="*70)
    
    top_10 = df_valid.head(10)
    
    for idx, row in enumerate(top_10.iterrows(), 1):
        row_data = row[1]
        print(f"\n{idx}. 目的地: {row_data['destination']}")
        print(f"   💰 價格: HKD ${row_data['price']:.2f}")
        print(f"   ✈️  出發: {row_data['departure_date']}")
        print(f"   🔙 返程: {row_data['return_date']}")
    
    print("\n" + "="*70)
    
    # 顯示統計資訊
    print(f"\n📊 統計:")
    print(f"   總共搵到: {len(df_valid)} 個目的地")
    print(f"   最平: HKD ${df_valid['price'].min():.2f}")
    print(f"   最貴: HKD ${df_valid['price'].max():.2f}")
    print(f"   平均: HKD ${df_valid['price'].mean():.2f}")


def main():
    """主程式"""
    
    print("="*70)
    print("🛫 香港機票價格監察器")
    print("="*70)
    print(f"⏰ 執行時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # ============================================
    # 🔧 你可以喺呢度修改搜尋參數
    # ============================================
    
    # 出發日期（7 日後出發，你可以改 days=7 為其他數字）
    days_from_now = 7
    departure_date = (datetime.now() + timedelta(days=days_from_now)).strftime("%Y-%m-%d")
    
    # 最高價格（港幣）
    max_price = 3000
    
    # 旅程日數（可選，留空表示任何日數）
    duration = None  # 例如: 7 表示住 7 日
    
    # CSV 檔案名稱
    output_file = 'cheap_flights.csv'
    
    # ============================================
    # 執行搜尋
    # ============================================
    
    try:
        # 搜尋從香港出發嘅平機票
        results = find_cheap_destinations(
            origin='HKG',
            departure_date=departure_date,
            max_price=max_price,
            duration=duration
        )
        
        # 處理結果
        if results:
            print(f"\n✓ 成功搵到 {len(results)} 個目的地！")
            df = save_results_to_csv(results, output_file)
            analyze_and_display(df)
        else:
            print("\n⚠️  搵唔到結果")
            print("   可能原因:")
            print("   1. 測試環境數據有限")
            print("   2. 搜尋條件太嚴格（試下提高 max_price）")
            print("   3. API 暫時冇呢個日期嘅數據")
            
            # 就算冇結果都建立檔案（避免 git 錯誤）
            save_results_to_csv([], output_file)
        
        print("\n" + "="*70)
        print("✓ 程式執行完畢")
        print("="*70)
        
    except Exception as e:
        print(f"\n❌ 程式執行失敗: {e}")
        traceback.print_exc()
        
        # 確保建立檔案（避免 GitHub Actions 錯誤）
        try:
            save_results_to_csv([], output_file)
        except:
            pass
        
        exit(1)


# 執行主程式
if __name__ == "__main__":
    main()

