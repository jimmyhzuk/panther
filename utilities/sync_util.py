#!/usr/bin/env python
# coding=utf-8
import sys
import sqlalchemy as sa
import pandas as pd
from datetime import datetime

sys.path.append('..')

import config


class SyncUtil(object):
    def __init__(self, source=None, is_db=True):
        source_db = '''mssql+pymssql://{0}:{1}@{2}:{3}/{4}'''.format(config.hh_db_user, config.hh_db_pwd,
                                                                     config.hh_db_host, config.hh_db_port,
                                                                     config.hh_db_database)
        # 源数据库
        if is_db:
            if source == None:
                self.source = sa.create_engine(source_db)
            else:
                self.source = source

    # 获取交易日
    def get_all_trades(self, exchange, start_date, end_date):
        sql = """select TRADEDATE FROM TQ_OA_TRDSCHEDULE WHERE EXCHANGE = '{0}'
                AND ISVALID = 1 AND TRADEDATE >= {1} and TRADEDATE <= {2} ORDER BY TRADEDATE DESC;""".format(exchange,
                                                                                                             start_date,
                                                                                                             end_date)
        trades_sets = pd.read_sql(sql, self.source)
        return trades_sets

    # 获取交易日
    def get_trades_ago(self, exchange, start_date, end_date, count, order='DESC'):
        if count == -1:
            top = ''
        else:
            top = """top ({0})""".format(count)
        sql = """select {0} TRADEDATE FROM TQ_OA_TRDSCHEDULE WHERE EXCHANGE = '{1}'
                AND ISVALID = 1 AND TRADEDATE >= {2} AND TRADEDATE <= {3} ORDER BY TRADEDATE {4}; """.format(top,
                                                                                                             exchange,
                                                                                                             start_date,
                                                                                                             end_date,
                                                                                                             order)
        trades_sets = pd.read_sql(sql, self.source)
        return trades_sets

    # 指定年份 ttm 周期计算
    def ttm_report_date_by_year(self, end_date, year):
        end_date = str(end_date).replace('-', '')
        end_datetime = datetime.strptime(end_date, '%Y%m%d')
        ttm_report_list = []
        start_year = end_datetime.year - year + 1
        pos_year = end_datetime.year
        while pos_year >= start_year:
            ttm_report_list += self.ttm_report_date(
                str(pos_year) + '-' + str(end_datetime.month) + '-' + str(end_datetime.day))
            pos_year -= 1
        ttm_report_list.sort(reverse=True)
        return ttm_report_list

    # ttm周期计算
    def ttm_report_date(self, end_date):
        end_datetime = datetime.strptime(end_date, '%Y-%m-%d')
        ttm_report_list = []
        if end_datetime.month * 100 + end_datetime.day < 501:
            ttm_report_list = [(end_datetime.year - 2) * 10000 + 1231,
                               (end_datetime.year - 1) * 10000 + 331,
                               (end_datetime.year - 1) * 10000 + 630,
                               (end_datetime.year - 1) * 10000 + 930]
        elif 501 <= (end_datetime.month * 100 + end_datetime.day) < 901:
            ttm_report_list = [(end_datetime.year - 1) * 10000 + 331,
                               (end_datetime.year - 1) * 10000 + 630,
                               (end_datetime.year - 1) * 10000 + 930,
                               (end_datetime.year) * 10000 + 331]
        elif 901 <= (end_datetime.month * 100 + end_datetime.day) < 1101:
            ttm_report_list = [(end_datetime.year - 1) * 10000 + 630,
                               (end_datetime.year - 1) * 10000 + 930,
                               (end_datetime.year) * 10000 + 331,
                               (end_datetime.year) * 10000 + 630]
        elif 1101 <= (end_datetime.month * 100 + end_datetime.day):
            ttm_report_list = [(end_datetime.year - 1) * 10000 + 1231,
                               (end_datetime.year) * 10000 + 331,
                               (end_datetime.year) * 10000 + 630,
                               (end_datetime.year) * 10000 + 930]
        return ttm_report_list

    # 获取报告日期
    def create_report_date(self, min_year, max_year):
        report_date_list = []
        start_date = min_year - 1
        if start_date < 2007:
            start_date = 2007
        while start_date <= max_year:
            report_date_list.append(start_date * 10000 + 331)
            report_date_list.append(start_date * 10000 + 630)
            report_date_list.append(start_date * 10000 + 930)
            report_date_list.append(start_date * 10000 + 1231)
            start_date += 1
        report_date_list.sort()
        return report_date_list

    # 从当前日期前推n个报告期，返回报告期日期
    def get_before_report_date(self, trade_date, num):
        year_size = int(num / 4) + 1
        current_year = int(trade_date[:4])
        all_report_date = []
        for year in range(current_year - year_size, current_year + 1):
            all_report_date.append(year * 10000 + 331)
            all_report_date.append(year * 10000 + 630)
            all_report_date.append(year * 10000 + 930)
            all_report_date.append(year * 10000 + 1231)
        all_report_date.sort(reverse=True)
        for report_date in all_report_date:
            if report_date < int(trade_date):
                num -= 1
                if num == 0:
                    return report_date

    # 获取区间
    def every_report_range(self, trade_date, report_date_list):
        report_date_list.sort(reverse=True)
        start_flag = 0
        start_count = 0
        for report_date in report_date_list:
            if int(trade_date) >= report_date:
                start_flag = 1
            if start_flag == 1:
                start_count += 1
                if start_count == 2:
                    return (trade_date, report_date)
        return (0, 0)

    # 财务报告时间换算
    def plus_year(self, row):
        # 331 1, 603 2, 930 3, 1231 4
        row['year'] = row['report_date'].year
        if row['report_date'].month * 100 + row['report_date'].day == 331:
            row['report_type'] = 1
        elif row['report_date'].month * 100 + row['report_date'].day == 630:
            row['report_type'] = 2
        elif row['report_date'].month * 100 + row['report_date'].day == 930:
            row['report_type'] = 3
        elif row['report_date'].month * 100 + row['report_date'].day == 1231:
            row['report_type'] = 4
        return row


if __name__ == "__main__":
    # pdb.set_trace()
    sync = SyncUtil()
    # test = sync.ttm_report_date_by_year('2018-06-10', 5)
    # test = sync.get_before_report_date('20180701', 2)
    test = sync.get_trades_ago('001002', '20180610', '20180615', 1, order='DESC')
    print(test)
