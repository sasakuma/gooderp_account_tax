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
import time
import random
import re
from PIL import Image
from selenium import webdriver
from selenium.webdriver.common.keys import Keys


# 字段只读状态
READONLY_STATES = {
        'done': [('readonly', True)],
    }

#初始化chrome
#options = webdriver.ChromeOptions()
#options.add_argument('--explicitly-allowed-ports=6000,556')

#加载插件
#profile=webdriver.FirefoxProfile()
#profile.add_extension('c:\\firebug-2.0.8-fx.xpi')
#激活插件
#profile.set_preference("extensions.firebug.allPagesActivation", "on")
firefox_path = r"C:\Program Files (x86)\Mozilla Firefox\geckodriver.exe"
browser = False

#每月进项发票
class tax_invoice(models.Model):
    _name = 'tax.invoice'
    _order = "name"
    name = fields.Many2one(
        'finance.period',
        u'会计期间',
        ondelete='restrict',
        required=True,
        states=READONLY_STATES)
    line_ids = fields.One2many('tax.invoice.line', 'order_id', u'明细发票行',
                               states=READONLY_STATES, copy=False)
    state = fields.Selection([('draft', u'草稿'),
                              ('done', u'已结束')], u'状态', default='draft')
    tax_amount = fields.Float(string=u'合计可抵扣税额', store=True, readonly=True,
                        compute='_compute_tax_amount', track_visibility='always',
                        digits=dp.get_precision('Amount'))

    @api.one
    @api.depends('line_ids.invoice_tax', 'line_ids.is_deductible')
    def _compute_tax_amount(self):
        '''当明细行的税额或是否抵扣改变时，改变可抵扣税额合计'''
        total = 0
        for line in self.line_ids:
            if line.is_deductible:
                total = total + 0
            else:
                total = total +line.invoice_tax
        self.tax_amount = total

    #由发票生成采购订单
    @api.one
    def invoice_to_buy(self):
        for i in self.line_ids:
            if i.is_verified and not i.buy_id:
                i.to_buy()

    #结束本期发票，然后确认money_invoice
    @api.one
    def tax_invoice_done(self):
        res = {}
        for line in self.line_ids:
            if not line.partner_id:
                raise UserError(u'税号%s没找到到供应商，请去供应商处维护！'%line.partner_code)
            if not line.is_verified:
                raise UserError(u'发票%s未核验，请核验！'%line.invoice_name)
            if not line.money_invoice_ids:
                raise UserError(u'%s的认证发票%s未与系统相关联请关联'%(line.partner_id.name,line.invoice_name))
            amount = line.invoice_amount
            tax = line.invoice_tax
            total = amount + tax
            '''如果有多条money，则表明是1张发票对应多次送货，否则是一次送货有多张发票，混起来没有办法处理。
            多条money对应一张发票，需要在money中填写发票号码'''
            if len(line.money_invoice_ids) == 1:
                money_invoice_id = line.money_invoice_ids
                if money_invoice_id.id not in res:
                    res[money_invoice_id.id] = {'amount': 0,'tax': 0,'total': 0,}
                val = res[money_invoice_id.id]
                #如果不抵扣则税额加到金额中去
                if line.is_deductible:
                    val.update({'amount': val.get('amount') + amount + tax,
                        'tax': val.get('tax'),
                        'total': val.get('total') + total,
                        })
                else:
                    val.update({'amount': val.get('amount') + amount,
                        'tax': val.get('tax') + tax,
                        'total': val.get('total') + total,
                        })
            else:
                order_amount = sum(money_invoice_id.amount for money_invoice_id in line.money_invoice_ids)
                order_tax = sum(money_invoice_id.tax_amount for money_invoice_id in line.money_invoice_ids)
                if total != order_amount:
                    raise UserError(u'%s的认证发票%s未与系统的结算单总金额不一致'%(total,order_amount))
                if tax != order_tax:
                    line.money_invoice_ids[0].tax_amount -= (tax - order_tax)

                for line in line.money_invoice_ids:
                    line.money_invoice_done()

        for money_invoice_ids,val in res.iteritems():
            money_id = self.env['money.invoice'].search([
                                    ('id', '=', money_invoice_ids),])
            if round(val.get('total'),2) != round(money_id.amount,2):
                raise UserError(u'%s的认证发票%s未与系统的结算单总金额不一致'%(total,money_id.amount))
            if round(val.get('tax'),2) != round(money_id.tax_amount,2):
                money_id.tax_amount = val.get('tax')
            money_id.money_invoice_done()
        self.state = 'done'
        self.create_input_structure()

    #引入EXCEL的wizard的button
    @api.multi
    def button_excel(self):
        return {
            'name': u'引入excel',
            'view_mode': 'form',
            'view_type': 'form',
            'res_model': 'create.invoice.line.wizard',
            'type': 'ir.actions.act_window',
            'target': 'new',
        }

    #在money_invoice上已经写了是哪几张发票的明细进行匹配发票
    @api.one
    def tax_invoice_money(self):
        money_ids = self.env['money.invoice'].search([
        ('tax_invoice_date', '=', False),
        ('bill_number', '!=', False),])
        for money in money_ids:
            if "-" in money.bill_number:
                if ',' in money.bill_number:
                    money.tax_invoice_date = self.many2_money_to_invoice(money)
                else:
                    money.tax_invoice_date = self.many_money_to_invoice(money,money.bill_number)
            else :
                money.tax_invoice_date = self.money_to_invoice(money)

        ''' 发票匹配money_invoice，减化操作'''
        for line in self.line_ids:
            if not line.money_invoice_ids:
                self.invoice_to_money(line)

    def invoice_to_money(self,line):
        line_amount = line.invoice_amount + line.invoice_tax
        money_ids = self.env['money.invoice'].search([
        ('tax_invoice_date', '=', False),
        ('partner_id', '=', line.partner_id.id),
        ('bill_number', '=', False),])
        for ids in money_ids:
            if ids.category_id.type != 'expense':
                continue
            if round(ids.amount,2) == round(line_amount,2):
                ids.bill_number = line.invoice_name
                ids.tax_invoice_date = line.invoice_confim_date
                line.money_invoice_ids = [(4, ids.id)]

    def many2_money_to_invoice(self,money):
        # 当有"-"加","在里面时，先需要将，等分开。
        money_ids = money.bill_number.split(',')
        for ids in money_ids:
            if "-" in ids:
                confim_date = self.many_money_to_invoice(money,ids)
            else:
                self.money_to_invoice(money)
        return confim_date

    def many_money_to_invoice(self,money,bill_number):
        # 当有-在里面时，有可能这个发票号码给隐藏在-中了。
        money_ids = bill_number.split('-')
        invoice_number = []
        before_number = long(money_ids[0])
        while before_number <= int(money_ids[1]):
            invoice_number += [before_number]
            before_number += 1
        for line in self.line_ids:
            if long(line.invoice_name) in invoice_number:
                line.money_invoice_ids = [(4, money.id)]
        return line.invoice_confim_date

    def money_to_invoice(self,money):
        for line in self.line_ids:
            if line.invoice_name in money.bill_number:
                line.money_invoice_ids = [(4, money.id)]
        return line.invoice_confim_date

    @api.one
    def tax_invoice_draft(self):
        self.state = 'draft'
