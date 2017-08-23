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
import odoo.addons.decimal_precision as dp
import xlrd
import base64
import datetime
import time
import re

from selenium import webdriver
from selenium.webdriver.common.keys import Keys

# 字段只读状态
READONLY_STATES = {
        'done': [('readonly', True)],
    }

TAX_TYPE = [('17', u'17%税率'),
            ('13', u'13%税率'),
            ('11', u'11%税率'),
            ('6', u'6%税率'),
            ('5', u'5%税率'),
            ('3', u'3%税率'),
            ('1.5', u'1.5%税率'),]

#初始化chrome
options = webdriver.ChromeOptions()
options.add_argument('--explicitly-allowed-ports=6000,556')

class tax_invoice(models.Model):
    '''税务发票'''
    _name = 'tax.invoice'
    _order = "name"

    name = fields.Many2one(
        'finance.period',
        u'会计期间',
        ondelete='restrict',
        required=True,
        states=READONLY_STATES)
    line_ids = fields.One2many('tax.invoice.line', 'order_id', u'折旧明细行',
                               states=READONLY_STATES, copy=False)
    state = fields.Selection([('draft', u'草稿'),
                              ('done', u'已结束')], u'状态', default='draft')
    tax_amount = fields.Float(string=u'合计可抵扣税额', store=True, readonly=True,
                        compute='_compute_tax_amount', track_visibility='always',
                        digits=dp.get_precision('Amount'))
    tax_17 = fields.Float(u'17%的进项',readonly=True,copy=False)
    tax_13 = fields.Float(u'13%的进项',readonly=True,copy=False)
    tax_11 = fields.Float(u'11%的进项',readonly=True,copy=False)
    tax_6 = fields.Float(u'6%的进项',readonly=True,copy=False)
    tax_5 = fields.Float(u'5%的进项',readonly=True,copy=False)
    tax_3 = fields.Float(u'3%的进项',readonly=True,copy=False)
    tax_1_5 = fields.Float(u'1.5%的进项',readonly=True,copy=False)
    tax1 = fields.Float(u'17%有形动产租赁的进项',readonly=True,copy=False)
    tax2 = fields.Float(u'11%运输服务的进项',readonly=True,copy=False)
    tax3 = fields.Float(u'11%电信服务的进项',readonly=True,copy=False)
    tax4 = fields.Float(u'11%建筑安装服务的进项',readonly=True,copy=False)
    tax5 = fields.Float(u'11%不动产租赁服务的进项',readonly=True,copy=False)
    tax6 = fields.Float(u'11%受让土地使用权的进项',readonly=True,copy=False)
    tax7 = fields.Float(u'6%电信服务的进项',readonly=True,copy=False)
    tax8 = fields.Float(u'6%金融保险服务的进项',readonly=True,copy=False)
    tax9 = fields.Float(u'6%生活服务的进项',readonly=True,copy=False)
    tax10 = fields.Float(u'6%取得无形资产的进项',readonly=True,copy=False)
    tax11 = fields.Float(u'5%不动产租赁服务的进项',readonly=True,copy=False)
    tax12 = fields.Float(u'3%货物及加工、修理修配劳务的进项',readonly=True,copy=False)
    tax13 = fields.Float(u'3%运输服务的进项',readonly=True,copy=False)
    tax14 = fields.Float(u'3%电信服务的进项',readonly=True,copy=False)
    tax15 = fields.Float(u'3%建筑安装服务的进项',readonly=True,copy=False)
    tax16 = fields.Float(u'3%金融保险服务的进项',readonly=True,copy=False)
    tax17 = fields.Float(u'3%有形动产租赁服务的进项',readonly=True,copy=False)
    tax18 = fields.Float(u'3%生活服务的进项',readonly=True,copy=False)
    tax19 = fields.Float(u'3%取得无形资产的进项',readonly=True,copy=False)
    tax_17_amount = fields.Float(u'17%的进项金额',readonly=True,copy=False)
    tax_13_amount = fields.Float(u'13%的进项金额',readonly=True,copy=False)
    tax_11_amount = fields.Float(u'11%的进项金额',readonly=True,copy=False)
    tax_6_amount = fields.Float(u'6%的进项金额',readonly=True,copy=False)
    tax_5_amount = fields.Float(u'5%的进项金额',readonly=True,copy=False)
    tax_3_amount = fields.Float(u'3%的进项金额',readonly=True,copy=False)
    tax_1_5_amount = fields.Float(u'1.5%的进项金额',readonly=True,copy=False)
    tax1_amount = fields.Float(u'17%有形动产租赁的进项金额',readonly=True,copy=False)
    tax2_amount = fields.Float(u'11%运输服务的进项金额',readonly=True,copy=False)
    tax3_amount = fields.Float(u'11%电信服务的进项金额',readonly=True,copy=False)
    tax4_amount = fields.Float(u'11%建筑安装服务的进项金额',readonly=True,copy=False)
    tax5_amount = fields.Float(u'11%不动产租赁服务的进项金额',readonly=True,copy=False)
    tax6_amount = fields.Float(u'11%受让土地使用权的进项金额',readonly=True,copy=False)
    tax7_amount = fields.Float(u'6%电信服务的进项金额',readonly=True,copy=False)
    tax8_amount = fields.Float(u'6%金融保险服务的进项金额',readonly=True,copy=False)
    tax9_amount = fields.Float(u'6%生活服务的进项金额',readonly=True,copy=False)
    tax10_amount = fields.Float(u'6%取得无形资产的进项金额',readonly=True,copy=False)
    tax11_amount = fields.Float(u'5%不动产租赁服务的进项金额',readonly=True,copy=False)
    tax12_amount = fields.Float(u'3%货物及加工、修理修配劳务的进项金额',readonly=True,copy=False)
    tax13_amount = fields.Float(u'3%运输服务的进项金额',readonly=True,copy=False)
    tax14_amount = fields.Float(u'3%电信服务的进项金额',readonly=True,copy=False)
    tax15_amount = fields.Float(u'3%建筑安装服务的进项金额',readonly=True,copy=False)
    tax16_amount = fields.Float(u'3%金融保险服务的进项金额',readonly=True,copy=False)
    tax17_amount = fields.Float(u'3%有形动产租赁服务的进项金额',readonly=True,copy=False)
    tax18_amount = fields.Float(u'3%生活服务的进项金额',readonly=True,copy=False)
    tax19_amount = fields.Float(u'3%取得无形资产的进项金额',readonly=True,copy=False)

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

    #结束本期发票，然后确认money_invoice
    @api.one
    def tax_invoice_done(self):
        res = {}
        for line in self.line_ids:
            if not line.partner_id:
                raise UserError(u'税号%s没找到到供应商，请去供应商处维护！'%line.partner_code)
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

    def create_input_structure(self):
        for line in self.line_ids:
            #不抵扣发票不计算
            if line.is_deductible:
                continue
            if len(line.money_invoice_ids) == 1:
                tax_structure = self.env['country.line'].search([('category_id', '=', line.money_invoice_ids.category_id.id)])
                if line.tax_rate == 17:
                    self.tax_17 += line.invoice_tax
                    self.tax_17_amount += line.invoice_amount
                    if tax_structure.name == 'no16':
                        self.tax1 += line.invoice_tax
                        self.tax1_amount += line.invoice_amount
                elif line.tax_rate == 13:
                    self.tax_13 += line.invoice_tax
                    self.tax_13_amount += line.invoice_amount
                elif line.tax_rate == 11:
                    self.tax_11 += line.invoice_tax
                    self.tax_11_amount += line.invoice_amount
                    if tax_structure.name == 'no1':
                        self.tax2 += line.invoice_tax
                        self.tax2_amount += line.invoice_amount
                    if tax_structure.name == 'no2':
                        self.tax3 += line.invoice_tax
                        self.tax3_amount += line.invoice_amount
                    if tax_structure.name == 'no3':
                        self.tax4 += line.invoice_tax
                        self.tax4_amount += line.invoice_amount
                    if tax_structure.name == 'no4':
                        self.tax5 += line.invoice_tax
                        self.tax5_amount += line.invoice_amount
                    if tax_structure.name == 'no5':
                        self.tax6 += line.invoice_tax
                        self.tax6_amount += line.invoice_amount
                elif line.tax_rate == 6:
                    self.tax_6 += line.invoice_tax
                    self.tax_6_amount += line.invoice_amount
                    if tax_structure.name == 'no2':
                        self.tax7 += line.invoice_tax
                        self.tax7_amount += line.invoice_amount
                    if tax_structure.name == 'no6':
                        self.tax8 += line.invoice_tax
                        self.tax8_amount += line.invoice_amount
                    if tax_structure.name == 'no7':
                        self.tax9 += line.invoice_tax
                        self.tax9_amount += line.invoice_amount
                    if tax_structure.name == 'no8':
                        self.tax10 += line.invoice_tax
                        self.tax10_amount += line.invoice_amount
                elif line.tax_rate == 5:
                    self.tax_5 += line.invoice_tax
                    self.tax_5_amount += line.invoice_amount
                    if tax_structure.name == 'no4':
                        self.tax11 += line.invoice_tax
                        self.tax11_amount += line.invoice_amount
                elif line.tax_rate == 3:
                    self.tax_3 += line.invoice_tax
                    self.tax_3_amount += line.invoice_amount
                    if tax_structure.name == 'no10':
                        self.tax12 += line.invoice_tax
                        self.tax12_amount += line.invoice_amount
                    if tax_structure.name == 'no1':
                        self.tax13 += line.invoice_tax
                        self.tax13_amount += line.invoice_amount
                    if tax_structure.name == 'no2':
                        self.tax14 += line.invoice_tax
                        self.tax14_amount += line.invoice_amount
                    if tax_structure.name == 'no12':
                        self.tax15 += line.invoice_tax
                        self.tax15_amount += line.invoice_amount
                    if tax_structure.name == 'no6':
                        self.tax16 += line.invoice_tax
                        self.tax16_amount += line.invoice_amount
                    if tax_structure.name == 'no16':
                        self.tax17 += line.invoice_tax
                        self.tax17_amount += line.invoice_amount
                    if tax_structure.name == 'no7':
                        self.tax18 += line.invoice_tax
                        self.tax18_amount += line.invoice_amount
                    if tax_structure.name == 'no8':
                        self.tax19 += line.invoice_tax
                        self.tax19_amount += line.invoice_amount
                else:
                    raise UserError(u'发票%s税率异常！'%line.invoice_name)
            else:
                for money in line.money_invoice_ids:
                    amount = money.amount-money.tax_amount
                    tax_rate = round(money.tax_amount/amount*100,0)
                    tax_structure = self.env['country.line'].search([('category_id', '=', money.category_id.id)])
                    if tax_rate == 17:
                        self.tax_17 += money.tax_amount
                        self.tax_17_amount += amount
                        if tax_structure.name == 'no16':
                            self.tax1 += money.tax_amount
                            self.tax_1_amount += amount
                    elif tax_rate == 13:
                        self.tax_13 += money.tax_amount
                        self.tax_13_amount += amount
                    elif tax_rate == 11:
                        self.tax_11 += money.tax_amount
                        self.tax_11_amount += amount
                        if tax_structure.name == 'no1':
                            self.tax2 += money.tax_amount
                            self.tax2_amount += amount
                        if tax_structure.name == 'no2':
                            self.tax3 += money.tax_amount
                            self.tax3_amount += amount
                        if tax_structure.name == 'no3':
                            self.tax4 += money.tax_amount
                            self.tax4_amount += amount
                        if tax_structure.name == 'no4':
                            self.tax5 += money.tax_amount
                            self.tax5_amount += amount
                        if tax_structure.name == 'no5':
                            self.tax6 += money.tax_amount
                            self.tax6_amount += amount
                    elif tax_rate == 6:
                        self.tax_6 += money.tax_amount
                        self.tax_6_amount += amount
                        if tax_structure.name == 'no2':
                            self.tax7 += money.tax_amount
                            self.tax7_amount += amount
                        if tax_structure.name == 'no6':
                            self.tax8 += money.tax_amount
                            self.tax8_amount += amount
                        if tax_structure.name == 'no7':
                            self.tax9 += money.tax_amount
                            self.tax9_amount += amount
                        if tax_structure.name == 'no8':
                            self.tax10 += money.tax_amount
                            self.tax10_amount += amount
                    elif tax_rate == 5:
                        self.tax_5 += money.tax_amount
                        self.tax_5_amount += amount
                        if tax_structure.name == 'no4':
                            self.tax11 += money.tax_amount
                            self.tax11_amount += amount
                    elif tax_rate == 3:
                        self.tax_3 += money.tax_amount
                        self.tax_3_amount += amount
                        if tax_structure.name == 'no10':
                            self.tax12 += money.tax_amount
                            self.tax12_amount += amount
                        if tax_structure.name == 'no1':
                            self.tax13 += money.tax_amount
                            self.tax13_amount += amount
                        if tax_structure.name == 'no2':
                            self.tax14 += money.tax_amount
                            self.tax14_amount += amount
                        if tax_structure.name == 'no12':
                            self.tax15 += money.tax_amount
                            self.tax15_amount += amount
                        if tax_structure.name == 'no6':
                            self.tax16 += money.tax_amount
                            self.tax16_amount += amount
                        if tax_structure.name == 'no16':
                            self.tax17 += money.tax_amount
                            self.tax17_amount += amount
                        if tax_structure.name == 'no7':
                            self.tax18 += money.tax_amount
                            self.tax18_amount += amount
                        if tax_structure.name == 'no8':
                            self.tax19 += money.tax_amount
                            self.tax19_amount += amount
                    else:
                        raise UserError(u'发票%s税率异常！'%line.invoice_name)

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
        ''' 反审核本期发票,反确认money_invoice '''
        self.tax_17 = self.tax_13 = self.tax_11 = self.tax_6 = self.tax_5 = self.tax_3 = self.tax_1_5 = 0
        self.tax1 = self.tax2 = self.tax3 = self.tax4 = self.tax5 = self.tax6 = self.tax7 = self.tax8 = self.tax9 = self.tax10 = 0
        self.tax11 = self.tax12 = self.tax14 = self.tax15 = self.tax16 = self.tax17 = self.tax18 = self.tax19 = self.tax12 = 0
        self.tax_17_amount = self.tax_13_amount = self.tax_11_amount = self.tax_6_amount = self.tax_5_amount = self.tax_3_amount = self.tax_1_5_amount = 0
        self.tax1_amount = self.tax2_amount = self.tax3_amount = self.tax4_amount = self.tax5_amount = self.tax6_amount = self.tax7_amount = self.tax8_amount = self.tax9_amount = self.tax10_amount = 0
        self.tax11_amount = self.tax12_amount = self.tax14_amount = self.tax15_amount = self.tax16_amount = self.tax17_amount = self.tax18_amount = self.tax19_amount = self.tax12_amount = 0
        self.state = 'draft'

