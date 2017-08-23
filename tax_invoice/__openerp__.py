# -*- coding: utf-8 -*-
{
    'name': "GOODERP 税务模块-进项发票",
    'author': "德清武康开源软件工作室",
    'website': "无",
    'category': 'gooderp',
    "description":
    '''
                        该模块实现了导入认证系统的进项发票，与自己的结算单／其他采购单匹配。
                        现在此模块仅支持1笔业务多张发票的情况，不支持多笔业务一张发票的情况。
                        1.在资金-结算单（money.invoice）填上发票号码，支持","和"-"。
                        2.在会计-发票匹配中导入从认证系统中导出的excel。
                        3.点击匹配，进行结算单与发票的匹配。
                        4.发票匹配中全部都有结算单后点击确认。
    ''',
    'version': '11.11',
    'depends': ['base', 'core', 'finance', 'money', 'tax'],
    'data': [
        'view/tax_invoice_view.xml',
        'view/tax_invoice_action.xml',
        'view/tax_invoice_menu.xml',
        'security/ir.model.access.csv',
    ],
    'demo': [
    ],
    'qweb': [
        "static/src/xml/*.xml",
    ],
}
