import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
from datetime import datetime

def convert_to_won(value):
    try:
        # 쉼표 제거 후 숫자만 추출
        number = value.replace(',', '')
        if number == '-' or number == '' or '정보없음' in number:
            return '0'  # 정보없음 대신 0으로 표시
        
        # 숫자로 변환하여 억 단위를 원 단위로 변경 (1억 = 100,000,000원)
        won_value = float(number) * 100000000
        # 천 단위 쉼표 추가
        return format(int(won_value), ',')
    except:
        return '0'  # 에러 발생시 0으로 표시

def get_stock_info(code):
    print(f"\n[{datetime.now()}] 처리 시작: {code}")
    try:
        # 기본 정보 (종목명, 주식수, 업종) 가져오기
        url = f'https://finance.naver.com/item/main.naver?code={code}'
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # HTTP 오류 체크
        soup = BeautifulSoup(response.text, 'html.parser')
        
        stock_name = soup.select_one('div.wrap_company h2 a')
        stock_name = stock_name.text if stock_name else '정보없음'
        print(f"종목명 추출: {stock_name}")
        
        # 업종 정보 가져오기
        industry_info = soup.select_one('div.trade_compare > h4 > em')
        if industry_info:
            industry = industry_info.text.strip().split(' ')[1]
        else:
            industry = '업종없음'
        print(f"업종 추출: {industry}")
        
        # 주식수 가져오기
        stock_shares = soup.select_one('table.tb_type1 td:contains("상장주식수")')
        if stock_shares:
            stock_shares = stock_shares.find_next_sibling('td').text.strip()
        else:
            stock_shares = '0'
        print(f"주식수 추출: {stock_shares}")

        # 전날 종가와 현재가격 가져오기
        url = f'https://finance.naver.com/item/sise.naver?code={code}'
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # HTTP 오류 체크
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 전날 종가 가져오기
        prev_close = soup.select_one('#_prev_close')
        prev_close = prev_close.text.strip() if prev_close else '0'
        print(f"전날 종가 추출: {prev_close}")
        
        # 현재가격 가져오기
        current_price = soup.select_one('#_nowVal')
        current_price = current_price.text.strip() if current_price else '0'
        print(f"현재가격 추출: {current_price}")

        # 컨센서스 정보 가져오기
        url = f'https://finance.naver.com/item/coinfo.naver?code={code}'  # coinfo 페이지로 변경
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 컨센서스 iframe 찾기
        consensus_iframe = soup.select_one('#coinfo_cp')
        if consensus_iframe:
            iframe_url = 'https://finance.naver.com' + consensus_iframe['src']
            response = requests.get(iframe_url, headers=headers)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
        
        table = soup.select_one('table.tb_type1.tb_num')
        if not table:
            print(f"경고: 컨센서스 테이블을 찾을 수 없음 ({code})")
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
                    print(f"영업이익 데이터 추출 완료")
            
            if 'ROE' in th.text:
                tds = row.select('td')
                if len(tds) >= 4:
                    roe_data['2025E'] = tds[1].text.strip() or '0'
                    roe_data['2026E'] = tds[2].text.strip() or '0'
                    roe_data['2027E'] = tds[3].text.strip() or '0'
                    print(f"ROE 데이터 추출 완료")
            
            if 'PER' in th.text:
                tds = row.select('td')
                if len(tds) >= 4:
                    per_data['2025E'] = tds[1].text.strip() or '0'
                    per_data['2026E'] = tds[2].text.strip() or '0'
                    per_data['2027E'] = tds[3].text.strip() or '0'
                    print(f"PER 데이터 추출 완료")
            
            if '순부채비율' in th.text:
                tds = row.select('td')
                if len(tds) >= 4:
                    debt_ratio_data['2025E'] = tds[1].text.strip() or '0'
                    debt_ratio_data['2026E'] = tds[2].text.strip() or '0'
                    print(f"순부채비율 데이터 추출 완료")

        result = {
            '업종': industry,
            '종목명': stock_name,
            '전날종가': prev_close,
            '현재가격': current_price,
            '주식수': stock_shares,
            '2025E 영업이익': profit_data.get('2025E', '0'),
            '2025E ROE': roe_data.get('2025E', '0'),
            '2025E PER': per_data.get('2025E', '0'),
            '2026E 영업이익': profit_data.get('2026E', '0'),
            '2026E ROE': roe_data.get('2026E', '0'),
            '2026E PER': per_data.get('2026E', '0'),
            '2027E 영업이익': profit_data.get('2027E', '0'),
            '2027E ROE': roe_data.get('2027E', '0'),
            '2027E PER': per_data.get('2027E', '0'),
            '2025E 순부채비율': debt_ratio_data.get('2025E', '0'),
            '2026E 순부채비율': debt_ratio_data.get('2026E', '0')
        }
        print(f"[{datetime.now()}] 처리 완료: {code}")
        return result
    
    except requests.RequestException as e:
        print(f"네트워크 오류 ({code}): {str(e)}")
        return None
    except Exception as e:
        print(f"처리 중 오류 발생 ({code}): {str(e)}")
        return None

