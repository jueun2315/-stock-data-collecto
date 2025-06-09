import requests
from bs4 import BeautifulSoup
import re
import csv
from datetime import datetime
import time

def clean_number(text):
    """숫자 문자열에서 쉼표를 제거하고 숫자만 추출"""
    if not text or text == "N/A":
        return text
    # 쉼표 제거 후 숫자만 추출
    number = re.sub(r'[^\d.-]', '', text)
    if number:
        # 문자열을 실수로 변환
        return str(int(float(number) * 10000))  # 억원 단위로 변환
    return "N/A"

def format_stock_code(code):
    """종목코드를 6자리로 포맷팅"""
    return str(code).zfill(6)

def get_stock_consensus(code):
    """
    네이버 금융에서 기업 실적 컨센서스 정보를 가져오는 함수
    :param code: 종목 코드 (예: '005930' for 삼성전자)
    :return: 컨센서스 정보를 담은 딕셔너리
    """
    code = format_stock_code(code)  # 종목코드 6자리로 통일
    print(f"\n[DEBUG] 종목 {code} 처리 시작 - {datetime.now()}")
    url = f"https://finance.naver.com/item/main.naver?code={code}"
    
    # 최대 3번 시도
    for attempt in range(3):
        try:
            print(f"[DEBUG] 시도 {attempt + 1}/3: {code} - {datetime.now()}")
            
            # 웹 페이지 가져오기
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.75 Safari/537.36'
            }
            print(f"[DEBUG] {code} - HTTP 요청 시작 - {datetime.now()}")
            # 타임아웃 설정 추가 (10초)
            response = requests.get(url, headers=headers, timeout=10)
            print(f"[DEBUG] {code} - HTTP 응답 받음 (상태 코드: {response.status_code}) - {datetime.now()}")
            
            response.encoding = 'euc-kr'
            
            # HTML 파싱
            print(f"[DEBUG] {code} - HTML 파싱 시작 - {datetime.now()}")
            soup = BeautifulSoup(response.text, 'html.parser')
            print(f"[DEBUG] {code} - HTML 파싱 완료 - {datetime.now()}")
            
            # 종목명
            stock_name = soup.select_one('div.wrap_company h2')
            if not stock_name:
                raise Exception("종목명을 찾을 수 없습니다")
            stock_name = stock_name.text.strip()
            print(f"[DEBUG] {code} - 종목명 찾음: {stock_name} - {datetime.now()}")
            
            # 컨센서스 테이블 찾기
            consensus_table = soup.select('div.cop_analysis table')
            if not consensus_table:
                raise Exception("컨센서스 테이블을 찾을 수 없습니다")
            print(f"[DEBUG] {code} - 컨센서스 테이블 찾음 - {datetime.now()}")
            
            # 연간 실적 컨센서스 찾기
            annual_data = {}
            rows = consensus_table[0].select('tr')
            found_profit_row = False
            
            print(f"[DEBUG] {code} - 영업이익 데이터 검색 시작 - {datetime.now()}")
            for row in rows:
                th = row.select_one('th')
                if th and '영업이익' in th.text:
                    found_profit_row = True
                    tds = row.select('td')
                    for i, td in enumerate(tds):
                        if td.text.strip():
                            year = 2023 + i  # 첫 번째 열이 2023년
                            # 2025년 이후 데이터만 저장
                            if year >= 2025:
                                value = clean_number(td.text)
                                annual_data[str(year)] = value
                                print(f"[DEBUG] {code} - {year}년 영업이익: {value} - {datetime.now()}")
            
            if not found_profit_row:
                raise Exception("영업이익 데이터를 찾을 수 없습니다")
            
            if not annual_data:
                raise Exception("2025년 이후 데이터가 없습니다")
            
            print(f"[DEBUG] {code} - 데이터 수집 성공 - {datetime.now()}")
            return {
                '종목코드': code,
                '종목명': stock_name,
                '연간 예상 영업이익': annual_data
            }
            
        except Exception as e:
            print(f"[ERROR] {code} - 에러 발생: {str(e)} - {datetime.now()}")
            if attempt < 2:  # 마지막 시도가 아니면 재시도
                print(f"[DEBUG] {code} - 3초 후 재시도 - {datetime.now()}")
                time.sleep(3)
            else:
                print(f"[ERROR] {code} - 최대 시도 횟수 초과 - {datetime.now()}")
                return None
    
    return None

