#!/usr/bin/env python
'''Beancount importer for China Merchants Bank debit cards'''

import sys
import csv
import argparse
import re
from datetime import datetime

account_map = {
    "DEFAULT": "Assets:Unknown",

    "房租|租金": "Expenses:Rent",
    "Octopus": "Expenses:Transport",

    "CMB": "Assets:Cash:CMBC-5189:Cash",
    "雪球基金": "Assets:Investment:SnowballFund:Cash",
    "天天基金": "Assets:Investment:TiantianFund:Cash",
    "提取托付": "Assets:Government:HousingFund:SZ",
    "约定批量提取": "Assets:Government:HousingFund:SH", # HousingFund:SH-S

    "工资": "Income:ARMC:GrossPay:BasicSalary", # To be refine
    "报销": "Income:ARMC:Reimbursement",
    "平安养老保险": "Income:Insurance",

    "支付宝-余额充值|支付宝-蚂蚁（杭州）基金销售有限公司": "Assets:Cash:Alipay",
    "零钱通": "Assets:Cash:WeChat",
    "中信银行信用卡|银联代收，信用卡还款": "Liabilities:CreditCard:CIBK-4691",
    "招商银行信用卡|信用卡自扣": "Liabilities:CreditCard:CMBC-0035",
    "中国银行信用卡|中银信用卡还款": "Liabilities:CreditCard:BKCH-8693",
    "银期转账:徽商期货": "Assets:Investment:HuishangFuture:Positions",
}

def mapping_account(account_map, keyword):
    """Finding which key of account_map contains the keyword, return the corresponding value.

    Args:
      account_map: A dict of account keywords string (each keyword separated by "|") to account name.
      keyword: A keyword string.
    Return:
      An account name string.
    Raises:
      KeyError: If "DEFAULT" keyword is not in account_map.
    """
    if "DEFAULT" not in account_map:
        raise KeyError("DEFAULT is not in " + account_map.__str__())
    account_name = account_map["DEFAULT"]
    for account_keywords in account_map.keys():
        if account_keywords == "DEFAULT":
            continue
        if re.search(account_keywords, keyword) or account_keywords == keyword:
            account_name = account_map[account_keywords]
            break
    return account_name

def get_DRCR_status(income, outcome):
    """Get the status which says DEBIT or CREDIT of a row.
    """
    if outcome:
        return 'credit', outcome
    else:
        return 'debit', income


class CMBDebitCardParser(object):

    def __init__(self, csv_data):
        self.reader = csv.reader(csv_data)
        self.parsed = []

    def _expand_date(self, date):
        orig_date = datetime.strptime(date, '%Y%m%d')
        iso_date = orig_date.date().strftime('%Y-%m-%d')
        return iso_date

    def _expand_time(self, date):
        orig_date = datetime.strptime(date, '%H:%M:%S')
        iso_time = orig_date.time().strftime('%H:%M:%S')
        return iso_time

    def _get_amounts(self, amount):
        _abs = amount.strip('-')
        if amount.startswith('-'):
            return '-' + _abs, '+' + _abs
        else:
            return '+' + _abs, '-' + _abs

    def parse(self, default_pass=True):
        for row in reversed(list(self.reader)):
            # Skip empty lines, comment lines, and table headers
            if not row:
                continue
            if row[0].startswith('#') or row[0].startswith('交易日期'):
                continue

            c = {}
            c['date']    = row[0].strip() #交易日期
            c['time']    = row[1].strip() #交易时间
            c['income']  = row[2].strip() #收入
            c['outcome'] = row[3].strip() #支出
            c['balance'] = row[4].strip() #余额
            c['type']    = row[5].strip() #交易类型
            c['comment'] = row[6].strip() #交易备注

            # Skip special lines
            if c['type'].startswith('朝朝宝'):
                continue

            d = {}
            d['date'] = self._expand_date(c['date'])
            d['time'] = self._expand_time(c['time'])
            #d['flag'] = '*' if default_pass else '!'
            d['narration'] = c['time'] + ' ' + c['type'] + ' ' + c['comment']
            drcr, amount = get_DRCR_status(c['income'], c['outcome'])
            if drcr == 'credit':
                d['credit'] = mapping_account(account_map, 'CMB')
                d['debit']  = mapping_account(account_map, c['comment'])
            else:
                d['credit'] = mapping_account(account_map, c['comment'])
                d['debit']  = mapping_account(account_map, 'CMB')
            d['credit_amount'] = '-' + amount
            d['debit_amount']  = amount
            d['flag'] = '!' if d['credit'] == 'Assets:Unknown' or d['debit'] == 'Assets:Unknown' else '*'
            self.parsed.append(d)

        return self.parsed


def compose_beans(parsed):
    template = (
        '{date} {flag} "{narration}"\n'
        '    {credit}    {credit_amount} CNY\n'
        '    {debit}    {debit_amount} CNY'
    )
    beans = [template.format_map(p) for p in parsed]
    return beans


def print_beans(beans, filename=None):
    header = '\n; Imported from {}'.format(filename)
    sep = '\n' * 2
    print(header)
    print(sep.join(beans))

def write_beans(beans, filename=None, savename=None):
    header = '; Imported from {}\n'.format(filename)
    sep = '\n' * 2
    with open(savename, 'w', encoding='utf-8') as file:
        file.write(header+'\n')
        file.write(sep.join(beans))

def main():
    argparser = argparse.ArgumentParser()
    argparser.add_argument(
        'csv', nargs='?', type=argparse.FileType(mode='r', encoding='utf-8-sig'), default=sys.stdin,
        help='CSV file of China Merchants Bank debit card data'
    )
    argparser.add_argument('-p', '--pass', dest='_pass', action='store_true')
    args = argparser.parse_args()

    parser = CMBDebitCardParser(args.csv)
    parsed = parser.parse(default_pass=args._pass)
    beans = compose_beans(parsed)
    print_beans(beans, args.csv.name)
    write_beans(beans, args.csv.name, 'bank_cmb.bean')


if __name__ == '__main__':
    main()
