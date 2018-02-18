# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2016  德清武康开源软件().
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
import odoo.addons.decimal_precision as dp
import xlrd
import base64
import datetime

READONLY_STATES = {
        'done': [('readonly', True)],
    }

ORDER_TYPE = [('get_order', u'收款单'),
              ('pay_order', u'付款单'),
              ('transfer_order', u'资金转帐单'),
              ('other_get', u'其他收入单'),
              ('other_pay', u'其他支出单')]


class bank_import(models.Model):
    _name = 'bank.import'
    _description = u'银行明细帐单'
    _rec_name = 'name'

    bank_id = fields.Many2one('bank.account', u'银行帐号',help=u'供应商',copy=False)
    name = fields.Many2one(
        'finance.period',
        u'会计期间',
        ondelete='restrict',
        required=True,
        states=READONLY_STATES)
    line_ids = fields.One2many('bank.import.line', 'order_id', u'银行交易明细',
                               states=READONLY_STATES, copy=False)
    state = fields.Selection([('draft', u'草稿'),
                              ('done', u'已结束')], u'状态', default='draft')

    # 引入EXCEL的wizard的button
    @api.multi
    def button_excel(self):
        return {
            'name': u'引入excel',
            'view_mode': 'form',
            'view_type': 'form',
            'res_model': 'create.bank.import.line.wizard',
            'type': 'ir.actions.act_window',
            'target': 'new',
        }

    def to_money_order(self):
        app = []
        for i in self.line_ids:
            #建收款单
            if i.select_order == 'get_order' and not i.is_right:
                #因系统同一客户不能建二张收付款单，故跳过~
                if i.partner_id.id in app:
                    continue
                amount = i.credit_amount or 0-i.debit_amount
                order_id = self.env['money.order'].create({
                    'date':i.transaction_date,
                    'partner_id':i.partner_id.id,
                    'type':'get',})
                self.env['money.order.line'].create({
                    'money_id': order_id.id,
                    'bank_id': self.bank_id.id,
                    'amount': amount,
                    'note': i.note,
                })
                app.append(i.partner_id.id)
                i.is_right = True
            #进付款单
            if i.select_order == 'pay_order' and not i.is_right:
                # 因系统同一客户不能建二张收付款单，故跳过~
                if i.partner_id.id in app:
                    continue
                amount = i.debit_amount or 0 - i.credit_amount
                order_id = self.env['money.order'].create({
                    'date': i.transaction_date,
                    'partner_id': i.partner_id.id,
                    'type': 'pay', })
                self.env['money.order.line'].create({
                    'money_id': order_id.id,
                    'bank_id': self.bank_id.id,
                    'amount': amount,
                    'note': i.note,
                })
                app.append(i.partner_id.id)
                i.is_right = True
            if i.select_order == 'transfer_order' and not i.is_right:
                amount = i.debit_amount or 0 - i.credit_amount
                out_bank_id = self.bank_id
                in_bank_id = self.env['bank.account'].search([('bank_num', '=', i.account_number)])
                order_id = self.env['money.transfer.order'].create({
                    'date': i.transaction_date,
                     })
                self.env['money.transfer.order.line'].create({
                    'transfer_id': order_id.id,
                    'out_bank_id': out_bank_id.id,
                    'in_bank_id': in_bank_id.id,
                    'amount': amount,
                    'note': i.note,
                })
                app.append(i.partner_id.id)
                i.is_right = True
            if i.select_order == 'other_get' and not i.is_right:
                category_id = self.get_category_id(i.note)
                amount = i.debit_amount or 0 - i.credit_amount
                order_id = self.env['other.money.order'].create({
                    'date': i.transaction_date,
                    'bank_id': self.bank_id.id,
                    'type': 'other_get',
                })
                self.env['other.money.order.line'].create({
                    'other_money_id': order_id.id,
                    'category_id': category_id and category_id.id or '',
                    'amount': amount,
                    'note': i.note,
                })

            if i.select_order == 'other_pay':
                category_id = self.get_category_id(i.note)
                amount = i.debit_amount or 0 - i.credit_amount
                order_id = self.env['other.money.order'].create({
                    'date': i.transaction_date,
                    'bank_id': self.bank_id.id,
                    'type': 'other_pay',
                })
                self.env['other.money.order.line'].create({
                    'other_money_id': order_id.id,
                    'category_id': category_id and category_id.id or '',
                    'amount': amount,
                    'note': i.note,
                })
        #self.state = 'done'
    def get_category_id(self, note):
        category = self.env['automatic.cost'].search([])
        for i in category:
            if i.name in note:
                category_id = i.category_id
        return category_id

