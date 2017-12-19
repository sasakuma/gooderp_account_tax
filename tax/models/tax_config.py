# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2016  开阖软件(<http://www.osbzr.com>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError



PROVINCE_TYPE = [('cj_jy', u'上传城建，教育附加，地方教育附加'),
                      ('stamp_duty', u'印花税'),
                      ('social_security', u'社保'),
                      ('property', u'房产税')]

COUNTRY_TYPE = [('no1', u'运输服务'),
                 ('no2', u'电信服务'),
                 ('no3', u'建筑安装服务'),
                 ('no4', u'不动产租赁服务'),
                 ('no5', u'受让土地使用权'),
                 ('no6', u'金融保险服务'),
                 ('no7', u'生活服务'),
                 ('no8', u'取得无形资产'),
                 ('no10', u'货物及加工、修理修配劳务'),
                 ('no12', u'建筑安装服务'),
                 ('no14', u'购建不动产并一次性抵扣'),
                 ('no15', u'通行费'),
                 ('no16', u'有形动产租赁服务')]

class config_country(models.Model):
    _name = 'config.country'

    name = fields.Char(u'地税登入名', required=True)
    password = fields.Char(u'地税密码', required=True)
    tel_number = fields.Char(u'手机后4位')


class config_province(models.Model):
    _name = 'config.province'

    name = fields.Char(u'社会统一编码', required=True)
    company_name = fields.Char(u'企业名称', required=True)
    password = fields.Char(u'国税密码', required=True)
    balance_lins = fields.One2many('balance.line',
                               'order_id',
                               u'资产负债表',
                               copy=False,
                               required=True)
    profit_lins = fields.One2many('profit.line',
                               'order_id',
                               u'利润表',
                               copy=False,
                               required=True)

class balance_line(models.Model):
    _name = 'balance.line'

    order_id = fields.Many2one('config.province', u'单位名称', index=True,
                               required=True, ondelete='cascade')
    update_name = fields.Char(u'上传名称',
                          required=True)
    excel_ncows = fields.Char(u'EXCEL对应列',
                          required=True)
    excel_ncols = fields.Char(u'EXCEL对应行',
                             required=True)

class profit_lins(models.Model):
    _name = 'profit.line'

    order_id = fields.Many2one('config.province', u'单位名称', index=True,
                               required=True, ondelete='cascade')
    update_name = fields.Char(u'上传名称',
                          required=True)
    excel_ncows = fields.Char(u'EXCEL对应列',
                          required=True)
    excel_ncols = fields.Char(u'EXCEL对应行',
                             required=True)

class partner(models.Model):
    _inherit = 'partner'
    computer_import = fields.Boolean(u'系统创建',default= False)

class goods(models.Model):
    _inherit = 'goods'
    computer_import = fields.Boolean(u'系统创建',default= False)