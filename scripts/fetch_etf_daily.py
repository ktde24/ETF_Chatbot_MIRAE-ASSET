# scripts/fetch_etf_daily.py
import requests
import xml.etree.ElementTree as ET
from datetime import datetime
import pandas as pd
import os

service_key = "여기에_본인_API_KEY_입력"
today = datetime.today().strftime("%Y%m%d")
url = "http://apis.data.go.kr/1160100/service/GetSecuritiesProductInfoService/getETFPriceInfo"

params = {
    "serviceKey": service_key,
    "numOfRows": "1000",
    "pageNo": "1",
    "resultType": "xml",
    "basDt": today
}

response = requests.get(url, params=params, timeout=10)
response.raise_for_status()

root = ET.fromstring(response.content)
items = root.findall(".//item")

all_data = []
for item in items:
    record = {elem.tag: elem.text for elem in item}
    all_data.append(record)

df = pd.DataFrame(all_data)
os.makedirs("data", exist_ok=True)
save_path = f"data/ETF_시세_데이터_{today}.csv"
df.to_csv(save_path, index=False, encoding='utf-8-sig')
print(f"CSV 저장 완료: {save_path}")