class bank_import_line(models.Model):
    _name = 'bank.import.line'
    _description = u'银行明细帐单'
    _rec_name = 'transaction_date'

    order_id = fields.Many2one('bank.import', u'订单编号', index=True, copy=False,
                               required=True, ondelete='cascade')
    account_number = fields.Char(u'对方账号', copy=False)
    account_name = fields.Char(u'对方户名', copy=False)
    partner_id = fields.Many2one('partner', u'合作伙伴',help=u'供应商或客户',copy=False)
    transaction_date = fields.Date(u'交易时间', required=True, copy=False)
    note = fields.Char(u'摘要', copy=False)
    is_right = fields.Boolean(u'已记帐')
    debit_amount = fields.Float(u'借方金额', copy=False)
    credit_amount = fields.Float(u'贷方金额', copy=False)
    select_order = fields.Selection(ORDER_TYPE, u'生成单据类型')

#用excel导入认证系统的EXCEL生成月认证发票
class create_bank_import_line_wizard(models.TransientModel):
    _name = 'create.bank.import.line.wizard'
    _description = 'Bank Line Import'

    excel = fields.Binary(u'导入认证系统导出的excel文件',)

    def create_bank_import_line(self):
        """
        注意：银行的贷方是我们的借方（收款）
              银行的借方是我们的贷方（付款）
        """
        if not self.env.context.get('active_id'):
            return
        bank_import = self.env['bank.import'].browse(self.env.context.get('active_id'))
        """
        通过Excel文件导入信息到tax.invoice.line
        """
        if not bank_import:
            return {}
        xls_data = xlrd.open_workbook(file_contents=base64.decodestring(self.excel))
        table = xls_data.sheets()[0]
        ncows = table.nrows
        ncols = 0
        colnames =  table.row_values(1)
        list =[]
        #数据读入，过滤没有开票日期的行
        for rownum in range(2,ncows):
            row = table.row_values(rownum)
            if row:
                app = {}
                for i in range(len(colnames)):
                   app[colnames[i]] = row[i]
                if app.get(u'交易时间'):
                    list.append(app)
                    ncols += 1

        #数据处理
        in_xls_data = {}
        for data in range(0,ncols):
            in_xls_data = list[data]
            partner_name = in_xls_data.get(u'对方单位') or in_xls_data.get(u'对方户名')
            partner_name = partner_name.replace(' ','')
            if in_xls_data.get(u'对方账号'):
                partner_id = self.env['partner'].search([
                                 ('bank_num', '=', in_xls_data.get(u'对方账号'))])
            else:
                partner_id = self.env['partner'].search([
                                 ('name', '=', partner_name)])

            if partner_name and not partner_id:
                partner_id = self.create_partner(in_xls_data)
            select_order = ''
            if partner_id:
                if partner_id.c_category_id:
                    select_order = 'get_order'
                if partner_id.s_category_id:
                    select_order = 'pay_order'
            '''
            our_bank = self.env['bank.account'].search([('bank_num', '=', in_xls_data.get(u'对方账号'))])
            if our_bank:
                select_order = 'transfer_order'
            '''
            print select_order
            self.env['bank.import.line'].create({
                'order_id':bank_import.id,
                'partner_id':partner_id and partner_id.id or '',
                'account_number':in_xls_data.get(u'对方账号'),
                'account_name': partner_name,
                'transaction_date': self.excel_date(in_xls_data.get(u'交易时间')),
                'note': in_xls_data.get(u'摘要'),
                'is_right': False,
                'debit_amount': float((in_xls_data.get(u'转入金额') or in_xls_data.get(u'借方发生额')).replace(',','')),
                'credit_amount': float((in_xls_data.get(u'转出金额') or in_xls_data.get(u'贷方发生额')).replace(',','')),
                'select_order': select_order,
                })

    def excel_date(self,data):
        #将excel日期改为正常日期
        if type(data) in (int,float):
            year, month, day, hour, minute, second = xlrd.xldate_as_tuple(data,0)
            py_date = datetime.datetime(year, month, day, hour, minute, second)
        else:
            py_date = data
        return py_date

    def create_partner(self, in_xls_data):
        debit_amount = float((in_xls_data.get(u'转入金额') or in_xls_data.get(u'借方发生额')).replace(',',''))
        credit_amount  = float((in_xls_data.get(u'转出金额') or in_xls_data.get(u'贷方发生额')).replace(',',''))
        partner_name = in_xls_data.get(u'对方单位') or in_xls_data.get(u'对方户名')
        if partner_name:
            #TODO 增加判断依據可配置
            if u'利息' in partner_name:
                return
            if debit_amount > 1:
                partner_id = self.env['partner'].create({
                    'name': partner_name,
                    'main_mobile': '',
                    'bank_num': in_xls_data.get(u'对方账号'),
                    's_category_id': self.env['core.category'].search([
                        '&', ('type', '=', 'supplier'), ('note', '=', u'默认供应商类别')]).id,
                    'computer_import': True,
                })
            if credit_amount > 1:
                partner_id = self.env['partner'].create({
                    'name': partner_name,
                    'main_mobile': '',
                    'bank_num': in_xls_data.get(u'对方账号'),
                    'c_category_id': self.env['core.category'].search([
                        '&', ('type', '=', 'customer'), ('note', '=', u'默认客户类别')]).id,
                    'computer_import': True
                })

        return partner_id