def main():
    print(f"\n[{datetime.now()}] 데이터 수집 시작")
    
    # 종목 코드 리스트
    stock_codes = [
        '010140',  # 삼성중공업
        '189300',  # 인텔리안테크
        '000720',  # 현대건설
        '028260',  # 삼성물산
        '042660',  # 한화오션
        '010620',  # HD현대미포조선
        '314130',  # HD현대마린솔루션
        '000880',  # 한화
        '064350',  # 현대로템
        '329180',  # HD현대중공업
        '009540',  # HD한국조선해양
        '009830',  # 한화솔루션
        '000660',  # SK하이닉스
        '009835',  # 한화솔루션우
        '042000',  # 카페24
        '304100',  # 솔트룩스
        '030200',  # KT
        '034020',  # 두산에너빌리티
        '017040',  # 수산인더스트리
        '119850',  # 지앤씨에너지
        '047810',  # 한국항공우주
        '454910',  # 두산로보틱스
        '089030',  # 테크윙
        '322000',  # 현대에너지솔루션
        '042700',  # 한미반도체
        '039440',  # 에스티아이
        '031980',  # 피에스케이홀딩스
        '253450',  # 아스테라시스
        '251120',  # 에이직랜드
        '036580',  # 파미셀
        '174900',  # 엑스게이트
        '005930',  # 삼성전자
        '114820',  # 케이에스에스
        '046970',  # 우리로
        '242430',  # 비아이매트릭스
        '035420',  # 네이버
        '083650',  # 비에이치아이
        '161890',  # 한국콜마
        '218410',  # RFHIC
        '226320',  # 잇츠한불
        '009420',  # 한올바이오파마
        '007660',  # 이수페타시스
        '192820',  # 코스맥스
        '262260',  # 에이피알
        '950140',  # 잉글우드랩
        '090430',  # 아모레퍼시픽
        '225430',  # 제닉
        '041510',  # SM
        '417180',  # 핑거스토리
        '068330',  # 팬스타엔터프라이즈
        '318020',  # 포바이포
        '017800',  # 현대엘리베이터
        '054040',  # 한텍
        '108320',  # LG CNS
        '259630',  # 엠디엠
        '263750',  # 펄어비스
        '259960',  # 크래프톤
        '225570',  # 넥슨게임즈
        '112040',  # 위메이드
        '036570'   # 엔씨소프트
    ]

    data = []
    for code in stock_codes:
        stock_data = get_stock_info(code)
        if stock_data:
            data.append(stock_data)
        time.sleep(2)  # 2초 대기

    if not data:
        print("오류: 수집된 데이터가 없습니다.")
        return

    # DataFrame 생성 및 CSV 저장
    df = pd.DataFrame(data)
    df.to_csv('stock_consensus.csv', index=False, encoding='utf-8-sig')
    print(f"[{datetime.now()}] 데이터 수집 완료 (총 {len(data)}개 종목)")

if __name__ == "__main__":
    main() 