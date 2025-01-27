import akshare as ak
import pandas as pd
import datetime

d = []

stock_map = [
    ["2023-01-01","2024-12-31","105.AMZN","AMZN","亚马逊 Amazon"],
    ]

stock_df = pd.DataFrame(stock_map,columns=['start','end','code','s_name','c_name'])

for i, stock in stock_df.iterrows():
    stock_code = stock['code']
    period = "weekly"
    start_date = datetime.datetime.strptime(stock['start'], "%Y-%m-%d").strftime("%Y%m%d")
    end_date = datetime.datetime.strptime(stock['end'], "%Y-%m-%d").strftime("%Y%m%d")
    adjust = "" #默认 adjust="", 则返回未复权的数据; adjust="qfq" 则返回前复权的数据, adjust="hfq" 则返回后复权的数据

    
    stock_us_hist_df = ak.stock_us_hist(symbol=stock_code, period=period, start_date=start_date, end_date=end_date, adjust=adjust)

    if stock_us_hist_df.empty:
        print("Error: No data retrieved")
    stock_us_hist_df.set_index('日期', inplace=True)
    
    comment = '\n* ' + ' '.join(stock)
    d.append(comment)
    print(comment)
    for date, row in stock_us_hist_df.iterrows():
        line = f"{date} price {stock['s_name']} {row['收盘']:.2f} USD"
        d.append(line)
        #print(line)


stock_map = [
    ["2023-01-01","2024-12-31","603288","HTWY","海天味业"],
    ["2023-01-01","2024-12-31","002415","HKWS","海康威视"],
    ["2023-01-01","2024-12-31","002714","MYGF","牧原股份"],
    ["2023-01-01","2024-12-31","002550","QHZY","千红制药"],
    ["2023-01-01","2024-12-31","601989","ZGZG","中国重工"],
    ["2023-01-01","2024-12-31","601226","HDKG","华电科工"],
    ]

stock_df = pd.DataFrame(stock_map,columns=['start','end','code','s_name','c_name'])

for i, stock in stock_df.iterrows():
    stock_code = stock['code']
    period = "weekly"
    start_date = datetime.datetime.strptime(stock['start'], "%Y-%m-%d").strftime("%Y%m%d")
    end_date = datetime.datetime.strptime(stock['end'], "%Y-%m-%d").strftime("%Y%m%d")
    adjust = "" #默认 adjust="", 则返回未复权的数据; adjust="qfq" 则返回前复权的数据, adjust="hfq" 则返回后复权的数据
    
    stock_zh_a_hist_df = ak.stock_zh_a_hist(symbol=stock_code, period=period, start_date=start_date, end_date=end_date, adjust=adjust)

    if stock_zh_a_hist_df.empty:
        print("Error: No data retrieved")
    stock_zh_a_hist_df.set_index('日期', inplace=True)
    
    comment = '\n* ' + ' '.join(stock)
    d.append(comment)
    print(comment)
    for date, row in stock_zh_a_hist_df.iterrows():
        line = f"{date} price {stock['s_name']} {row['收盘']:.2f} CNY"
        d.append(line)
        #print(line)


fund_open_map = [
    ["2022-01-01","2024-12-31","001717","GYRX_QYYL","工银瑞信前沿医疗A"],
    ["2023-01-01","2024-12-31","007744","CSAY_CZ","长盛安逸纯债A"],
    ["2024-01-01","2024-12-31","016790","ZSXL_CZ","招商鑫利中短债债券A"],
    ["2023-01-01","2024-12-31","015736","CSSY_CZ","长盛盛裕纯债D"],
    ["2023-01-01","2024-12-31","013428","DXXX_CZ","东兴鑫享6个月滚动持有债券A"],
    ["2023-01-01","2024-12-31","003547","PHFL_CZ","鹏华丰禄债券"],
    ["2023-01-01","2024-12-31","000183","JSFY_CZ","嘉实丰益策略定期债券"],
    ["2023-01-01","2024-12-31","217022","ZSCY_CZ","招商产业债券A"],
    ["2023-01-01","2024-12-31","016149","ZYJJX_CZ","中银季季享90天滚动持有债券A"],
    ["2023-01-01","2024-12-31","970039","TFLGY_CZ","天风六个月滚动持有债券A"], #Sold 2024-09-23
    ["2022-01-01","2024-12-31","004011","HTDL_HH","华泰博瑞鼎利混合C"], #Sold 2024-10-11
    ["2023-01-01","2024-12-31","009617","DXXL_CZ","东兴兴利债券C"], #Sold 2024-11-15
    ["2024-01-01","2024-12-31","013964","DCSYX_CZ","达诚定海双月享60天滚动持有短债A"], #Sold 2024-12-23
    ]

fund_open_df = pd.DataFrame(fund_open_map,columns=['start','end','code','s_name','c_name'])

for i, fund in fund_open_df.iterrows():
    symbol = fund['code']
    start_date = datetime.datetime.strptime(fund['start'], "%Y-%m-%d").date()
    end_date = datetime.datetime.strptime(fund['end'], "%Y-%m-%d").date()

    fund_open_fund_info_em_df = ak.fund_open_fund_info_em(symbol=symbol, indicator="单位净值走势")

    fund_open_fund_info_em_df.set_index('净值日期', inplace=True)
    
    comment = '\n* ' + ' '.join(fund)
    d.append(comment)
    print(comment)
    for date, row in fund_open_fund_info_em_df.iterrows():
        if (date >= start_date) and (date <= end_date):
            line = f"{date} price {fund['s_name']} {row['单位净值']:.4f} CNY"
            d.append(line)
            #print(line)


fund_etf_map = [
    ["2022-01-01","2024-12-31","159859","SWYY_ETF","生物医药ETF"],
    ["2024-01-01","2024-12-31","159869","YX_ETF","游戏ETF"],
    ["2024-01-01","2024-12-31","159985","DP_ETF","豆粕ETF"],
    ["2024-01-01","2024-12-31","510300","HS300_ETF","沪深300ETF"],
    ["2024-01-01","2024-12-31","518880","GOLD_ETF","黄金ETF"], #Sold 2024-12-30
    ["2024-01-01","2024-12-31","161226","SILV_LOF","白银LOF"], #Sold 2024-12-30
    ["2024-01-01","2024-12-31","515210","GT_ETF","钢铁ETF"], #Sold 2024-10-08
    ]

fund_etf_df = pd.DataFrame(fund_etf_map,columns=['start','end','code','s_name','c_name'])

for i, fund in fund_etf_df.iterrows():
    symbol = fund['code']
    start_date = datetime.datetime.strptime(fund['start'], "%Y-%m-%d").strftime("%Y%m%d")
    end_date = datetime.datetime.strptime(fund['end'], "%Y-%m-%d").strftime("%Y%m%d")

    fund_etf_fund_info_em_df = ak.fund_etf_fund_info_em(fund=symbol, start_date=start_date, end_date=end_date)

    fund_etf_fund_info_em_df.set_index('净值日期', inplace=True)
    
    comment = '\n* ' + ' '.join(fund)
    d.append(comment)
    print(comment)
    for date, row in fund_etf_fund_info_em_df.iterrows():
        line = f"{date} price {fund['s_name']} {row['单位净值']:.4f} CNY"
        d.append(line)
        #print(line)


with open('price_gen.bean', 'w', encoding='utf-8') as file:
    file.write('\n'.join(d))
