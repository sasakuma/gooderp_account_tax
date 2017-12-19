// ==UserScript==
// @name         税务查询
// @namespace    http://tampermonkey.net/
// @version      0.1
// @description  try to take over the world!
// @author       You
// @match        https://inv-veri.chinatax.gov.cn/
// @grant        none
// ==/UserScript==


(function() {
    'use strict';
    var host='http://localhost:8888';

    var isQuery=false;


    /*
    window.timerQuery=function(){
        if(!isQuery) return;



        setTimeout(function(){timerQuery();},5*1000);



    };


    window.beginQuery=function(){
        if($('#btnQuery').html()=='开始查询')
        {
            $('#btnQuery').html('停止查询');
            isQuery=true;
            timerQuery();
        }
        else
        {
            $('#btnQuery').html('开始查询');
            isQuery=false;
        }
    };
    */


    window.beginQuery=function(){

        $.ajax({
            type : "GET",
            url : host+"/tax_invoice/query_invoice?callback=?",
            dataType : "jsonp",
            jsonp: 'callback',
            success : function(json){
                console.log(json);
                //alert(json.code);
                if(json.code==0)
                {
                    $('#id').val(json.data[0].id);

                    $('#fpdm').val(json.data[0].invoice_code);
                    $('#fphm').val(json.data[0].invoice_name);
                    $('#kprq').val(json.data[0].invoice_open_date.replace('-','').replace('-',''));
                    $('#kjje').val(json.data[0].invoice_amount);
                    $("#fpdm").keyup();
                    $("#fphm").keyup();
                    $("#kprq").keyup();
                    $("#kjje").keyup();

                    getYzmXx();

                }
                else
                {
                    alert(json.msg);
                }

            }
        });
    };

    window.checkfp=function() {
        var fpdm = $("#fpdm").val().trim();
        var fphm = $("#fphm").val().trim();
        var kprq = $("#kprq").val().trim();
        var dmchek = getSwjg(fpdm, 1);
        if (dmchek.length > 0) {
            var DATE_FORMAT = /^[0-9]{4}[0-1]?[0-9]{1}[0-3]?[0-9]{1}$/;
            if (DATE_FORMAT.test(kprq)) {

            } else {
                jAlert("日期格式错误，为YYYYMMDD格式！", "提示");
                return;
            }
            var kjje = $("#kjje").val().trim();
            if (aur()) {
                $('#checkfp').hide();
                $('#uncheckfp').show();
                var date = new Date();

                var yzm = $("#yzm").val().trim();
                var setText = "";

                var param = null;
                var url = "";

                var iterationCount = 100;
                var keySize = 128;
                iv = CryptoJS.lib.WordArray.random(128 / 8).toString(CryptoJS.enc.Hex);
                salt = CryptoJS.lib.WordArray.random(128 / 8).toString(CryptoJS.enc.Hex);
                var aesUtil = new AesUtil(keySize, iterationCount);

                if (avai(fplx)) {

                    if (fplx == "01" || fplx == "02" || fplx == "03") {
                        var index = kjje.indexOf(".");
                        if (index > 0) {
                            var arr = kjje.split(".");
                            if (arr[1] == "00" || arr[1] == "0") {
                                kjje = arr[0];
                            } else if (arr[1].charAt(1) == "0") {
                                kjje = arr[0] + "." + arr[1].charAt(0);
                            }
                        }
                    }



                    param = {
                        'fpdm': fpdm,
                        'fphm': fphm,
                        'kprq': kprq,
                        'fpje': kjje,
                        'fplx': fplx,
                        'yzm': yzm,
                        'yzmSj': yzmSj,
                        'index': jmmy,
                        'iv': iv,
                        'salt': salt,
                        'publickey':$.ck(fpdm,fphm,kjje, kprq, yzmSj, yzm)

                    };
                    delayMessage = "发票查验请求失败!";
                    showTime();

                    url = ip + "/query";
                    $.ajax({
                        type: "post",
                        url: url,
                        dataType: "jsonp",
                        data: param,
                        jsonp: "callback",
                        success: function(jsonData) {
                            console.log(jsonData);





                            delayFlag = "1";
                            var cyjgdm = jsonData.key1;

                            if (cyjgdm == "1") {
                                show_yzm = "";
                                jAlert("该省尚未开通发票查验功能！", "提示");
                            } else if (cyjgdm == "001") {

                                show_yzm = "";
                                var t = jsonData.key5;
                                //alert(t);


                                // 在这里把结果传给odoo
                                // 王▽子▽1▽2▽0▽克▽双▽铜▽█865*720█吨█30.4944█4829.059829059829█147259.28█17█25034.08○王▽子▽1▽5▽0▽克▽双▽铜▽█889*1194█吨█5.3735█4957.264957264957█26637.86█17█4528.44○王▽子▽1▽5▽0▽克▽双▽铜▽█870*597█吨█24.7173█4957.264957264957█122530.21█17█20830.13
                                //var jsonData='王▽子▽1▽2▽0▽克▽双▽铜▽█865*720█吨█30.4944█4829.059829059829█147259.28█17█25034.08○王▽子▽1▽5▽0▽克▽双▽铜▽█889*1194█吨█5.3735█4957.264957264957█26637.86█17█4528.44○王▽子▽1▽5▽0▽克▽双▽铜▽█870*597█吨█24.7173█4957.264957264957█122530.21█17█20830.13';
                                var key3= jsonData.key3;

                                var data=key3.replace(new RegExp('▽', 'g'), '');



                                $.ajax({
                                    type : "GET",
                                    url : host+"/tax_invoice/check_result?callback=?&id="+$('#id').val()+"&data="+data,
                                    dataType : "jsonp",
                                    //data:data,
                                    jsonp: 'callback',
                                    success : function(json){
                                        console.log(json);
                                        //alert(json.code);
                                        if(json.code==0)
                                        {
                                            alert(json.msg);
                                            beginQuery();
                                        }
                                        else
                                        {
                                            alert(json.msg);
                                        }
                                    }
                                });



                                eval(t);


                                var hwxx = jsonData.key3;
                                var jmbz = "";
                                if (jsonData.key4.trim() != '') {
                                    jmbz = aesUtil.decrypt(jsonData.key8, jsonData.key7, jsonData.key9, jsonData.key4);
                                }
                                var jmsort = aesUtil.decrypt(jsonData.key8, jsonData.key7, jsonData.key9, jsonData.key10);
                                var tt = jsonData.key6;
                                jsname = jsonData.key11 + ".js";


                                //alert(tt);



                                eval(tt);
                                //alert(tt);




                                if (browser == "edge" || browser == "firefox") {
                                    sessionStorage["jsname"] = jsname;
                                    $.getScript("js/" + jsname,
                                                function() {
                                        bb();
                                        show_dialog(1100, 700, "cyjgedge" + fplx + ".html", result);
                                    });
                                } else if (browser == "ie8") {
                                    sessionStorage["jsname"] = jsname;
                                    sessionStorage["browser"] = "ie8";
                                    var str = JSON.stringify(result);
                                    sessionStorage["result"] = str;
                                    $.getScript("js/" + jsname,
                                                function() {
                                        bb();
                                        show_dialog(1100, 700, "cyjgedge" + fplx + ".html", result);
                                    });
                                } else {
                                    sessionStorage["jsname"] = jsname;
                                    $.getScript("js/" + jsname,
                                                function() {
                                        sessionStorage["rule"] = rule;
                                        window.showModalDialog('cyjg' + fplx + '.html', result, "dialogTop:10px;dialogWidth:1100px;dialogHeight:700px;");
                                    });
                                }
                            } else if (cyjgdm == "002") {
                                show_yzm = "";
                                jAlert("超过该张发票当日查验次数(请于次日再次查验)!", "提示",
                                       function(r) {
                                    if (r) {
                                        arw();
                                    }
                                });
                            } else if (cyjgdm == "003") {
                                show_yzm = "";
                                jAlert("发票查验请求太频繁，请稍后再试！", "提示",
                                       function(r) {
                                    if (r) {

                                    }
                                });
                            } else if (cyjgdm == "004") {
                                show_yzm = "";
                                jAlert("超过服务器最大请求数，请稍后访问!", "提示",
                                       function(r) {
                                    if (r) {
                                    }
                                });
                            } else if (cyjgdm == "005") {
                                show_yzm = "";
                                jAlert("请求不合法!", "提示",
                                       function(r) {
                                    if (r) {
                                    }
                                });
                            } else if (cyjgdm == "020") {
                                show_yzm = "";
                                jAlert("由于查验行为异常，涉嫌违规，当前无法使用查验服务！", "提示",
                                       function(r) {
                                    if (r) {
                                    }
                                });
                            } else if (cyjgdm == "006") {
                                var key2222 = jsonData.key2;
                                var key3333 = jsonData.key3;
                                show_yzm = "";
                                setText = "不一致";
                                param = {
                                    'fplx': fplx,
                                    'swjg': swjgmc,
                                    'fpdm': fpdm,
                                    'fphm': fphm,
                                    'kprq': kprq,
                                    'kjje': kjje,
                                    'cysj': yzmSj,
                                    'setText': setText,
                                    'key2222':key2222,
                                    'key3333':key3333
                                };
                                if (browser == "edge" || browser == "firefox") {
                                    show_dialog(800, 400, "jgbyz.html", param);
                                } else {
                                    window.showModalDialog('jgbyz.html', param, "dialogWidth:800px;dialogHeight:400px;center:yes;scroll:no");
                                }
                            } else if (cyjgdm == "007") {
                                show_yzm = "";
                                jAlert("验证码失效!", "提示",
                                       function(r) {
                                    if (r) {
                                    }
                                });
                            } else if (cyjgdm == "008") {
                                show_yzm = "";
                                jAlert("验证码错误!", "提示",
                                       function(r) {
                                    if (r) {
                                    }
                                });
                            } else if (cyjgdm == "009") {
                                var key2222 = jsonData.key2;
                                var key3333 = jsonData.key3;
                                show_yzm = "";
                                setText = "查无此票";
                                param = {
                                    'fplx': fplx,
                                    'swjg': swjgmc,
                                    'fpdm': fpdm,
                                    'fphm': fphm,
                                    'kprq': kprq,
                                    'kjje': kjje,
                                    'cysj': yzmSj,
                                    'setText': setText,
                                    'key2222':key2222,
                                    'key3333':key3333
                                };
                                if (browser == "edge" || browser == "firefox") {
                                    show_dialog(800, 400, "jgbyz.html", param);
                                } else {
                                    window.showModalDialog('jgbyz.html', param, "dialogWidth:800px;dialogHeight:400px;center:yes;scroll:no");
                                }
                            } else if (cyjgdm == "rqerr") {
                                show_yzm = "";
                                jAlert("当日开具发票可于次日进行查验！", "警告");
                            } else if (cyjgdm == "010") {
                                show_yzm = "";
                                var etype = jsonData.key2;
                                if (etype == 'inredis') {
                                    etype = "(02)";
                                } else if (etype == 'weberr') {
                                    etype = "(03)";
                                }
                                jAlert("网络超时，请重试！" + etype, "系统错误",
                                       function(r) {
                                    if (r) {
                                    }
                                });
                            } else if (cyjgdm == "010_") {
                                show_yzm = "";
                                jAlert("网络超时，请重试！(05)", "系统错误",
                                       function(r) {
                                    if (r) {}
                                });
                            } else {
                                show_yzm = "";
                                jAlert("网络超时，请重试！(04)", "系统错误",
                                       function(r) {
                                    if (r) {
                                    }
                                });
                            }
                            $('#uncheckfp').hide();
                            $('#checkfp').show();
                            //yzmSj = "";

                        },
                        error: function(XMLHttpRequest, textStatus, errorThrown){
                        }
                    });
                }
            }
        }

    };

    window.do_check=function(){
       checkfp();
    };

    window.Test=function(){
        // 王▽子▽1▽2▽0▽克▽双▽铜▽█865*720█吨█30.4944█4829.059829059829█147259.28█17█25034.08○王▽子▽1▽5▽0▽克▽双▽铜▽█889*1194█吨█5.3735█4957.264957264957█26637.86█17█4528.44○王▽子▽1▽5▽0▽克▽双▽铜▽█870*597█吨█24.7173█4957.264957264957█122530.21█17█20830.13
        var jsonData='王▽子▽1▽2▽0▽克▽双▽铜▽█865*720█吨█30.4944█4829.059829059829█147259.28█17█25034.08○王▽子▽1▽5▽0▽克▽双▽铜▽█889*1194█吨█5.3735█4957.264957264957█26637.86█17█4528.44○王▽子▽1▽5▽0▽克▽双▽铜▽█870*597█吨█24.7173█4957.264957264957█122530.21█17█20830.13';


        var data=jsonData.replace(new RegExp('▽', 'g'), '');



        $.ajax({
            type : "GET",
            url : host+"/tax_invoice/check_result?callback=?&id="+$('#id').val()+"&data="+data,
            dataType : "jsonp",
            //data:data,
            jsonp: 'callback',
            success : function(json){
                console.log(json);
                //alert(json.code);
                if(json.code==0)
                {
                    alert(json.msg);
                }
                else
                {
                    alert(json.msg);
                }
            }
        });
    };


    jQuery(document).ready(function () {
        //alert('11111');
        var html='';
        html+='<button onClick="beginQuery()" id="btnQuery">读取未认证发票</button>';

        $('.comm_table2').prepend('<tr><td class="align_right2">ID：</td><td width=200><input id="id"></input></td></tr><tr><td class="align_right2">自动查询：</td><td width=200>'+html+'</td></tr>');

        html='<button class="blue_button" style="cursor: default;" id="btncheck" onclick="do_check()">查验并提交给ERP</button>';
        //html+='<button class="blue_button" style="cursor: default;" id="btnTest" onclick="Test()">Test</button>';

        $('.comm_btn_div2').prepend(html);


			var script = document.createElement('script');
			script.setAttribute('type', 'text/javascript');
			script.setAttribute('src', host+'/web/static/lib/qweb/qweb2.js');
			document.getElementsByTagName('head')[0].appendChild(script);


    });

    // Your code here...
})();