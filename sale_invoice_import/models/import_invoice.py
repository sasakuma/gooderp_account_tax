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
import odoo.addons.decimal_precision as dp
import xlrd
import base64
import datetime
import random
from odoo.exceptions import UserError, ValidationError

READONLY_STATES = {
        'to_delivery': [('readonly', True)],
        'done': [('readonly', True)],
    }

class sale_invoice(models.Model):
    '''金穗销售发票'''
    _name = 'sale.invoice'
    _order = "name"

    @api.one
    @api.depends('invoice_open_date')
    def _compute_period_id(self):
        self.name = self.env['finance.period'].get_period(self.invoice_open_date)

    @api.one
    @api.depends('line_ids.invoice_amount', 'line_ids.invoice_tax')
    def _compute_amount(self):
        amount = tax_amount = 0
        for line in self.line_ids:
            amount = amount +line.invoice_amount
            tax_amount = tax_amount +line.invoice_tax
        self.amount = amount
        self.tax_amount = tax_amount

    name = fields.Many2one(
        'finance.period',
        u'会计期间',
        compute='_compute_period_id', ondelete='restrict', store=True)
    line_ids = fields.One2many('sale.invoice.line', 'order_id', u'折旧明细行',
                               states=READONLY_STATES, copy=False)
    state = fields.Selection([('draft', u'草稿'),
                              ('to_delivery', u'待出库'),
                              ('done', u'已完成')], u'状态', default='draft')
    amount = fields.Float(string=u'合计金额', store=True, readonly=True,
                        compute='_compute_amount', track_visibility='always',
                        digits=dp.get_precision('Amount'))
    tax_amount = fields.Float(string=u'合计税额', store=True, readonly=True,
                        compute='_compute_amount', track_visibility='always',
                        digits=dp.get_precision('Amount'))
    invoice_code = fields.Char(u'发票代码', required=True,copy=False,states=READONLY_STATES)
    invoice_name = fields.Char(u'发票号码', required=True,copy=False,states=READONLY_STATES)
    partner_id = fields.Many2one('partner', u'客户',help=u'购买方',copy=False,states=READONLY_STATES)
    invoice_open_date = fields.Date(u'开票日期',required=True,copy=False,states=READONLY_STATES)
    sell_id = fields.Many2one('sell.order', u'销售订单号', copy=False, readonly=True,
                               ondelete='cascade',
                               help=u'产生的销货订单')

    _sql_constraints = [
        ('unique_code_name', 'unique (invoice_code,invoice_name)', u'发票代码+发票号码不能重复!'),
    ]

    @api.one
    def _wrong_done(self):
        if self.state == 'done':
            raise UserError(u'请不要重复审核！')
        if self.name.is_closed:
            raise UserError(u'该会计期间(%s)已结账！不能审核'%self.name.name)
        if self.amount <= 0:
            raise UserError(u'金额必须大于0！\n金额:%s'%self.amount)
        if self.tax_amount < 0:
            raise UserError(u'税额必须大于0！\n税额:%s'%self.tax_amount)
        return

    @api.one
    def sale_invoice_done(self):
        ''' 审核发票 '''
        self._wrong_done()
        # 系统创建的客户或产品不能审核
        if self.partner_id.computer_import:
            raise UserError(u'系统创建的客户不能审核！')
        for line in self.line_ids:
            if line.goods_id.computer_import:
                raise UserError(u'系统创建的产品不能审核！')
        #随机取0-15中整数，让订单日期在发票日期前15-30天内变化
        date = datetime.datetime.strptime(self.invoice_open_date,'%Y-%m-%d') - datetime.timedelta(days=random.randint(0,15)+15)
        sell_id = self.env['sell.order'].create({
                    'partner_id': self.partner_id.id,
                    'date':date,
                    'delivery_date': self.invoice_open_date,
                    'warehouse_id': self.env['warehouse'].search([('type', '=', 'stock')]).id,
                    })
        for line in self.line_ids:
            self.env['sell.order.line'].create({
                'goods_id':line.goods_id.id,
                'order_id':sell_id.id,
                'uom_id':line.uom_id.id,
                'quantity':line.quantity,
                'price':line.invoice_amount/line.quantity,
                'price_taxed':(line.invoice_amount+line.invoice_tax)/line.quantity,
                'amount':line.invoice_amount,
                'tax_rate':round(line.invoice_tax/line.invoice_amount*100,0),
                'tax_amount':line.invoice_tax,
            })
        self.sell_id = sell_id
        sell_id.sell_order_done()
        delivery_id = self.env['sell.delivery'].search([
                                    ('order_id', '=', sell_id.id)])
        delivery_id.sell_delivery_done()
        if delivery_id.state == 'done':
            invoice_id = self.env['money.invoice'].search([
                                    ('name', '=', delivery_id.name)])
            invoice_id.bill_number = self.invoice_name
            invoice_id.money_invoice_done()
            self.state = 'done'
        else:
            self.state = 'to_delivery'

    @api.one
    def sale_delivery_to_invoice(self):
        delivery_id = self.env['sell.delivery'].search([
                                    ('order_id', '=', self.sell_id.id)])
        delivery_id.sell_delivery_done()
        if delivery_id.state == 'done':
            invoice_id = self.env['money.invoice'].search([
                                    ('name', '=', delivery_id.name)])
            invoice_id.bill_number = self.invoice_name
            invoice_id.money_invoice_done()
            self.state = 'done'
        else:
            raise UserError(u'此发票出库数量不足。')

    @api.one
    def sale_invoice_draft(self):
        delivery_id = self.env['sell.delivery'].search([
                                    ('order_id', '=', self.sell_id.id)])
        if delivery_id.state == 'done':
            delivery_id.sell_delivery_draft()
        sell_id = self.sell_id
        sell_id.sell_order_draft()
        self.sell_id = False
        sell_id.unlink()
        self.state = 'draft'

