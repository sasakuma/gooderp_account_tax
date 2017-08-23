# -*- coding: utf-8 -*-
{
    'name': "GOODERP 税务模块-税务申报报表，地税申报上传",
    'author': "德清武康开源软件工作室",
    'website': "无",
    'category': 'gooderp',
    "description":
    '''
                        该模块为上传地税申报模块
    ''',
    'version': '11.11',
    'depends': ['base', 'core', 'finance', 'money', 'tax'],
    'data': [
        'view/tax_provice_report_view.xml',
        'view/tax_provice_report_action.xml',
        'view/tax_provice_report_menu.xml',
        'security/ir.model.access.csv',
    ],
    'demo': [
    ],
    'qweb': [
        "static/src/xml/*.xml",
    ],
}
