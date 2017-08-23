# -*- coding: utf-8 -*-
{
    'name': "GOODERP 税务模块",
    'author': "德清武康开源软件工作室",
    'website': "无",
    'category': 'gooderp',
    "description":
    '''
                        工资表导出excel，用与导入金三系统
    ''',
    'version': '11.11',
    'depends': ['staff_wages'],
    'data': [
        'view/export_wages_view.xml',

 ],
    'demo': [
    ],
    'qweb': [
        "static/src/xml/*.xml",
    ],
}