class no_deductible_update(models.TransientModel):
    _name = 'no.deductible.update'
    _description = 'no deductible update'
    account = fields.Char(u'税号', default=lambda self:self.env['config.country'].search([]).name)
    password = fields.Char(u'密码', default=lambda self:self.env['config.country'].search([]).password)


    def guoshui_login(self):
        browser = webdriver.Chrome(chrome_options=options)
        try:
            browser.get('http://100.0.0.120:6000/dzswj/index-dl.html')
        except:
            raise UserError(u'网页打不开，请确认vpdn已拨号')
        #最高等待10
        browser.implicitly_wait(10)
        browser.find_element_by_name("number").send_keys(self.account)
        browser.find_element_by_name("number").send_keys(Keys.TAB)
        browser.find_element_by_name("password").send_keys(self.password)
        browser.implicitly_wait(10)
        login_button = browser.find_element_by_class_name("login-btn-style")
        login_button.click()
        nowhandle = browser.current_window_handle
        time.sleep(5)
        #关闭js提示
        try:
            browser.switch_to_alert().accept()
        except:
            print 'no js windows!'
        #关闭弹窗
        try:
            all_windows = browser.window_handles
            for windows in all_windows:
                if windows != nowhandle:
                    browser.switch_to.window(windows)
                    browser.close()
            browser.switch_to.window(nowhandle)
        except:
            print 'no new windows open!'
        browser.find_element_by_class_name("homepage-nav-sbns").click()

        return browser

    @api.one
    def no_deductible_update(self):
        browser = self.guoshui_login()
        browser.implicitly_wait(10)
        browser.find_element_by_link_text("增值税一般纳税人").click()
        browser.implicitly_wait(10)
        #上传不抵扣发票
        browser.find_element_by_link_text("不抵扣发票").click()
        browser.implicitly_wait(10)
        try:
            if not self.env.context.get('active_id'):
                return
            tax_invoice = self.env['tax.invoice'].browse(self.env.context.get('active_id'))
            i = 0
            for line in tax_invoice.line_ids:
                if line.is_deductible:
                    i += 1
                    update_code = browser.find_element_by_name('B_FPDM_%s'%int(i))
                    update_name = browser.find_element_by_name('B_FPHM_%s'%int(i))
                    update_code.send_keys(line.invoice_code)
                    browser.implicitly_wait(10)
                    update_name.send_keys(line.invoice_name)
                    browser.implicitly_wait(10)
            browser.find_element_by_link_text("提交").click()
            browser.implicitly_wait(10)
            browser.switch_to_alert().accept()
        except:
            browser.switch_to_alert().accept()
        #确认抵扣联明细
        browser.find_element_by_link_text("抵扣联明细").click()
        browser.implicitly_wait(10)
        try:
            browser.find_element_by_link_text("发票数据下载").click()
            browser.implicitly_wait(10)
            total2 = browser.find_element_by_name("hj_se_se").get_attribute('value')
            browser.implicitly_wait(10)
            print total2,tax_invoice.tax_amount
            if float(total2) == tax_invoice.tax_amount:
                browser.find_element_by_link_text("确认提交").click()
                browser.implicitly_wait(10)
            else:
                raise UserError(u'与国税不一致')
        except:
            browser.find_element_by_link_text("返回").click()
            browser.find_element_by_link_text("增值税一般纳税人").click()
            browser.implicitly_wait(10)
        #上传进项结构明细表
        if tax_invoice.state == 'done':
            browser.find_element_by_link_text("进项结构明细表").click()
            browser.implicitly_wait(10)
            try:
                if tax_invoice.tax_17:
                    browser.find_element_by_id("sl_17_je").clear()
                    browser.find_element_by_id("sl_17_je").send_keys('%s'%tax_invoice.tax_17_amount)
                    browser.find_element_by_id("sl_17_se").clear()
                    browser.find_element_by_id("sl_17_se").send_keys('%s'%tax_invoice.tax_17)
                if tax_invoice.tax1:
                    browser.find_element_by_id("sl_17_qz_yxdczp_je").clear()
                    browser.find_element_by_id("sl_17_qz_yxdczp_je").send_keys('%s'%tax_invoice.tax1_amount)
                    browser.find_element_by_id("sl_17_qz_yxdczp_se").clear()
                    browser.find_element_by_id("sl_17_qz_yxdczp_se").send_keys('%s'%tax_invoice.tax1_amount)
                if tax_invoice.tax_13:
                    browser.find_element_by_id("sl_13_je").clear()
                    browser.find_element_by_id("sl_13_je").send_keys('%s'%tax_invoice.tax_13_amount)
                    browser.find_element_by_id("sl_13_se").clear()
                    browser.find_element_by_id("sl_13_se").send_keys('%s'%tax_invoice.tax_13)
                if tax_invoice.tax_11:
                    browser.find_element_by_id("sl_11_je").clear()
                    browser.find_element_by_id("sl_11_je").send_keys('%s'%tax_invoice.tax_11_amount)
                    browser.find_element_by_id("sl_11_se").clear()
                    browser.find_element_by_id("sl_11_se").send_keys('%s'%tax_invoice.tax_11)
                if tax_invoice.tax_6:
                    browser.find_element_by_id("sl_6_je").clear()
                    browser.find_element_by_id("sl_6_je").send_keys('%s'%tax_invoice.tax_6_amount)
                    browser.find_element_by_id("sl_6_se").clear()
                    browser.find_element_by_id("sl_6_se").send_keys('%s'%tax_invoice.tax_6)
                if tax_invoice.tax_5:
                    browser.find_element_by_id("sl_5_je").clear()
                    browser.find_element_by_id("sl_5_je").send_keys('%s'%tax_invoice.tax_5_amount)
                    browser.find_element_by_id("sl_5_se").clear()
                    browser.find_element_by_id("sl_5_se").send_keys('%s'%tax_invoice.tax_5)
                if tax_invoice.tax_17:
                    browser.find_element_by_id("sl_3_je").clear()
                    browser.find_element_by_id("sl_3_je").send_keys('%s'%tax_invoice.tax_3_amount)
                    browser.find_element_by_id("sl_3_se").clear()
                    browser.find_element_by_id("sl_3_se").send_keys('%s'%tax_invoice.tax_3)
                browser.find_element_by_link_text("提交").click()
                browser.implicitly_wait(10)
                browser.switch_to_alert().accept()
            except:
                browser.find_element_by_link_text("返回").click()
                browser.find_element_by_link_text("增值税一般纳税人").click()
                browser.implicitly_wait(10)
        browser.find_element_by_link_text("固定资产抵扣明细").click()
        browser.implicitly_wait(10)
        #上传固定资产抵扣明细
        browser.find_element_by_name("zj_fphm").send_keys("21230559")
        browser.find_element_by_xpath("//input[@value='确定']").click()
        browser.find_element_by_name("zj_jqsbmc").send_keys("测试固定资产")
        browser.find_element_by_name("zj_gmrq").send_keys("2017-01-02")
        browser.find_element_by_name("zj_sbdj").send_keys("单价")
        browser.find_element_by_name("zj_sbsl").send_keys("数量")
        browser.find_element_by_name("zj_sbje").send_keys("金额")
        browser.find_element_by_name("zj_dkse").send_keys("税额")
        browser.find_element_by_link_text("提交").click()

