#!/usr/bin/env python
'''Beancount importer for WeChat'''

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

    "房租|租金": "Expenses:Rent",
    "Octopus|途运科技|样样巴士|AA巴士|帅淘|巴士|迅隆船务|ZAKC Limited|大巴|出租车|打车|出行|高铁": "Expenses:Transport",
    "中国儿童少年基金会|上海联劝公益基金会|上海仁德基金会|水滴筹": "Expenses:Donation",
    "香蕉|水果|松涛园|Olé|兰州拉面|饿了么": "Expenses:EatAndDrink",
    "发给|喜欢作者|发出群红包|微信红包-退款": "Expenses:Relationship:GiftMoney",
    "顺丰": "Expenses:DailyUtilities",
    "上海早木信息科技有限公司": "Expenses:Education",

    "零钱|零钱通": "Assets:Cash:WeChat",

    "群收款": "Income:TransferIn",
    "微信红包": "Income:Relationship:GiftMoney",

    "中信银行信用卡|中信银行\(4691\)|银联代收，信用卡还款": "Liabilities:CreditCard:CIBK-4691",
    "招商银行信用卡|招商银行\(0035\)|信用卡自扣": "Liabilities:CreditCard:CMBC-0035",
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


class WechatParser(object):

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
            c['type']    = row[1].strip() #交易类型
            c['payee']   = row[2].strip() #交易对方
            c['item']    = row[3].strip() #商品
            c['io_type'] = row[4].strip() #收/支
            c['amount']  = row[5].strip() #金额(元)
            c['payer']   = row[6].strip() #支付方式
            c['status']  = row[7].strip() #当前状态
            c['t_id']    = row[8].strip() #交易单号
            c['m_id']    = row[9].strip() #商户单号
            c['comment'] = row[10].strip() #备注
            c['item']    = c['item'].strip('收款方备注:二维码收款').replace('"', "'")
            c['amount']  = c['amount'].strip('¥')

            # Skip special lines
            if c['type'].startswith('转入零钱通'):
                continue

            d = {}
            d['date'], d['time'] = self._expand_datetime(c['datetime'])
            #d['flag'] = '*' if default_pass else '!'
            d['payee'] = c['payee']
            d['narration'] = c['type'] + ' ' + c['item'] + ' ' + d['time']

            drcr = get_DRCR_status(c['io_type'], row)
            if drcr == 'credit':
                d['credit'] = mapping_account(account_map, c['payer'])
                d['debit']  = mapping_account(account_map,             c['payee'] + c['item'])
            else:
                d['credit'] = mapping_account(account_map, c['type'] + c['payee'] + c['item'])
                d['debit']  = mapping_account(account_map, c['payer'] + c['status'])
            d['credit_amount'] = '-' + c['amount']
            d['debit_amount']  = c['amount']
            d['flag'] = '!' if d['credit'] == 'Assets:Unknown' or d['debit'] == 'Assets:Unknown' else '*'
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
        help='CSV file of WeChat'
    )
    argparser.add_argument('-p', '--pass', dest='_pass', action='store_true')
    args = argparser.parse_args()

    parser = WechatParser(args.csv)
    parsed = parser.parse(default_pass=args._pass)
    beans = compose_beans(parsed)
    print_beans(beans, args.csv.name)
    write_beans(beans, args.csv.name, 'wechat.bean')


if __name__ == '__main__':
    main()