class sale_invoice_line(models.Model):
    _name = 'sale.invoice.line'
    _description = u'导入销售发票明细'

    order_id = fields.Many2one('sale.invoice', u'订单编号', index=True,copy=False,
                               required=True, ondelete='cascade')
    invoice_amount = fields.Float(u'金额',
                                  required=True,
                                  copy=False,
                                  digits=dp.get_precision('Amount'))
    invoice_tax = fields.Float(u'税额',
                               required=True,
                               copy=False,
                               digits=dp.get_precision('Amount'))
    quantity = fields.Float(u'数量',
                            default=1,
                            required=True,
                            digits=dp.get_precision('Quantity'),
                            help=u'发票数量')
    uom_id = fields.Many2one('uom', u'单位', ondelete='restrict',
                             help=u'商品计量单位')
    goods_id = fields.Many2one('goods',
                               u'商品',
                               required=True,
                               ondelete='restrict',
                               help=u'商品')

class create_slae_invoice_wizard(models.TransientModel):
    '''导入金穗发票'''
    _name = 'create.sale.invoice.wizard'
    _description = 'Sale Invoice Import'

    excel = fields.Binary(u'导入金穗系统导出的excel文件',)
    excel_filename = fields.Char(u'文件名')

    @api.one
    def create_sale_invoice(self):
        """
        通过Excel文件导入信息到tax.invoice
        """
        xls_data = xlrd.open_workbook(
                file_contents=base64.decodestring(self.excel))
        table = xls_data.sheets()[0]
        #取得行数
        ncows = table.nrows
        ncols = table.ncols
        company_tax = table.cell(0,0).value
        if self.env.user.company_id.tax_number != str(company_tax):
            raise UserError(u'不是同一公司不可以导入！')
        #取得第6行数据
        colnames =  table.row_values(5)
        list =[]
        newcows = 0
        for rownum in range(6,ncows):
            row = table.row_values(rownum)
            if row:
                app = {}
                for i in range(len(colnames)):
                   app[colnames[i]] = row[i]
                if app.get(u'税率') and app.get(u'税率')!=u'税率':
                    list.append(app)
                    newcows += 1
        #数据读入，检测是否需要新增。
        for data in range(0,newcows):
            in_xls_data = list[data]
            #无客户则新增客户，创建销售发票
            if in_xls_data.get(u'购方税号'):
                partner_id = self.env['partner'].search([
                                 ('tax_num', '=', in_xls_data.get(u'购方税号'))])
                partner_name = self.env['partner'].search([
                                 ('name', '=', in_xls_data.get(u'购方企业名称'))])
                if partner_name and not partner_id:
                    raise UserError(u'此客户(%s)未设置税号请补全'%partner_name.name)
                if not partner_id:
                    partner_id = self.env['partner'].create({
                        'name': in_xls_data.get(u'购方企业名称'),
                        'main_mobile': in_xls_data.get(u'地址电话')or in_xls_data.get(u'购方税号'),
                        'tax_num': in_xls_data.get(u'购方税号'),
                        'c_category_id':self.env['core.category'].search([
                                     '&',('type', '=', 'customer'),('note', '=', u'默认客户类别')]).id,
                        'computer_import':True
                    })
                invoice_id = self.env['sale.invoice'].create({
                        'invoice_code': in_xls_data.get(u'发票代码'),
                        'invoice_name': in_xls_data.get(u'发票号码'),
                        'partner_id': partner_id.id,
                        'invoice_open_date': self.excel_date(in_xls_data.get(u'开票日期')),
                        'state':'draft'
                    })

            #新增单位
            if in_xls_data.get(u'单位'):
                uom_id = self.env['uom'].search([
                                 ('name', '=', in_xls_data.get(u'单位'))])
            if not uom_id:
                uom_id = self.env['uom'].create({
                    'name': in_xls_data.get(u'单位'),
                    'active': 1
                })
            #新增商品
            if in_xls_data.get(u'商品名称'):
                goods = self.env['goods'].search([
                                 ('name', '=', in_xls_data.get(u'商品名称'))])
            if not goods:
                goods = self.env['goods'].create({
                    'name': in_xls_data.get(u'商品名称'),
                    'uom_id': self.env['uom'].search([
                                 ('name', '=', in_xls_data.get(u'单位'))]).id,
                    'uos_id': self.env['uom'].search([
                                 ('name', '=', in_xls_data.get(u'单位'))]).id,
                    #'tax_rate': float(in_xls_data.get(u'税率')),
                    'category_id':self.env['core.category'].search([
                                 '&',('type', '=', 'goods'),('note', '=', u'默认商品类别')]).id,
                    'computer_import':True
                })

            self.env['sale.invoice.line'].create({
                    'goods_id': goods.id,
                    'quantity': str(in_xls_data.get(u'数量')),
                    'invoice_amount':str(in_xls_data.get(u'金额')),
                    'invoice_tax':str(in_xls_data.get(u'税额')),
                    'uom_id':uom_id.id,
                    'order_id':invoice_id.id,
                    })

    def excel_date(self,data):
        #将excel日期改为正常日期
        if type(data) in (int,float):
            year, month, day, hour, minute, second = xlrd.xldate_as_tuple(data,0)
            py_date = datetime.datetime(year, month, day, hour, minute, second)
        else:
            py_date = data
        return py_date


