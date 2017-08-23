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
import time
import datetime
import re


from selenium import webdriver
from selenium.webdriver.common.keys import Keys

#初始化chrome
options = webdriver.ChromeOptions()
options.add_argument('--explicitly-allowed-ports=6000,556')

BALANCE_DIRECTIONS_TYPE = [
    ('in', u'借'),
    ('out', u'贷')]

ACCOUNT_FORMULA={
    'minamt':u'本月借方合计',
    'mouamt':u'本月贷方合计',
    'yinamt':u'本年借方合计',
    'youamt':u'本年贷方合计',
    'mbnamt':u'本月余额合计',
    'ybnamt':u'本年余额合计',
}

class tax_provice_updata(models.TransientModel):
    _name = 'tax.provice.updata'
    _description = 'tax provice updata'

    account = fields.Char(u'税号', default=lambda self:self.env['config.province'].search([]).name)
    password = fields.Char(u'密码', default=lambda self:self.env['config.province'].search([]).password)
    mobile = fields.Char(u'手机后4位', default=lambda self:self.env['config.province'].search([]).tel)

    def provice_login(self,browser,url):
        #登入地税
        #todo 图片验证码的问题
        browser.get(url+'#/login')
        #最高等待10
        browser.implicitly_wait(10)
        browser.find_element_by_id("username").send_keys(self.account)
        browser.find_element_by_id("password0").send_keys(self.password)
        browser.find_element_by_id("mobile").send_keys(self.mobile)
        time.sleep(10)
        try:
            login_button = browser.find_element_by_id("ptyhDL")
            login_button.click()
        except:
            UserError(u'请确认帐号，密码，手机后4位及验证码')
        browser.implicitly_wait(30)
        browser.find_element_by_class_name("tax").click()
        cookies = browser.get_cookies()

        return cookies

    def update_cj_jy(self,browser,url):
        #上传城建，教育附加，地方教育附加
        nowhandle = browser.current_window_handle
        browser.get(url)
        try:
            time.sleep(20)
            all_windows = browser.window_handles
            for windows in all_windows:
                if windows != nowhandle:
                    browser.switch_to.window(windows)
                    gs_button = browser.find_element_by_xpath("//div[@class='button']/button[1]")
                    up_button = browser.find_element_by_xpath("//div[@class='button']/button[2]")
                    close_button = browser.find_element_by_xpath("//div[@class='button']/a/button")
        except:
            print 'no new windows open!'
        gs_button.click()
        browser.implicitly_wait(10)
        #等测试时再开
        '''
        try:
            browser.switch_to_alert().accept()
            close_button.click()
        except:
            up_button.click()
        browser.close()
        '''
        browser.switch_to.window(nowhandle)

    def update_stamp_duty(self,browser,cookies,url):
        #上传印花税
        nowhandle = browser.current_window_handle
        browser.get(url)
        try:
            time.sleep(20)
            all_windows = browser.window_handles
            for windows in all_windows:
                if windows != nowhandle:
                    browser.switch_to.window(windows)
                    up_button = browser.find_element_by_xpath("//div[@class='button']/button[1]")
                    close_button = browser.find_element_by_xpath("//div[@class='button']/a/button")
        except:
            print 'no new windows open!'
        browser.find_element_by_name("jsje[0]").clear()
        browser.find_element_by_name("jsje[0]").send_keys("5555555")
        browser.find_element_by_name("jsje[0]").send_keys(Keys.TAB)
        try:
            up_button.click()
        except:
            print '申报未成功'
        browser.switch_to.window(nowhandle)

    def update_social_security(self,browser,cookies,url):
        #上传社保
        nowhandle = browser.current_window_handle
        browser.get(url)
        try:
            time.sleep(20)
            all_windows = browser.window_handles
            for windows in all_windows:
                if windows != nowhandle:
                    browser.switch_to.window(windows)
                    up_button = browser.find_element_by_xpath("//div[@class='button']/button[1]")
                    close_button = browser.find_element_by_xpath("//div[@class='button']/a/button")
        except:
            print 'no new windows open!'
        browser.find_element_by_name("jsje[0]").clear()
        browser.find_element_by_name("jsje[0]").send_keys("5555555")
        browser.find_element_by_name("jsje[0]").send_keys(Keys.TAB)
        try:
            up_button.click()
        except:
            print '申报未成功'
        browser.switch_to.window(nowhandle)

    @api.one
    def tax_provice_update(self):
        province_id = self.env['config.province'].search([])
        url = province_id.province_url
        browser = webdriver.Chrome(chrome_options=options)
        browser.implicitly_wait(10)
        if province_id.ids:
            cookies = self.provice_login(browser,url)
            for line in province_id.ids:
                new_url = url + line.add_url
                if line.name == 'cj_jy':
                    self.update_cj_jy(browser,cookies,new_url)
                if line.name == 'stamp_duty':
                    self.update_stamp_duty(browser,cookies,new_url)
                if line.name == 'social_security':
                    self.update_social_security(browser,cookies,new_url)

