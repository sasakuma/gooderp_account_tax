# -*- coding: utf-8 -*-

import functools
import logging

import json

import werkzeug.utils
from werkzeug.exceptions import BadRequest

from odoo import api, http, SUPERUSER_ID, _
from odoo.exceptions import AccessDenied
from odoo.http import request
from odoo import registry as registry_get
import datetime


from odoo import http

_logger = logging.getLogger(__name__)


class Home(http.Controller):

    @http.route(['/tax_invoice/query_invoice'], type='http', auth='public')
    def query_invoice(self, *args, **kargs):
        res = {
            "code": 0,
            "msg": "查询成功！",
            "data": {


            }
        }
        if args:
            print args
        if kargs:
            print kargs
            if kargs['callback']:
                callback = kargs['callback']
                lines = request.env['tax.invoice.line'].sudo().search([('is_verified','=',False)], limit=1, order='id desc')
                if len(lines) > 0:
                    i=0
                    data=[]

                    for line in lines:
                        data.append({
                             "id": line.id,
                             "invoice_name": line.invoice_name,
                             "invoice_code" : line.invoice_code,
                             "invoice_amount":line.invoice_amount,
                             "invoice_open_date":line.invoice_open_date,
                        });
                    res["data"]=data

                else:
                    res["code"] = 1
                    res["msg"] = "没有未认证发票！"
            return callback + "(" + json.dumps(res) + ");"


    @http.route(['/tax_invoice/check_result'], type='http', auth='public')
    def check_result(self, *args, **kargs):
        res = {
            "code": 0,
            "msg": "更新成功！",
            "data": {

            }
        }
        if args:
            print args
        if kargs:
            #print kargs
            if kargs['callback']:
                callback = kargs['callback']
                #print kargs['data']
                invoice_id = (int)(kargs['id'])
                data = kargs['data']
                if len(data) > 0:
                    i=0
                    rows=data.split(u'○')
                    
                    for line in rows:
                        col=line.split(u'█')
                        val={
                             "line_id": invoice_id,
                             "product_name": col[0],
                             "product_type" : col[1],
                             "product_unit":col[2],
                             "product_count":col[3],
                             "product_price":col[4],
                             "product_amount":col[5],
                             "product_tax_rate":col[6],
                             "product_tax":col[7],

                        };
                        line_id=request.env['tax.invoice.line.detail'].sudo().create(val).id
                    request.env['tax.invoice.line'].sudo().browse(invoice_id).write({'is_verified':True})

                else:
                    res["code"] = 1
                    res["msg"] = "没有数据！"
            return callback + "(" + json.dumps(res) + ");"
