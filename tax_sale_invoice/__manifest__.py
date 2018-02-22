# -*- coding: utf-8 -*-
{
    'name': "GOODERP 税务模块-销项发票导入生成销项定单及",
    'author': "德清武康开源软件工作室",
    'website': "无",
    'category': 'gooderp',
    "description":
    '''
                        该模块为从金税系统导出开票内容，导入系统后，自动生成销售订单，出库单，结算单。
    ''',
    'version': '11.11',
    'depends': ['base', 'core', 'finance', 'money', 'tax', 'sell'],
    'data': [
        'view/sale_invoice_view.xml',
        'view/sale_invoice_action.xml',
        'view/sale_invoice_menu.xml',
        'security/ir.model.access.csv',
    ],
    'demo': [
    ],
    'qweb': [
        "static/src/xml/*.xml",
    ],
}