def save_to_csv(stocks_data, filename):
    """
    주식 데이터를 CSV 파일로 저장
    """
    print(f"\n[DEBUG] CSV 저장 시작 - {datetime.now()}")
    
    if not stocks_data:
        print("[ERROR] 저장할 데이터가 없습니다")
        return
    
    try:
        # 헤더 생성 (연도 찾기)
        all_years = set()
        for stock in stocks_data:
            all_years.update(stock['연간 예상 영업이익'].keys())
        years = sorted(list(all_years))
        
        if not years:
            print("[ERROR] 연도 데이터가 없습니다")
            return
        
        print(f"[DEBUG] 찾은 연도: {years} - {datetime.now()}")
        
        # CSV 파일 작성
        with open(filename, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            
            # 헤더 작성
            header = ['종목코드', '종목명'] + [f'{year}년 예상영업이익(억원)' for year in years]
            writer.writerow(header)
            print(f"[DEBUG] CSV 헤더 작성 완료 - {datetime.now()}")
            
            # 데이터 작성
            for stock in stocks_data:
                row = [
                    format_stock_code(stock['종목코드']),  # 종목코드 6자리로 통일
                    stock['종목명']
                ]
                for year in years:
                    value = stock['연간 예상 영업이익'].get(str(year), 'N/A')
                    if value != 'N/A':
                        value = format(int(value), ',')  # 천단위 쉼표 추가
                    row.append(value)
                writer.writerow(row)
                print(f"[DEBUG] {stock['종목명']} 데이터 작성 완료 - {datetime.now()}")
        
        print(f"\n[SUCCESS] 데이터가 {filename} 파일로 저장되었습니다 - {datetime.now()}")
    
    except Exception as e:
        print(f"[ERROR] 파일 저장 중 에러 발생: {str(e)} - {datetime.now()}")

def main():
    """메인 함수"""
    start_time = datetime.now()
    print(f"\n[INFO] 데이터 수집 시작: {start_time}")
    
    # 관심 있는 종목 리스트
    stock_codes = [
        ('005930', '삼성전자'),
        ('000660', 'SK하이닉스'),
        ('373220', 'LG에너지솔루션'),
        ('005380', '현대차'),
        ('035420', '네이버'),
        ('035720', '카카오'),
        ('051910', 'LG화학'),
        ('005490', 'POSCO홀딩스'),
        ('000270', '기아'),
        ('207940', '삼성바이오로직스')
    ]
    
    print(f"[DEBUG] 처리할 종목 수: {len(stock_codes)}")
    
    # 데이터 수집
    stocks_data = []
    success_count = 0
    
    for code, name in stock_codes:
        print(f"\n[INFO] {name} ({code}) 처리 시작 - {datetime.now()}")
        data = get_stock_consensus(code)
        if data:
            stocks_data.append(data)
            success_count += 1
            print(f"[SUCCESS] {name} 처리 완료 - {datetime.now()}")
        else:
            print(f"[ERROR] {name} 처리 실패 - {datetime.now()}")
    
    print(f"\n[INFO] 총 {len(stock_codes)}개 종목 중 {success_count}개 성공")
    
    # CSV 파일로 저장
    if stocks_data:
        filename = 'stock_consensus.csv'
        save_to_csv(stocks_data, filename)
    else:
        print("\n[ERROR] 저장할 데이터가 없습니다")
    
    end_time = datetime.now()
    duration = end_time - start_time
    print(f"\n[INFO] 작업 완료: {end_time}")
    print(f"[INFO] 총 소요 시간: {duration}")

if __name__ == "__main__":
    main() 