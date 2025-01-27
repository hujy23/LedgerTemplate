#!/usr/bin/env python
'''Beancount importer for Alipay'''

import sys
import csv
import argparse
import re
from datetime import datetime

# 正则表达式，竖线分割，括号有特殊含义要加反斜线，空格正常
# 交易备注里可以写上关键词以实现额外匹配
# 从上到下匹配，成功则返回，故上面的优先级高
account_map = {
    "DEFAULT": "Assets:Unknown",

    "中国移动|上海联通|科学上网": "Expenses:Telecom",
    "酒店|宾馆|汉庭|华住": "Expenses:Hotel",
    "爱车养车|小兔充充|出入境管理局": "Expenses:Transport",

    "餐饮美食": "Expenses:EatAndDrink",
    "服饰装扮": "Expenses:Clothing",
    "日用百货": "Expenses:DailyUtilities",
    "家居家装": "Expenses:HomeDecoration",
    "数码电器": "Expenses:Digital",
    "美容美发": "Expenses:BeautyHair",
    "交通出行": "Expenses:Transport",
    "住房物业": "Expenses:Rent",
    "文化休闲": "Expenses:Entertainment",
    "教育培训": "Expenses:Education",
    "医疗健康": "Expenses:Health",
    "公益捐赠": "Expenses:Donation",

    "余额宝|账户余额": "Assets:Cash:Alipay",

    "平安养老保险": "Income:Insurance",

    "招商银行储蓄卡": "Assets:Cash:CMBC-5189:Cash",
    "中信银行信用卡|银联代收，信用卡还款": "Liabilities:CreditCard:CIBK-4691",
    "招商银行信用卡|信用卡自扣": "Liabilities:CreditCard:CMBC-0035",
    "中国银行信用卡|中银信用卡还款": "Liabilities:CreditCard:BKCH-8693",
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

def get_DRCR_status(io_type, row):
    """Get the status which says DEBIT or CREDIT of a row.
    """
    if io_type == '支出':
        return 'credit'
    elif io_type == '收入':
        return 'debit'
    else:
        raise KeyError("Unknown 收/支 type： " + io_type + " " + row.__str__())


class AlipayParser(object):

    def __init__(self, csv_data):
        self.reader = csv.reader(csv_data)
        self.parsed = []

    def _expand_datetime(self, date):
        orig_date = datetime.strptime(date, '%Y-%m-%d %H:%M:%S')
        iso_date = orig_date.date().strftime('%Y-%m-%d')
        iso_time = orig_date.time().strftime('%H:%M:%S')
        return iso_date, iso_time

    def _get_amounts(self, io_type, amount):
        amount_abs = amount.strip('¥')
        if io_type == '收入':
            return '+' + amount_abs, '-' + amount_abs
        elif io_type == '支出':
            return '-' + amount_abs, '+' + amount_abs
        else:
            return '?' + amount_abs, '?' + amount_abs

    def parse(self, default_pass=True):
        for row in reversed(list(self.reader)):
            # Skip empty lines and table headers
            if not row:
                continue
            if row[0].startswith('交易时间'):
                break

            c = {}
            c['datetime']= row[0].strip() #交易时间
            c['type']    = row[1].strip() #交易分类
            c['payee']   = row[2].strip() #交易对方
            c['payee_id']= row[3].strip() #对方账号
            c['item']    = row[4].strip() #商品说明
            c['io_type'] = row[5].strip() #收/支
            c['amount']  = row[6].strip() #金额
            c['payer']   = row[7].strip() #收/付款方
            c['status']  = row[8].strip() #交易状态
            c['t_id']    = row[9].strip() #交易订单号
            c['m_id']    = row[10].strip() #商户订单号
            c['comment'] = row[11].strip() #备注
            c['item']    = c['item'].replace('"', "'")

            # Skip special lines
            if c['io_type'] == '不计收支':
                if c['item'].startswith('余额宝'): #收益发放
                    continue
                if c['item'].startswith('花呗自动还款'):
                    continue
                if c['item'] == '转账收款到余额宝' or c['item'] == '充值-普通充值':
                    continue
                if c['status'] == '交易关闭' or c['status'] == '已关闭':
                    continue
                if c['status'] == '芝麻免押下单成功' or c['status'] == '解冻成功':
                    continue
                if c['status'] == '冻结成功':
                    continue
                if c['payer'].startswith('支付宝小荷包'):
                    continue
                if c['status'] == '退款成功':
                    c['io_type'] = '收入'
    
            d = {}
            d['date'], d['time'] = self._expand_datetime(c['datetime'])
            d['flag'] = '*'# if default_pass else '!'
            d['payee'] = c['payee']
            d['narration'] = c['type'] + ' ' + c['item'] + ' ' + c['comment'] + ' ' + d['time']

            drcr = get_DRCR_status(c['io_type'], row)
            if drcr == 'credit':
                d['credit'] = mapping_account(account_map, c['payer'])
                d['debit']  = mapping_account(account_map, c['type'] + c['payee'] + c['comment'])
            else:
                d['credit'] = mapping_account(account_map, c['type'] + c['payee'] + c['comment'])
                d['debit']  = mapping_account(account_map, c['payer'])
            d['credit_amount'] = '-' + c['amount']
            d['debit_amount']  = c['amount']
            d['flag'] = '!' if d['credit'] == 'Assets:Unknown' or d['debit'] == 'Assets:Unknown' else d['flag']
            self.parsed.append(d)

        return self.parsed


def compose_beans(parsed):
    template = (
        '{date} {flag} "{payee}" "{narration}"\n'
        '    {credit}    {credit_amount} CNY\n'
        '    {debit}    {debit_amount} CNY'
    )
    beans = [template.format_map(p) for p in parsed]
    return beans


def print_beans(beans, filename=None):
    header = '; Imported from {}\n'.format(filename)
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
        help='CSV file of Alipay'
    )
    argparser.add_argument('-p', '--pass', dest='_pass', action='store_true')
    args = argparser.parse_args()

    parser = AlipayParser(args.csv)
    parsed = parser.parse(default_pass=args._pass)
    beans = compose_beans(parsed)
    print_beans(beans, args.csv.name)
    write_beans(beans, args.csv.name, 'alipay.bean')


if __name__ == '__main__':
    main()