#结算单增加认证日期
class money_invoice(models.Model):
    _inherit = 'money.invoice'
    tax_invoice_date = fields.Date(string=u'认证日期',
                           help=u'发票认证的日期')
#每月进项明细发票
class tax_invoice_line(models.Model):
    _name = 'tax.invoice.line'
    _description = u'认证发票明细'
    _rec_name='invoice_name'

    partner_code = fields.Char(u'供应商税号',copy=False)
    partner_id = fields.Many2one('partner', u'供应商',help=u'供应商',copy=False)
    invoice_code = fields.Char(u'发票代码', required=True,copy=False)
    invoice_name = fields.Char(u'发票号码', required=True,copy=False)
    invoice_amount = fields.Float(u'金额', required=True,copy=False)
    invoice_tax = fields.Float(u'税额', required=True,copy=False)
    invoice_open_date = fields.Date(u'开票日期',required=True,copy=False)
    invoice_confim_date = fields.Date(u'认证日期',required=True,copy=False)
    tax_rate = fields.Float(u'税率',digits=(12, 0),copy=False)
    is_deductible = fields.Boolean(u'是否抵扣')
    order_id = fields.Many2one('tax.invoice', u'订单编号', index=True,copy=False,
                               required=True, ondelete='cascade')
    money_invoice_ids = fields.Many2many('money.invoice',
                                   'invoice_verification',
                                   'money_ids',
                                   'tax_invoice_ids',
                                    u'结算单与认证发票的关系',copy=False)
    is_verified = fields.Boolean(u'已核验')
    invoice_line_detail=fields.One2many('tax.invoice.line.detail', 'line_id', u'发票明细行',
                               copy=False)
    buy_id = fields.Many2one('buy.order', u'采购订单号', copy=False, readonly=True,
                             ondelete='cascade',
                             help=u'产生的采购订单')
    image = fields.Binary(u'图片', attachment=True)
    img_note = fields.Char(u"填写要求")
    img_code = fields.Char(u'验证码')

    _sql_constraints = [
        ('unique_start_date', 'unique (invoice_code, invoice_name)', u'发票代码+发票号码不能相同!'),
    ]

    # 新增UOM
    def Adduom(self,uom):
        uom_id = ''
        if uom:
            uom_id = self.env['uom'].search([('name', '=', uom)])
            if not uom_id:
                uom_id = self.env['uom'].create({
                    'name': uom,
                    'active': 1})
        return uom_id

    #新增产品
    def Addgoods(self, goods_name,uom_id):
        print '1'
        goods_id = self.env['goods'].search([('name', '=', goods_name)])
        if not goods_id:
            self.env['goods'].create({
                'name': goods_name,
                'uom_id': uom_id and uom_id.id or '',
                'uos_id': uom_id and uom_id.id or '',
                # 'tax_rate': float(in_xls_data.get(u'税率')),
                'category_id': self.env['core.category'].search([
                    '&', ('type', '=', 'goods'), ('note', '=', u'默认采购商品类别')]).id,
                'computer_import': True,
                'cost_method':'average',
            })
        print goods_id

    #取验证码
    def get_img_code(self):
        global browser
        if not browser:
            browser = webdriver.Firefox(executable_path=firefox_path)
            browser.maximize_window()
        url = "https://inv-veri.chinatax.gov.cn/"
        browser.get(url)
        date = self.invoice_open_date.replace('-','')
        browser.find_element_by_id("fpdm").send_keys(self.invoice_code)
        browser.find_element_by_id("fphm").send_keys(self.invoice_name)
        date_in = browser.find_element_by_id("kprq")
        date_in.clear()
        date_in.send_keys(date)
        browser.find_element_by_id("kjje").send_keys(str(self.invoice_amount))
        time.sleep(2)
        #取图片
        imgelement = browser.find_element_by_id("yzm_img")
        img_code = imgelement.get_attribute('src')[22:]
        #取图片说明
        img_note = browser.find_element_by_id("yzminfo").text
        self.write({'image': img_code,'img_note':img_note})
    #传验证码取得明细
    def to_verified(self):
        if not browser:
            raise UserError(u'请重新取验证码')
        yzm = browser.find_element_by_id("yzm")
        yzm.clear()
        yzm.send_keys(self.img_code)
        button = browser.find_element_by_id("checkfp")
        button.click()
        time.sleep(6)
        #如果有JS弹出窗，则由gooderp返回给用户
        try:
            browser.find_element_by_id("bg_div")
        except:
            alert = browser.switch_to_alert()
            text = browser.find_element_by_id("popup_message").text
            raise UserError(u'提示！%s' % text)
            text.accept()
        # 删除旧数据
        if self.invoice_line_detail:
            self.invoice_line_detail.unlink()
        try:
            '''
            zf = browser.find_element_by_id("icon_zf")
            if zf:
                self.write({'is_deductible': 1, 'is_verified': 1})
                return
            '''
            #有清单
            button_mx = browser.find_element_by_id("showmx")
            button_mx.click()
            time.sleep(6)
            tr_line = browser.find_elements_by_xpath("//tr [@id='tab_head_mx']/../tr")
            for tr in tr_line[1:-3]:
                # 将每一个tr的数据根据td查询出来，返回结果为list对象,第一行和最后三行不要
                table_td_list = tr.find_elements_by_tag_name("td")
                row_list = []
                for td in table_td_list:  # 遍历每一个td
                    row_list.append(td.text)  # 取出表格的数据，并放入行列表里
                goods_name = row_list[1].split('*')[-1]
                self.env['tax.invoice.line.detail'].create({
                    'line_id':self.id,
                    'product_name': goods_name,
                    'product_type': row_list[2] or '',
                    'product_unit': row_list[-6] or '',
                    'product_count': row_list[-5] or '',
                    'product_price': row_list[-4] or '',
                    'product_amount': row_list[-3] or '0',
                    'product_tax_rate':row_list[-2].replace('%','') or '0',
                    'product_tax': row_list[-1] or '0',
                })
                # 新增计量单位
                uom = self.Adduom(row_list[-6])
                # 新增商品单位
                self.Addgoods( goods_name,uom)

        except:
            #无清单
            tr_line = browser.find_elements_by_xpath("//tr [@id='tab_head_zp']/../tr")
            for tr in tr_line[1:-2]:
                # 将每一个tr的数据根据td查询出来，返回结果为list对象,第一行和最后二行不要
                table_td_list = tr.find_elements_by_tag_name("td")
                row_list = []
                # 新增商品单位
                for td in table_td_list:  # 遍历每一个td
                    row_list.append(td.text)  # 取出表格的数据，并放入行列表里
                # 新增计量单位
                uom = self.Adduom(row_list[-6])
                if uom:
                    goods_name = row_list[0].split('*')[-1]
                    self.Addgoods(goods_name, uom)
                self.env['tax.invoice.line.detail'].create({
                    'line_id':self.id,
                    'product_name': goods_name,
                    'product_type': row_list[1] or '',
                    'product_unit': row_list[-6] or '',
                    'product_count': row_list[-5] or '',
                    'product_price': row_list[-4] or '',
                    'product_amount': row_list[-3] or '0',
                    'product_tax_rate':row_list[-2].replace('%',''),
                    'product_tax': row_list[-1] or '0',
                })

        self.write({'is_verified': 1})
        browser.close()
        global browser
        browser = False

    def to_buy(self):
        ''' 系统创建的客户或产品不能审核
        if self.partner_id.computer_import:
            raise UserError(u'系统创建的客户不能审核！')
        for line in self.line_ids:
            if line.goods_id.computer_import:
                raise UserError(u'系统创建的产品不能审核！')
        '''
        if self.partner_id.s_category_id.note == u'默认供应商类别':
            # 随机取0-15中整数，让订单日期在发票日期前20-35天内变化
            date = datetime.datetime.strptime(self.invoice_open_date, '%Y-%m-%d') - datetime.timedelta(days = random.randint(0, 15) + 20)
            buy_id = self.env['buy.order'].create({
                'partner_id': self.partner_id.id,
                'date': date,
                'planned_date': self.invoice_confim_date,
                'warehouse_dest_id': self.env['warehouse'].search([('type', '=', 'stock')]).id,
            })
            if self.invoice_line_detail:
                for lines in self.invoice_line_detail:
                    goods_id = self.env['goods'].search([('name', '=', lines.product_name)])
                    if not goods_id:
                        continue
                    self.env['buy.order.line'].create({
                        'goods_id': goods_id.id,
                        'order_id': buy_id.id,
                        'uom_id': goods_id.uom_id.id,
                        'quantity': lines.product_count,
                        'price': lines.product_price,
                        'price_taxed': round(lines.product_price * (1 + lines.product_tax_rate / 100), 2),
                        'amount': lines.product_amount,
                        'tax_rate': lines.product_tax_rate,
                        'tax_amount': lines.product_tax,
                    })
                self.buy_id = buy_id
                buy_id.buy_order_done()
                delivery_id = self.env['buy.receipt'].search([
                    ('order_id', '=', buy_id.id)])
                delivery_id.buy_receipt_done()
                invoice_id = self.env['money.invoice'].search([
                    ('name', '=', delivery_id.name)])
                invoice_id.bill_number = self.invoice_name
        else:
            #todo 跟据采购服务的商品名称来生成服务供应发票
            pass
