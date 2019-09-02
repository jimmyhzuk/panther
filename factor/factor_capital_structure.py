#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
@version:
@author: Wang
@file: factor_operation_capacity.py
@time: 2019-05-30
"""
import sys
sys.path.append('../')
sys.path.append('../../')
sys.path.append('../../../')
import json
import numpy as np
import pandas as pd
from factor.factor_base import FactorBase
from pandas.io.json import json_normalize
from factor.utillities.calc_tools import CalcTools

from factor import app
from ultron.cluster.invoke.cache_data import cache_data


class CapitalStructure(FactorBase):
    """
    资本结构
    """
    def __init__(self, name):
        super(CapitalStructure, self).__init__(name)

    def create_dest_tables(self):
        """
        创建数据库表
        :return:
        """
        drop_sql = """drop table if exists `{0}`""".format(self._name)
        create_sql = """create table `{0}`(
                    `id` varchar(32) NOT NULL,
                    `symbol` varchar(24) NOT NULL,
                    `trade_date` date NOT NULL,
                    
                    `non_current_assets_ratio` decimal(19,4),
                    `long_term_debt_to_asset` decimal(19,4),
                    `long_debt_to_asset` decimal(19,4),
                    `intangible_asset_ratio` decimal(19,4),
                    `fix_asset_ratio` decimal(19,4),
                    `equity_to_asset` decimal(19,4),
                    `equity_fixed_asset_ratio` decimal(19,4),
                    `current_assets_ratio` decimal(19,4),
                    PRIMARY KEY(`id`,`trade_date`,`symbol`)
                    )ENGINE=InnoDB DEFAULT CHARSET=utf8;""".format(self._name)
        super(CapitalStructure, self)._create_tables(create_sql, drop_sql)

    @staticmethod
    def non_current_assets_ratio(tp_management, factor_management, dependencies=['total_non_current_assets', 'total_assets']):
        """
        非流动资产比率
        非流动资产比率 = 非流动资产合计 / 总资产
        :param dependencies:
        :param tp_management:
        :param factor_management:
        :return:
        """

        management = tp_management.loc[:, dependencies]
        management['non_current_assets_ratio'] = np.where(
            CalcTools.is_zero(management.total_assets.values), 0,
            management.total_non_current_assets.values / management.total_assets.values)
        management = management.drop(dependencies, axis=1)
        factor_management = pd.merge(factor_management, management, on="symbol")
        return factor_management

    @staticmethod
    def long_term_debt_to_asset(tp_management, factor_management, dependencies=['total_non_current_liability', 'total_assets']):
        """
        长期负债与资产总计之比
        长期负债与资产总计之比 = 非流动性负债合计/总资产
        :param dependencies:
        :param tp_management:
        :param factor_management:
        :return:
        """

        management = tp_management.loc[:, dependencies]
        management['long_term_debt_to_asset'] = np.where(
            CalcTools.is_zero(management.total_assets.values), 0,
            management.total_non_current_liability.values / management.total_assets.values)
        management = management.drop(dependencies, axis=1)
        factor_management = pd.merge(factor_management, management, on="symbol")
        return factor_management


    @staticmethod
    def long_debt_to_asset(tp_management, factor_management, dependencies=['longterm_loan', 'total_assets']):
        """
        长期借款与资产总计之比
        长期借款与资产总计之比 = 长期借款/总资产
        :param dependencies:
        :param tp_management:
        :param factor_management:
        :return:
        """

        management = tp_management.loc[:, dependencies]
        management['long_debt_to_asset'] = np.where(
            CalcTools.is_zero(management.total_assets.values), 0,
            management.longterm_loan.values / management.total_assets.values)
        management = management.drop(dependencies, axis=1)
        factor_management = pd.merge(factor_management, management, on="symbol")
        return factor_management


    @staticmethod
    def intangible_asset_ratio(tp_management, factor_management, dependencies=['intangible_assets', 'development_expenditure', 'good_will', 'total_assets']):
        """
        无形资产比率
        无形资产比率 = （无形资产 + 研发支出 + 商誉）/ 总资产
        :param dependencies:
        :param tp_management:
        :param factor_management:
        :return:
        """

        management = tp_management.loc[:, dependencies]
        management["ia"] = (management.intangible_assets +
                            management.development_expenditure +
                            management.good_will)
        management['intangible_asset_ratio'] = np.where(
            CalcTools.is_zero(management.total_assets.values), 0,
            management.ia.values / management.total_assets.values)
        dependencies.append('ia')
        management = management.drop(dependencies, axis=1)
        factor_management = pd.merge(factor_management, management, on="symbol")
        return factor_management

    @staticmethod
    def fix_asset_ratio(tp_management, factor_management, dependencies=['fixed_assets', 'construction_materials', 'constru_in_process', 'total_assets']):
        """
        固定资产比率
        固定资产比率 = （固定资产+工程物资+在建工程）/总资产
        :param dependencies:
        :param tp_management:
        :param factor_management:
        :return:
        """

        management = tp_management.loc[:, dependencies]
        management['fix_asset_ratio'] = np.where(
            CalcTools.is_zero(management.total_assets.values), 0,
            (management.fixed_assets.values +
             management.construction_materials.values +
             management.constru_in_process.values) / management.total_assets.values)
        management = management.drop(dependencies, axis=1)
        factor_management = pd.merge(factor_management, management, on="symbol")
        return factor_management


    @staticmethod
    def equity_to_asset(tp_management, factor_management, dependencies=['total_owner_equities', 'total_assets']):
        """
        股东权益比率
        股东权益比率 = 股东权益/总资产
        :param dependencies:
        :param tp_management:
        :param factor_management:
        :return:
        """

        management = tp_management.loc[:, dependencies]
        management['equity_to_asset'] = np.where(
            CalcTools.is_zero(management.total_assets.values), 0,
            management.total_owner_equities.values / management.total_assets.values)
        management = management.drop(dependencies, axis=1)
        factor_management = pd.merge(factor_management, management, on="symbol")
        return factor_management

    @staticmethod
    def equity_fixed_asset_ratio(tp_management, factor_management, dependencies=['total_owner_equities', 'fixed_assets', 'construction_materials', 'constru_in_process']):
        """
        股东权益与固定资产比率
        股东权益与固定资产比率 = 股东权益/（固定资产+工程物资+在建工程）
        :param dependencies:
        :param tp_management:
        :param factor_management:
        :return:
        """

        management = tp_management.loc[:, dependencies]
        management['equity_fixed_asset_ratio'] = np.where(
            CalcTools.is_zero(management.fixed_assets.values +
                              management.construction_materials.values +
                              management.constru_in_process.values), 0,
            management.total_owner_equities.values
            / (management.fixed_assets.values
               + management.construction_materials.values
               + management.constru_in_process.values))
        management = management.drop(dependencies, axis=1)
        factor_management = pd.merge(factor_management, management, on="symbol")
        return factor_management


    @staticmethod
    def current_assets_ratio(tp_management, factor_management, dependencies=['total_current_assets', 'total_assets']):
        """
        流动资产比率
        流动资产比率 = 流动资产合计/总资产
        :param dependencies:
        :param tp_management:
        :param factor_management:
        :return:
        """

        management = tp_management.loc[:, dependencies]
        management['current_assets_ratio'] = np.where(
            CalcTools.is_zero(management.total_assets.values), 0,
            management.total_current_assets.values / management.total_assets.values)
        management = management.drop(dependencies, axis=1)
        factor_management = pd.merge(factor_management, management, on="symbol")
        return factor_management


def calculate(trade_date, management_data_dic, management):  # 计算对应因子
    print(trade_date)
    # 读取目前涉及到的因子
    tp_management = management_data_dic['tp_management']
    ttm_management = management_data_dic['ttm_management']

    # 因子计算
    factor_management = pd.DataFrame()
    factor_management['symbol'] = tp_management.index
    factor_management = management.non_current_assets_ratio(tp_management, factor_management)
    factor_management = management.long_term_debt_to_asset(tp_management, factor_management)
    factor_management = management.long_debt_to_asset(tp_management, factor_management)
    factor_management = management.intangible_asset_ratio(tp_management, factor_management)
    factor_management = management.fix_asset_ratio(tp_management, factor_management)
    factor_management = management.equity_to_asset(tp_management, factor_management)
    factor_management = management.equity_fixed_asset_ratio(tp_management, factor_management)
    factor_management = management.current_assets_ratio(tp_management, factor_management)

    factor_management['id'] = factor_management['symbol'] + str(trade_date)
    factor_management['trade_date'] = str(trade_date)
    management._storage_data(factor_management, trade_date)


@app.task()
def factor_calculate(**kwargs):
    print("management_kwargs: {}".format(kwargs))
    date_index = kwargs['date_index']
    session = kwargs['session']
    cash_flow = CapitalStructure('factor_management')  # 注意, 这里的name要与client中新建table时的name一致, 不然回报错
    content1 = cache_data.get_cache(session + str(date_index) + "1", date_index)
    content2 = cache_data.get_cache(session + str(date_index) + "2", date_index)
    tp_management = json_normalize(json.loads(str(content1, encoding='utf8')))
    ttm_management = json_normalize(json.loads(str(content2, encoding='utf8')))
    tp_management.set_index('symbol', inplace=True)
    ttm_management.set_index('symbol', inplace=True)
    print("len_tp_management_data {}".format(len(tp_management)))
    print("len_ttm_management_data {}".format(len(ttm_management)))
    total_cash_flow_data = {'tp_management': tp_management, 'ttm_management': ttm_management}
    calculate(date_index, total_cash_flow_data, cash_flow)
