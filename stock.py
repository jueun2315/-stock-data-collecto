import requests
from bs4 import BeautifulSoup
import pandas as pd
import time

def convert_to_won(value):
    try:
        # 쉼표 제거 후 숫자만 추출
        number = value.replace(',', '')
        if number == '-' or number == '':
            return '정보없음'
        
        # 숫자로 변환하여 억 단위를 원 단위로 변경 (1억 = 100,000,000원)
        won_value = float(number) * 100000000
        # 천 단위 쉼표 추가
        return format(int(won_value), ',')
    except:
        return value

def get_stock_info(code):
    try:
        # 기본 정보 (종목명, 주식수, 업종) 가져오기
        url = f'https://finance.naver.com/item/main.naver?code={code}'
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        stock_name = soup.select_one('div.wrap_company h2 a')
        stock_name = stock_name.text if stock_name else '정보없음'
        
        # 업종 정보 가져오기
        industry_info = soup.select_one('div.trade_compare > h4 > em')
        if industry_info:
            industry = industry_info.text.strip().split(' ')[1]
        else:
            industry = '업종없음'
        
        # 주식수 가져오기
        stock_shares = soup.select_one('table.tb_type1 td:contains("상장주식수")')
        if stock_shares:
            stock_shares = stock_shares.find_next_sibling('td').text.strip()
        else:
            stock_shares = '정보없음'

        # 전날 종가와 현재가격 가져오기
        url = f'https://finance.naver.com/item/sise.naver?code={code}'
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 전날 종가 가져오기
        prev_close = soup.select_one('#_prev_close')
        prev_close = prev_close.text.strip() if prev_close else '정보없음'
        
        # 현재가격 가져오기
        current_price = soup.select_one('#_nowVal')
        current_price = current_price.text.strip() if current_price else '정보없음'

        # 컨센서스 정보 가져오기
        table = soup.select_one('table.tb_type1.tb_num')
        if not table:
            return None

        rows = table.select('tr')
        profit_data = {}
        roe_data = {}
        per_data = {}
        debt_ratio_data = {}
        
        for row in rows:
            th = row.select_one('th')
            if not th:
                continue
                
            if '영업이익' in th.text:
                tds = row.select('td')
                if len(tds) >= 4:
                    profit_data['2025E'] = convert_to_won(tds[1].text.strip())
                    profit_data['2026E'] = convert_to_won(tds[2].text.strip())
                    profit_data['2027E'] = convert_to_won(tds[3].text.strip())
            
            if 'ROE' in th.text:
                tds = row.select('td')
                if len(tds) >= 4:
                    roe_data['2025E'] = tds[1].text.strip()
                    roe_data['2026E'] = tds[2].text.strip()
                    roe_data['2027E'] = tds[3].text.strip()
            
            if 'PER' in th.text:
                tds = row.select('td')
                if len(tds) >= 4:
                    per_data['2025E'] = tds[1].text.strip()
                    per_data['2026E'] = tds[2].text.strip()
                    per_data['2027E'] = tds[3].text.strip()
            
            if '순부채비율' in th.text:
                tds = row.select('td')
                if len(tds) >= 4:
                    debt_ratio_data['2025E'] = tds[1].text.strip()
                    debt_ratio_data['2026E'] = tds[2].text.strip()

        return {
            '업종': industry,
            '종목명': stock_name,
            '전날종가': prev_close,
            '현재가격': current_price,
            '주식수': stock_shares,
            '2025E 영업이익': profit_data.get('2025E', '정보없음'),
            '2025E ROE': roe_data.get('2025E', '정보없음'),
            '2025E PER': per_data.get('2025E', '정보없음'),
            '2025E 순부채비율': debt_ratio_data.get('2025E', '정보없음'),
            '2026E 영업이익': profit_data.get('2026E', '정보없음'),
            '2026E ROE': roe_data.get('2026E', '정보없음'),
            '2026E PER': per_data.get('2026E', '정보없음'),
            '2026E 순부채비율': debt_ratio_data.get('2026E', '정보없음'),
            '2027E 영업이익': profit_data.get('2027E', '정보없음'),
            '2027E ROE': roe_data.get('2027E', '정보없음'),
            '2027E PER': per_data.get('2027E', '정보없음')
        }
    
    except Exception as e:
        print(f"Error processing {code}: {str(e)}")
        return None

def main():
    # 종목 코드 리스트
    stock_codes = [
        '005930',  # 삼성전자
        '000660',  # SK하이닉스
        '207940',  # 삼성바이오로직스
        '005380',  # 현대차
        '005490',  # POSCO홀딩스
        '035420',  # NAVER
        '000270',  # 기아
        '051910',  # LG화학
        '006400',  # 삼성SDI
        '035720',  # 카카오
        '105560',  # KB금융
        '055550',  # 신한지주
        '373220',  # LG에너지솔루션
        '012330',  # 현대모비스
        '028260',  # 삼성물산
        '086790',  # 하나금융지주
        '066570',  # LG전자
        '003670',  # 포스코퓨처엠
        '323410',  # 카카오뱅크
        '316140',  # 우리금융지주
    ]

    data = []
    for code in stock_codes:
        stock_data = get_stock_info(code)
        if stock_data:
            data.append(stock_data)
        time.sleep(1)  # 1초 대기

    # DataFrame 생성 및 CSV 저장
    df = pd.DataFrame(data)
    df.to_csv('stock_consensus.csv', index=False, encoding='utf-8-sig')

if __name__ == "__main__":
    main() 