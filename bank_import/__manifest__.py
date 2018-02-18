# -*- coding: utf-8 -*-
{
    'name': "GOODERP 税务模块-银行明细导入",
    'author': "德清武康开源软件工作室",
    'website': "无",
    'category': 'gooderp',
    "description":
    '''
                        该模块实现了导入银行明细，生成收付款单
    ''',
    'version': '11.11',
    'depends': ['base', 'core', 'finance', 'money', 'tax'],  
    'data': [
        'view/bank_import_view.xml',
        'view/bank_import_action.xml',
        'view/bank_import_menu.xml',
        #'security/ir.model.access.csv',
    ],
    'demo': [
    ],
    'qweb': [
        "static/src/xml/*.xml",
    ],
}