class partner(models.Model):
    _inherit = 'partner'
    tax_number = fields.Char(u'税号', copy=False)

class money_invoice(models.Model):
    _inherit = 'money.invoice'
    tax_invoice_date = fields.Date(string=u'认证日期',
                           help=u'发票认证的日期')

class tax_invoice_line(models.Model):
    _name = 'tax.invoice.line'
    _description = u'认证发票明细'

    @api.onchange('invoice_amount','invoice_tax')
    def tax_import(self):
        if self.invoice_amount:
            self.tax_rate = self.invoice_tax/self.invoice_amount*100

    @api.onchange('partner_code')
    def get_partner_id(self):
        if self.partner_code:
            self.partner_id = self.env['partner'].search([
                                 ('tax_number', '=', self.partner_code)])
        else:
            raise UserError(u'供应商中察找不到相应税号！')

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

    _sql_constraints = [
        ('unique_start_date', 'unique (invoice_code, invoice_name)', u'发票代码+发票号码不能相同!'),
    ]

class create_invoice_line_wizard(models.TransientModel):
    _name = 'create.invoice.line.wizard'
    _description = 'Tax Invoice Import'

    excel = fields.Binary(u'导入认证系统导出的excel文件',)

    @api.one
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
        xls_data = xlrd.open_workbook(
                file_contents=base64.decodestring(self.excel))
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
            print 'aaaaaa',in_xls_data
            if in_xls_data.get(u'销方税号'):
                partner_id = self.env['partner'].search([
                                 ('tax_number', '=', in_xls_data.get(u'销方税号'))])
            else:
                partner_id = self.env['partner'].search([
                                 ('name', '=', in_xls_data.get(u'销方名称'))])
            self.env['tax.invoice.line'].create({
                'partner_code': str(in_xls_data.get(u'销方税号')),
                'partner_id': partner_id.id,
                'invoice_code': str(in_xls_data.get(u'发票代码')),
                'invoice_name': str(in_xls_data.get(u'发票号码')),
                'invoice_amount': float(in_xls_data.get(u'金额')),
                'invoice_tax': float(in_xls_data.get(u'税额')),
                'invoice_open_date': self.excel_date(in_xls_data.get(u'开票日期')),
                'invoice_confim_date': self.excel_date(in_xls_data.get(u'认证时间') or in_xls_data.get(u'确认时间')),
                'order_id':invoice_id.id,
                'tax_rate':float(in_xls_data.get(u'税额'))/float(in_xls_data.get(u'金额'))*100,
            })

    def excel_date(self,data):
        #将excel日期改为正常日期
        if type(data) in (int,float):
            year, month, day, hour, minute, second = xlrd.xldate_as_tuple(data,0)
            py_date = datetime.datetime(year, month, day, hour, minute, second)
        else:
            py_date = data
        return py_date