#定意发票明细行
class tax_invoice_line_detail(models.Model):
    _name = 'tax.invoice.line.detail'
    _description = u'认证发票明细行'
    _rec_name='product_name'

    line_id = fields.Many2one('tax.invoice.line', u'认证发票明细',help=u'认证发票明细',copy=False)
    product_name = fields.Char(u"货物名称")
    product_type = fields.Char(u"规格型号")
    product_unit = fields.Char(u"单位")
    product_count = fields.Float(u"数量")
    product_price = fields.Float(u"价格")
    product_amount = fields.Float(u"金额")
    product_tax_rate = fields.Float(u"税率")
    product_tax = fields.Float(u"税额")
#用excel导入认证系统的EXCEL生成月认证发票
class create_invoice_line_wizard(models.TransientModel):
    _name = 'create.invoice.line.wizard'
    _description = 'Tax Invoice Import'

    excel = fields.Binary(u'导入认证系统导出的excel文件',)

    def create_invoice_line(self):
        if not self.env.context.get('active_id'):
            return
        invoice_id = self.env['tax.invoice'].browse(self.env.context.get('active_id'))
        """
        通过Excel文件导入信息到tax.invoice.line
        """
        tax_invoice = self.env['tax.invoice'].browse(self.env.context.get('active_id'))
        if not tax_invoice:
            return {}
        xls_data = xlrd.open_workbook(file_contents=base64.decodestring(self.excel))
        table = xls_data.sheets()[0]
        ncows = table.nrows
        ncols = 0
        colnames =  table.row_values(0)
        list =[]
        #数据读入，过滤没有开票日期的行
        for rownum in range(1,ncows):
            row = table.row_values(rownum)
            if row:
                app = {}
                for i in range(len(colnames)):
                   app[colnames[i]] = row[i]
                if app.get(u'开票日期'):
                    list.append(app)
                    ncols += 1

        #数据处理
        in_xls_data = {}
        for data in range(0,ncols):
            in_xls_data = list[data]
            if in_xls_data.get(u'销方税号'):
                partner_id = self.env['partner'].search([
                                 ('tax_num', '=', in_xls_data.get(u'销方税号'))])
            else:
                partner_id = self.env['partner'].search([
                                 ('name', '=', in_xls_data.get(u'销方名称'))])
            is_verified = True
            if in_xls_data.get(u'发票代码'):
                code = str(in_xls_data.get(u'发票代码'))
                if len(code) == 10:
                    b = code[7:8]
                    if b == '1' or b == '5':
                        is_verified = False
            #按税率增加新加供应商
            tax_rate = float(in_xls_data.get(u'税额'))/float(in_xls_data.get(u'金额'))*100
            if 15 < tax_rate < 18:
                cailou_partner = 1
            else:
                cailou_partner = 0
            if not partner_id.id :
                #17%为原材料供应商，非为服务供应商
                if cailou_partner:
                    partner_id = self.env['partner'].create({
                        'name': in_xls_data.get(u'销方名称'),
                        'main_mobile': in_xls_data.get(u'销方税号'),
                        'tax_num': in_xls_data.get(u'销方税号'),
                        's_category_id': self.env['core.category'].search([
                            '&', ('type', '=', 'supplier'), ('note', '=', u'默认供应商类别')]).id,
                        'computer_import': True,
                    })
                else:
                    partner_id = self.env['partner'].create({
                        'name': in_xls_data.get(u'销方名称'),
                        'main_mobile': in_xls_data.get(u'销方税号'),
                        'tax_num': in_xls_data.get(u'销方税号'),
                        's_category_id': self.env['core.category'].search([
                            '&', ('type', '=', 'supplier'), ('note', '=', u'默认服务供应商类别')]).id,
                        'computer_import': True,
                    })

            self.env['tax.invoice.line'].create({
                'partner_code': str(in_xls_data.get(u'销方税号')),
                'partner_id': partner_id.id or '',
                'invoice_code': str(in_xls_data.get(u'发票代码')),
                'invoice_name': str(in_xls_data.get(u'发票号码')),
                'invoice_amount': float(in_xls_data.get(u'金额')),
                'invoice_tax': float(in_xls_data.get(u'税额')),
                'invoice_open_date': self.excel_date(in_xls_data.get(u'开票日期')),
                'invoice_confim_date': self.excel_date(in_xls_data.get(u'认证时间') or in_xls_data.get(u'确认时间')),
                'order_id':invoice_id.id or '',
                'tax_rate':float(in_xls_data.get(u'税额'))/float(in_xls_data.get(u'金额'))*100,
                'is_verified': is_verified or False,
                })

    def excel_date(self,data):
        #将excel日期改为正常日期
        if type(data) in (int,float):
            year, month, day, hour, minute, second = xlrd.xldate_as_tuple(data,0)
            py_date = datetime.datetime(year, month, day, hour, minute, second)
        else:
            py_date = data
        return py_date