class TaxReport(models.Model):
    """地税申报表模板
        模板主要用来定义项目的 科目范围,
        然后根据科目的范围得到科目范围内的科目的余额
    """
    _name = "tax.report"

    name = fields.Char(u'报表名称', help=u'报表的行次的总一个名称')
    date = fields.Date(u'记帐日期', required=True)
    account = fields.Many2one('finance.account', u'记帐科目', required=True)
    balance_directions = fields.Selection(BALANCE_DIRECTIONS_TYPE, u'借/贷方向', required=True, help=u'生成凭证是借方或者贷方！')
    period_id = fields.Many2one(
        'finance.period',
        u'会计期间',
        compute='_compute_period_id', ondelete='restrict', store=True)
    line_ids = fields.One2many('tax.report.line',
                               'order_id',
                               u'报表明细行',
                               required=True)
    amount = fields.Float(u'金额', digits=dp.get_precision(u'金额'), compute='_report_amount', ondelete='restrict', store=True)


    @api.one
    @api.depends('date')
    def _compute_period_id(self):
        self.period_id = self.env['finance.period'].get_period(self.date)

    @api.one
    @api.depends('line_ids.amount')
    def _report_amount(self):
        amount = 0
        for line in self.line_ids:
            if line.balance_directions == 'in':
                amount += line.amount
            else:
                amount -= line.amount
        self.amount = abs(amount)

    @api.one
    def tax_to_voucher(self):
        ''' 生成凭证，不关联，可重复生成，按钮放在更多里'''
        vouch_obj = self.env['voucher'].create({'date': self.date})
        for line in self.line_ids:
            if line.balance_directions == 'in':
                vouch_obj.line = self.env['voucher.line'].create({'voucher_id': vouch_obj.id, 'name': line.name,
                     'debit': line.amount, 'account_id': line.account.id,
                     'auxiliary_id': False})
            else:
                vouch_obj.line = self.env['voucher.line'].create({'voucher_id': vouch_obj.id, 'name': line.name,
                     'credit': line.amount, 'account_id': line.account.id,
                     'auxiliary_id': False})


class tax_report_line(models.Model):
    _name = 'tax.report.line'

    order_id = fields.Many2one('tax.report', u'单位名称', index=True,required=True, ondelete='cascade')
    name = fields.Char(u'摘要', help=u'报表的行次的总一个名称')
    account = fields.Many2one('finance.account', u'记帐科目', required=True)
    occurrence_balance_formula = fields.Text(u'计算公式', required=True, help=u'设定计算基础金额公式')
    current_occurrence_balance = fields.Float(u'计算基础金额', help=u'本月的收入的金额!', compute='_tax_base', ondelete='restrict', store=True)
    tax_rate = fields.Float(u'税率', required=True, help ='为百分比，如税率为17%，则填写17')
    amount = fields.Float(u'金额', digits=dp.get_precision(u'金额'), compute='_compute_amount', ondelete='restrict', store=True)
    balance_directions = fields.Selection(BALANCE_DIRECTIONS_TYPE, u'借/贷方向', required=True, help=u'生成凭证是借方或者贷方！')

    @api.one
    @api.depends('current_occurrence_balance','tax_rate')
    def _compute_amount(self):
        self.amount = self.current_occurrence_balance * self.tax_rate

    @api.one
    @api.depends('occurrence_balance_formula')
    def _tax_base(self):
        #双"间代表从帐上求来的科目金额（[本月／本年]／[借／贷／余额]）
        if self.occurrence_balance_formula:
            formula = self.occurrence_balance_formula
            p = re.compile(r'"([^"]+)"')
            try:
                tax_base = eval(p.sub(self.account_amount, formula))
                self.current_occurrence_balance = tax_base
            except:
                raise UserError(u'请按正确的公式设置公式%s,'%self.occurrence_balance_formula)

    def account_amount(self,get_data):
        #按公式取需要的科目金额
        data = get_data.group()
        code = re.findall(r"\d+\.?\d*",data)
        account_code = code[0]
        today = datetime.date.today()
        #判断公式期间是否正确
        if "," in data:
            year = code[1]
            month = code[2]
            print year,month
            if len(month) < 2:
                month = '0%s' %(month)
            if len(year) == 4 and month != 0:
                date = '%s-%s-11'%(year,month)
            if len(year) < 4:
                year = today.year
                if int(month) == 0:
                    month = today.month
                if int(month) < 10:
                    month = '0%s' %(int(month))
                date = '%s-%s-11'%(year,month)
            else :
                month = today.month
                if month < 10:
                    month = '0%s' %(month)
                print 'c'
                date = '%s-%s-11'%(year,month)
            print date
        else:
            date = fields.Date.context_today(self)
        try:
            period_id = self.env['finance.period'].get_period(date)
        except:
            raise UserError(u'请确认公式期间%s-%s是否正确,'%(year, month))
        #判断公式科目是否正确
        account = self.env['finance.account'].search([('code', '=', account_code)])
        if not account:
            raise UserError(u'请确认公式科目%s是否正确,'%data)

        trial_balance = self.env['trial.balance'].search([('subject_name_id', '=', account_code), ('period_id', '=', period_id.id)])
        #判断公式函数是否正确
        formula = data[1:7]
        if formula in ACCOUNT_FORMULA:
            if formula == 'minamt':
                data = trial_balance.current_occurrence_debit
            if formula == 'mouamt':
                data = trial_balance.current_occurrence_credit
            if formula == 'yinamt':
                data = trial_balance.cumulative_occurrence_debit
            if formula == 'youamt':
                data = trial_balance.cumulative_occurrence_credit
            if formula == 'mbnamt':
                balance_directions = account.balance_directions
                if balance_directions == 1:
                    data = trial_balance.current_occurrence_debit - trial_balance.current_occurrence_credit
                else:
                    data = trial_balance.current_occurrence_credit - trial_balance.current_occurrence_debit
            if formula == 'ybnamt':
                balance_directions = account.balance_directions
                if balance_directions == 1:
                    data = trial_balance.cumulative_occurrence_debit - trial_balance.cumulative_occurrence_credit
                else:
                    data = trial_balance.cumulative_occurrence_credit - trial_balance.cumulative_occurrence_debit
        else:
            raise UserError(u'请确认公式函数%s是否正确,'%data)
        return str(data)

class add_report(models.Model):
    _inherit = 'province.line'
    tax_report = fields.Many2one('province.line', u'联连报表', index=True,
                               required=True, ondelete='cascade')