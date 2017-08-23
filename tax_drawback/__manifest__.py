# -*- coding: utf-8 -*-
{
    'name': "GOODERP 税务模块-出口退税",
    'author': "德清武康开源软件工作室",
    'website': "无",
    'category': 'gooderp',
    "description":
    '''
                        该模块为税务出口退税申报，退税记录
    ''',
    'version': '11.11',
    'depends': ['base', 'core', 'finance', 'warehouse'],
    'data': [
        'view/tax_drawback_view.xml',
        'view/tax_drawback_action.xml',
        'view/tax_drawback_menu.xml',
    ],
    'demo': [
    ],
    'qweb': [
        "static/src/xml/*.xml",
    ],
}
