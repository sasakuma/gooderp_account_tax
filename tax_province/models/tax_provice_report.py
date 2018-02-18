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
import pytesseract
from PIL import Image
from PIL import ImageEnhance
import base64
import xlrd

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.alert import Alert

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

firefox_path = r"C:\Program Files (x86)\Mozilla Firefox\geckodriver.exe"
browser = False

threshold = 140
table = []
for i in range(256):
  if i < threshold:
    table.append(0)
  else:
    table.append(1)

#登入国税系统，申报资产负债表，利润表
class provice_up_down(models.Model):
    _name = 'provice.upanddown'
    _description = 'tax provice updata'

    name = fields.Many2one(
        'finance.period',
        u'会计期间',required=True)
    account = fields.Many2one('config.province', u'税号', required=True)
    password = fields.Char(u'密码')
    image = fields.Binary(u'图片', attachment=True)
    img_code = fields.Char(u'验证码')
    _sql_constraints = [
        ('unique_name', 'unique (name)', u'会计期间不能重复!'),
    ]
    state = fields.Selection([('draft', u'草稿'),
                              ('done', u'已完成')], u'状态', default='draft')

    profit_ids = fields.One2many('profit.update',
                               'order_id',
                               u'上传利润表数据',
                               copy=False,
                               required=True)
    balance_ids = fields.One2many('balance.update',
                               'order_id',
                               u'上传资产负债表数据',
                               copy=False,
                               required=True)

    excel_profit = fields.Binary(u'用于导入利润表的excel文件' )
    excel_balance = fields.Binary(u'用于导入资产负债表的excel文件')
    note = fields.Char(u'备注')

    def get_img_code(self):
        global browser
        if not browser:
            browser = webdriver.Firefox(executable_path=firefox_path)
            browser.maximize_window()
        url = "http://etax.zjtax.gov.cn/dzswj/user/login.html"
        browser.get(url)
        browser.get_screenshot_as_file("./log/BB.png")
        imgelement = browser.find_element_by_id("yzmImg")
        location = imgelement.location
        size = imgelement.size
        coderange = (int(location['x']), int(location['y']), int(location['x'] + size['width']),
                     int(location['y'] + size['height']))
        i = Image.open("./log/BB.png")
        frame4 = i.crop(coderange)
        frame4.save("./log/CC.png")
        imgdata = open('./log/CC.png', 'rb')
        img_code = base64.encodestring(imgdata.read())
        '''
        打开图片
        img = Image.open('./log/CC.png')
        img.show()
        code = image_file_to_string('./log/CC.png', graceful_errors=True)
        print code
        '''
        im = Image.open('./log/CC.png')
        # 转化到灰度图
        imgry = im.convert('L')
        # 保存图像
        imgry.save("./log/dd.png")
        # 二值化，采用阈值分割法，threshold为分割点
        out = imgry.point(table, '1')
        out.save("./log/ee.png")
        # 识别
        code = pytesseract.image_to_string(out).strip()
        self.write({'image': img_code,
                    'img_code': code})

    @api.one
    def to_done(self):
        if not browser:
            raise UserError(u'请重新取验证码')
        username = self.account.name
        browser.find_element_by_id("username").send_keys(username)
        browser.find_element_by_id("password").send_keys(self.password)
        browser.find_element_by_id("vcode").send_keys(self.img_code)
        login_button = browser.find_element_by_id("loginBtn1")
        login_button.click()
        browser.get_screenshot_as_file("./log/new.png")
        company_name = browser.find_element_by_id("userinfo").text
        self.update_Balance()

    def update_Balance(self):
        if not browser:
            raise UserError(u'请重新登入')
        url = "http://etax.zjtax.gov.cn/zjdzswjsbweb/pages/sb/nssb/bdlb.html?xmzslx=1&sbxmdm=xqycwbb&sfqz=N"
        browser.get(url)
        time.sleep(3)
        try:
            browser.find_element_by_xpath("//ul[@id='sbbdlist']/li[2]/a/img")
            print "已申报"
            return
        except:
            browser.find_element_by_xpath("//ul[@id='sbbdlist']/li[2]/a").click()
            time.sleep(3)
            browser.get_screenshot_as_file("./log/new3.png")
            for i in self.profit_ids:
                update_id = i.update_name
                update_number = str(i.update_number)
                browser.find_element_by_id(update_id).clear()
                browser.find_element_by_id(update_id).send_keys(update_number)
                browser.find_element_by_id(update_id).send_keys(Keys.ENTER)
            browser.get_screenshot_as_file("./log/new4.png")
            browser.find_element_by_xpath("//td[@colspan='4']/a[2]").click()
            time.sleep(3)
            # 关闭js提示
            try:
                browser.switch_to_alert().accept()
            except:
                print 'no js windows!'
            browser.get_screenshot_as_file("./log/new5.png")
            browser.close()
            global browser
            browser = False
            return

    @api.one
    def to_draft(self):
        return

    @api.one
    def create_profit_update(self):
        """
        通过Excel文件导入信息到profit.update
        """
        xls_data = xlrd.open_workbook(
            file_contents=base64.decodestring(self.excel_profit))
        table = xls_data.sheets()[0]
        # 取国税申报信息
        data_list = self.account.profit_lins
        # 如果有历史数据则删除历史数据，以新数据为准
        if self.profit_ids:
            self.profit_ids.unlink()
        for i in data_list:
            self.env['profit.update'].create({
                'update_name': i.update_name,
                'update_number': table.cell(int(i.excel_ncols), int(i.excel_ncows)).value or '0.00',
                'order_id': self.id,
            })

    @api.one
    def create_balance_update(self):
        """
        通过Excel文件导入信息到balance.update
        """
        xls_data = xlrd.open_workbook(
            file_contents=base64.decodestring(self.excel_balance))
        table = xls_data.sheets()[0]
        # 取国税申报信息
        data_list = self.account.balance_lins
        # 如果有历史数据则删除历史数据，以新数据为准
        if self.balance_ids:
            self.balance_ids.unlink()
        for i in data_list:
            self.env['balance.update'].create({
                'update_name': i.update_name,
                'update_number': table.cell(int(i.excel_ncols), int(i.excel_ncows)).value or '0.00',
                'order_id': self.id,
            })
