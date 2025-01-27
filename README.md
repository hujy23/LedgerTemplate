# LedgerTemplate

My [Beancount](https://github.com/beancount/beancount) ledger template, including python scripts for bank, wechat and alipay bills processing, market price getting for Chinese stock.

## Generate beans

```sh
cd importer
python ./bank_cmb.py ../data/2024/CMB_6214--------5189_20240101_20240131.csv
python ./wechat.py '../data/2024/微信支付账单(20240101-20240131).csv'
python ./alipay.py ../data/2024/alipay_record_202401.csv
```

## Get market price

```sh
cd importer
python ./price_gen.py
```
