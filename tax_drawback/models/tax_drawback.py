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

class customs_declare(models.Model):
    _name = 'customs.declare'
    '''
    报关单音号，记销售日期，出口发票号，成交方式，运费，保费，杂费，币别，退税期间， 是否已退税'''
    name = fields.Char(u'报关单号', help=u'网址中#后的网址')
    date = fields.Date(u'记帐日期', help=u'报关单日期')
    invoice = fields.Char(u'发票号码', help=u'出口发票号')
    period_id = fields.Many2one('finance.period', u'退税期间')
    is_drawback = fields.Boolean(u'已退税')

class tax_drawback_updata(models.TransientModel):
    _name = 'tax.drawback.updata'
    _description = u'测试上传功能'
    password = fields.Char(u'密码', default=lambda self: self.env['config.country'].search([]).billing_password)

    def drawback_login(self):
        browser = webdriver.Chrome(chrome_options=options)
        try:
            browser.get('http://ckts.tonlan.com.cn:8080/start')
        except:
            raise UserError(u'网页打不开，请确认')
        browser.implicitly_wait(10)
        browser.find_element_by_id("userPass").send_keys(self.password)
        browser.implicitly_wait(10)
        login_button = browser.find_element_by_id("loginBtn")
        login_button.click()