#利润表上传内容
class profit_update(models.Model):
    _name = 'profit.update'

    order_id = fields.Many2one('provice.upanddown', u'单位名称', index=True,
                               required=True, ondelete='cascade')
    update_name = fields.Char(u'上传ID名称',
                          required=True)
    update_number = fields.Float(u'上传金额',
                          required=True)
#资产负债表上传内容
class balance_update(models.Model):
    _name = 'balance.update'

    order_id = fields.Many2one('provice.upanddown', u'单位名称', index=True,
                               required=True, ondelete='cascade')
    update_name = fields.Char(u'上传ID名称',
                          required=True)
    update_number = fields.Float(u'上传金额',
                          required=True)
#地税申报报表
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
#地税申报报表明细
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
                date = '%s-%s-11'%(year,month)
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
#登入地税，下载地税申报内容
class tax_get_zjds(models.Model):
    _name = 'tax.get.zjds'
    _description = 'tax get zjds'

    name = fields.Many2one(
        'finance.period',
        u'会计期间', required=True)
    account = fields.Char(u'用户名', required=True)
    password = fields.Char(u'密码')
    tel = fields.Char(u'手机后4位')
    image = fields.Binary(u'图片', attachment=True)
    img_code = fields.Char(u'验证码')
    note = fields.Char(u'备注')
    line_ids = fields.One2many('tax.get.zjds.line', 'order_id', u'发票明细行',copy=False)

    _sql_constraints = [
        ('unique_name', 'unique (name)', u'会计期间不能重复!'),
    ]
    state = fields.Selection([('draft', u'草稿'),
                              ('done', u'已完成')], u'状态', default='draft')
    base_url = 'http://www.zjds-etax.cn/wsbs/'

    def get_img_code(self):
        global browser
        if not browser:
            browser = webdriver.Firefox(executable_path=firefox_path)
            browser.maximize_window()
        add_url = '#/login'
        url = self.base_url + add_url
        browser.get(url)
        time.sleep(3)
        #取图片
        imgelement = browser.find_element_by_xpath("//i [@class='code_img']/a/img")
        img_code = imgelement.get_attribute('src')[22:]
        # 取图片说明
        self.write({'image': img_code})

    def download_tax(self):
        if not browser:
            raise UserError(u'请重新取验证码')
        username = browser.find_element_by_id("username")
        username.clear()
        username.send_keys(self.account)
        password = browser.find_element_by_id("password0")
        password.clear()
        password.send_keys(self.password)
        mobile = browser.find_element_by_id("mobile")
        mobile.clear()
        mobile.send_keys(self.tel)
        yzm = browser.find_element_by_id("imgCode")
        yzm.clear()
        yzm.send_keys(self.img_code)
        button = browser.find_element_by_id("ptyhDL")
        button.click()
        time.sleep(3)
        # 如果有JS弹出窗，则由gooderp返回给用户
        try:
            browser.find_element_by_xpath("//div [@ng-controller='jbxxController']")
        except:
            alert = browser.switch_to_alert()
            text = browser.find_element_by_id("popup_message").text
            raise UserError(u'提示！%s' % text)
            text.accept()
        self.get_stamp()
        browser.close()
        global browser
        browser = False
        self.create_voucher()
    #生成凭证
    def create_voucher(self):
        date = '%s28' % self.name.name
        for i in self.line_ids:
            if not i.debit_account:
                continue
            if not i.credit_account:
                continue
            if i.account_amount:
                vouch_obj = self.env['voucher'].create({'date': date, 'ref': '%s,%s' % (self._name, self.id)})
                self.env['voucher.line'].create({'voucher_id': vouch_obj.id, 'name': u'计提%s' % (i.tax_select),
                                                 'debit': i.account_amount, 'account_id': i.debit_account.id,
                                                 })
                self.env['voucher.line'].create({'voucher_id': vouch_obj.id, 'name': u'计提%s' % (i.tax_select),
                                                 'credit': i.account_amount,
                                                 'account_id': i.credit_account.id,
                                                 })
                i.write({'voucher_id': vouch_obj.id})
    #取交税报表
    def get_stamp(self):
        if not browser:
            raise UserError(u'请重新取验证码')
        add_url = '#/sscx/nssbcx/sbbcx'
        url = self.base_url + add_url
        browser.get(url)
        time.sleep(3)
        #删除旧数据
        if self.line_ids:
            self.line_ids.unlink()
        chaxun = browser.find_element_by_xpath("//td [@class='tjBtn']/button")
        chaxun.click()
        time.sleep(3)
        #取有几页
        total_pages = len(browser.find_element_by_class_name("pagination").find_elements_by_tag_name("li")) - 4
        page = browser.find_element_by_class_name("pagination").find_elements_by_tag_name("span")
        #循環所有报表页
        for i in range(total_pages):
            page[i+2].click()
            i += 1
            print i
            time.sleep(6)
            stamp = browser.find_elements_by_xpath("//div [@class='ngCanvas']/div")
            for i in stamp:
                text = i.text
                baobiao = text.split(u'《')[1].split(u'》')[0]
                gz_button = i.find_elements_by_tag_name("button")
                print text
                gz_button[0].click()
                time.sleep(3)
                #切换窗口
                handls = browser.window_handles
                print handls
                browser.switch_to_window(handls[1])
                time.sleep(3)
                self.get_tax(baobiao)
                browser.switch_to_window(handls[0])
    #从交税报表中取交税信息
    def get_tax(self,name):
        if not browser:
            raise UserError(u'请重新取验证码')
        if name == u'城建税、教育费附加、地方教育附加税（费）申报表':
            neirong = browser.find_elements_by_xpath("//tr [@ng-repeat='k in fjsData']")
            for tr in neirong:
                text = tr.find_elements_by_tag_name("td")
                row_list = []
                for td in text[:-1]:  # 遍历每一个td
                    row_list.append(td.text)  # 取出表格的数据，并放入行列表里
                account_amount = float(row_list[8].replace(',', ''))
                if not account_amount:
                    continue
                tax_name = row_list[0]
                credit_account = self.env['automatic.cost'].search([('name', '=', tax_name)]).category_id.account_id
                debit_account = self.env['automatic.cost'].search([('name', '=', tax_name)]).account_id
                self.env['tax.get.zjds.line'].create({
                    'order_id': self.id,
                    'debit_account':debit_account and debit_account.id or '',
                    'credit_account': credit_account and credit_account.id or '',
                    'tax_select': tax_name,
                    'tax_report': name or '',
                    'base_amount': float(row_list[2].replace(',','')) or '',
                    'account_amount': account_amount or '',
                    'tax_rate':row_list[7],
                })
        if name == u'社会保险费缴费申报表（适用单位缴费人）':
            neirong = browser.find_elements_by_xpath("//tr [@ng-repeat='s in printData.sbfsbbmxVOGrid']")
            for tr in neirong:
                text = tr.find_elements_by_tag_name("td")
                row_list = []
                for td in text[:-1]:  # 遍历每一个td
                    row_list.append(td.text)  # 取出表格的数据，并放入行列表里
                account_amount = float(row_list[5].replace(',', ''))
                if not account_amount:
                    continue
                tax_name = row_list[0] + row_list[2]
                print tax_name
                credit_account = self.env['automatic.cost'].search([('name', '=', tax_name)]).category_id.account_id
                debit_account = self.env['automatic.cost'].search([('name', '=', tax_name)]).account_id
                self.env['tax.get.zjds.line'].create({
                    'order_id': self.id,
                    'debit_account':debit_account and debit_account.id or '',
                    'credit_account': credit_account and credit_account.id or '',
                    'tax_select': row_list[0],
                    'tax_report': name or '',
                    'base_amount': float(row_list[3].replace(',','')) or '',
                    'account_amount': account_amount or '',
                    'tax_rate': row_list[4],
                    'note': row_list[2],
                })
        if name == u'残疾人就业保障金缴费申报表':
            neirong = browser.find_elements_by_xpath("//tr [@ng-repeat='data in pringData']")
            for tr in neirong:
                text = tr.find_elements_by_tag_name("td")
                row_list = []
                for td in text[:-1]:  # 遍历每一个td
                    row_list.append(td.text)  # 取出表格的数据，并放入行列表里
                account_amount = float(row_list[8].replace(',', ''))
                if not account_amount:
                    continue
                tax_name = name
                credit_account = self.env['automatic.cost'].search([('name', '=', tax_name)]).category_id.account_id
                debit_account = self.env['automatic.cost'].search([('name', '=', tax_name)]).account_id
                self.env['tax.get.zjds.line'].create({
                    'order_id': self.id,
                    'debit_account':debit_account and debit_account.id or '',
                    'credit_account': credit_account and credit_account.id or '',
                    'tax_select': name,
                    'tax_report': name or '',
                    'base_amount': '',
                    'account_amount': account_amount or '',
                    'tax_rate': row_list[5].replace('%',''),
                })
        if name == u'印花税纳税申报（报告）表':
            neirong = browser.find_elements_by_xpath("//tr [@ng-repeat='data in yhsSbbGirdVO']")
            for tr in neirong:
                text = tr.find_elements_by_tag_name("td")
                row_list = []
                for td in text[:-1]:  # 遍历每一个td
                    row_list.append(td.text)  # 取出表格的数据，并放入行列表里
                #0税额跳过
                account_amount = float(row_list[5].replace(',', ''))
                if not account_amount:
                    continue
                tax_name = row_list[0]
                credit_account = self.env['automatic.cost'].search([('name', '=', tax_name)]).category_id.account_id
                debit_account = self.env['automatic.cost'].search([('name', '=', tax_name)]).account_id
                self.env['tax.get.zjds.line'].create({
                    'order_id': self.id,
                    'debit_account':debit_account and debit_account.id or '',
                    'credit_account': credit_account and credit_account.id or '',
                    'tax_select': row_list[0],
                    'tax_report': name or '',
                    'base_amount': float(row_list[2].replace(',','')) or '',
                    'account_amount': account_amount or '',
                    'tax_rate': row_list[4],
                })
        if name == u'房产税纳税申报表':
            neirong = browser.find_elements_by_xpath("//tr [@class='cztdhj']")
            for tr in neirong:
                text = tr.find_elements_by_tag_name("td")
                row_list = []
                for td in text:  # 遍历每一个td
                    row_list.append(td.text)  # 取出表格的数据，并放入行列表里
                #0税额跳过
                account_amount = float(row_list[-1].replace(',', ''))
                if not account_amount:
                    continue
                tax_name = name
                credit_account = self.env['automatic.cost'].search([('name', '=', tax_name)]).category_id.account_id
                debit_account = self.env['automatic.cost'].search([('name', '=', tax_name)]).account_id
                self.env['tax.get.zjds.line'].create({
                    'order_id': self.id,
                    'debit_account':debit_account and debit_account.id or '',
                    'credit_account': credit_account and credit_account.id or '',
                    'tax_select': tax_name,
                    'tax_report': name or '',
                    'base_amount': '',
                    'account_amount': account_amount or '',
                    'tax_rate': '',
                })
        if name == u'通用申报表':
            neirong = browser.find_elements_by_xpath("//tr [@ng-repeat='s in tysbbData']")
            for tr in neirong:
                text = tr.find_elements_by_tag_name("td")
                row_list = []
                for td in text[:-1]:  # 遍历每一个td
                    row_list.append(td.text)  # 取出表格的数据，并放入行列表里
                #0税额跳过
                account_amount = float(row_list[-1].replace(',', ''))
                if not account_amount:
                    continue
                tax_name = row_list[1]
                credit_account = self.env['automatic.cost'].search([('name', '=', tax_name)]).category_id.account_id
                debit_account = self.env['automatic.cost'].search([('name', '=', tax_name)]).account_id
                self.env['tax.get.zjds.line'].create({
                    'order_id': self.id,
                    'debit_account':debit_account and debit_account.id or '',
                    'credit_account': credit_account and credit_account.id or '',
                    'tax_select': tax_name,
                    'tax_report': name or '',
                    'base_amount': float(row_list[7].replace(',','')) or '',
                    'account_amount': account_amount or '',
                    'tax_rate': row_list[8],
                })

        browser.close()

#地税下载明细
class tax_get_zjds_line(models.Model):
    _name = 'tax.get.zjds.line'
    _description = 'tax get zjds line'

    order_id = fields.Many2one('tax.get.zjds', u'订单编号', index=True, copy=False,
                               required=True, ondelete='cascade')
    debit_account = fields.Many2one('finance.account', u'借方科目', copy=False)
    credit_account = fields.Many2one('finance.account', u'贷方科目', copy=False)
    tax_select = fields.Char(u'申报内容', help=u'申报表内的内容！')
    tax_report = fields.Char(u'申报表', help=u'申报表！')
    base_amount = fields.Float(u'计税依据', copy=False)
    tax_rate = fields.Char(u'费率', copy=False)
    account_amount = fields.Float(u'税额',  copy=False)
    note = fields.Char(u'备注', help=u'申报表内容的说明！')
    voucher_id = fields.Many2one('voucher', u'凭证', copy=False)