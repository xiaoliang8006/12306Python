# -*- coding: utf-8 -*-
"""
@time: 2018-11-04
@author: liangfh
"""

"""
Usage:
    python hack12306.py [-c] <configpath>
Options:
    -h,--help   显示帮助菜单
    -c          指定config.ini绝对路径
Example:
    python hack12306.py -c /usr/local/services/config.ini
    或者
    python hack12306.py
"""

from splinter.browser import Browser
from configparser import ConfigParser
from time import sleep
import traceback
import time, sys
import codecs
import argparse
import os
import time

class hackTickets(object):
    """docstring for hackTickets"""

    """读取配置文件"""
    def readConfig(self, config_file='config.ini'):
        print(u"加载配置文件...")
        # 补充文件路径，获得config.ini的绝对路径，默认为主程序当前目录
        path = os.path.join(os.getcwd(), config_file)

        cp = ConfigParser()
        try:
            # 指定读取config.ini编码格式，防止中文乱码（兼容windows）
            #cp.readfp(codecs.open(config_file, "r", "utf-8-sig"))
           cp.read_file(codecs.open(config_file,"r","utf-8-sig"))
        except IOError as e:
            print(u'打开配置文件"%s"失败, 请先创建或者拷贝一份配置文件config.ini' % (config_file))
            input('Press any key to continue')
            sys.exit()
        # 登录名
        self.username = cp.get("login", "username")
        # 密码
        self.passwd = cp.get("login", "password")
        # 始发站
        starts_city = cp.get("cookieInfo", "starts")
        # config.ini配置的是中文，转换成"武汉,WHN"，再进行编码
        self.starts = self.convertCityToCode(starts_city).encode('unicode_escape').decode("utf-8").replace("\\u", "%u").replace(",", "%2c")
        # 终点站
        ends_city = cp.get("cookieInfo", "ends");
        self.ends = self.convertCityToCode(ends_city).encode('unicode_escape').decode("utf-8").replace("\\u", "%u").replace(",", "%2c")
        # 乘车时间
        self.dtime = cp.get("cookieInfo", "dtime")
        # 车次
        orderStr = cp.get("orderItem", "order")
        # 配置文件中的是字符串，转换为int
        self.order = int(orderStr)
        # 乘客名
        self.users = cp.get("userInfo", "users").split(",")
        # 车次类型
        self.train_types = cp.get("trainInfo", "train_types").split(",")
        # 发车时间
        self.start_time = cp.get("trainInfo", "start_time")
        # 网址
        self.ticket_url = cp.get("urlInfo", "ticket_url")
        self.login_url = cp.get("urlInfo", "login_url")
        self.initmy_url = cp.get("urlInfo", "initmy_url")
        self.buy = cp.get("urlInfo", "buy")

        # 席别
        seat_type = cp.get("confirmInfo", "seat_type")
        self.seatType = self.seatMap[seat_type] if seat_type in self.seatMap else ""
        self.seatOrder = self.seatMap2[seat_type] if seat_type in self.seatMap2 else ""
        # 是否允许分配无座
        noseat_allow = cp.get("confirmInfo", "noseat_allow")
        self.noseat_allow = 1 if int(noseat_allow) != 0 else 0

        # 浏览器名称：目前使用的是chrome
        self.driver_name = cp.get("pathInfo", "driver_name")
        # 浏览器驱动（目前使用的是chromedriver）路径
        self.executable_path = cp.get("pathInfo", "executable_path")

    def loadConfig(self):
        parser = argparse.ArgumentParser()
        parser.add_argument('-c', '--config', help='Specify config file, use absolute path')
        args = parser.parse_args()
        if args.config:
            # 使用指定的配置文件
            self.readConfig(args.config)
        else:
            # 使用默认的配置文件config.ini
            self.readConfig()

    """
        加载映射文件，并将中文"武汉"转换成编码后的格式：“武汉,WHN“
    """
    def loadCityCode(self):
        print(u"映射出发地、目的地...")
        city_codes = {}
        path = os.path.join(os.getcwd(), 'city_code.txt')
        with codecs.open(path, "r", "utf-8-sig") as f:
            for l in f.readlines():
                city = l.split(':')[0]
                code = l.split(':')[1].strip()
                city_codes[city] = city + "," + code
        return city_codes

    def convertCityToCode(self, c):
        try:
            return self.city_codes[c]
        except KeyError:
            print(u"转换城市错误，请修改config.ini中starts或者ends值为中文城市名")
            return False

    """加载席别编码"""
    def loadSeatType(self):
        self.seatMap = {
            "硬座" : "1",
            "硬卧" : "3",
            "软卧" : "4",
            "商务座" : "9",
            "一等座" : "M",
            "二等座" : "O"
        }
        self.seatMap2 = {
            "硬座" : 9,
            "硬卧" : 7,
            "软卧" : 5,
            "商务座" : 1,
            "一等座" : 2,
            "二等座" : 3,
            "高级软卧" : 4
        }

    def __init__(self):
        # 读取城市中文与三字码映射文件，获得转换后到城市信息-- “武汉”: "武汉,WHN"
        self.city_codes = self.loadCityCode();

        # 加载席别
        self.loadSeatType()

        # 读取配置文件，获得初始化参数
        self.loadConfig();

    def login(self):
        print(u"开始登录...")
        # 登录
        self.driver.visit(self.login_url)
        # 自动填充用户名
        self.driver.fill("loginUserDTO.user_name", self.username)
        # 自动填充密码
        self.driver.fill("userDTO.password", self.passwd)
        print(u"等待验证码，自行输入...")
        # 验证码需要自行输入，程序自旋等待，直到验证码通过，点击登录
        while True:
            if self.driver.url != self.initmy_url:
                sleep(1)
            else:
                break
        print(u"登录成功！")

    """更多查询条件"""
    def searchMore(self):
        # 选择车次类型
        for type in self.train_types:
            # 车次类型选择
            train_type_dict = {'T': u'T-特快',                # 特快
                                'G': u'GC-高铁/城际',         # 高铁
                                'D': u'D-动车',               # 动车
                                'Z': u'Z-直达',               # 直达
                                'K': u'K-快速'                # 快速
                                }
            if type == 'T' or type == 'G' or type == 'D' or type == 'Z' or type == 'K':
                print('--------->Select train type', train_type_dict[type])
                self.driver.find_by_text(train_type_dict[type]).click()
            else:
                print("Train type exception or no choice!(train_type=%s)" % type)

        # 选择发车时间
        print('--------->Selection departure time', self.start_time)
        if self.start_time:
            self.driver.find_option_by_text(self.start_time).first.click()
        else:
            print(u"未指定发车时间，默认00:00-24:00")

    """填充查询条件"""
    def preStart(self):
        # 加载查询信息
        # 出发地
        self.driver.cookies.add({"_jc_save_fromStation": self.starts})
        # 目的地
        self.driver.cookies.add({"_jc_save_toStation": self.ends})
        # 出发日
        self.driver.cookies.add({"_jc_save_fromDate": self.dtime})

    def specifyTrainNo(self):
        count=0
        self.searchMore();
        while self.driver.url == self.ticket_url:
            # 勾选车次类型，发车时间            
            sleep(1)
            self.driver.find_by_text(u"查询").click()
            count += 1            
            print(u"循环点击查询... 第 %s 次" % count)
            try:
                sleep(0.3)
                row = self.driver.find_by_id('queryLeftTable').find_by_tag('tr')[self.order * 2 - 2]
                rema = row.find_by_tag('td')[self.seatOrder].text
                if (rema != "无") and (rema != "--"):
                    row.find_by_tag('td')[12].find_by_text(u"预订").click()
                sleep(0.3)
            except Exception as e:
                print(e)
                print(u"还没开始预订")
                continue

    def confirmOrder(self):
        print(u'选择乘客...')
        print(u"选择席别...")
        t=1
        for user in self.users:
            sleep(0.1)
            self.driver.find_by_text(user).last.click()
            if user.endswith(')'):
                self.driver.find_by_id('qd_closeDefaultWarningWindowDialog_id').click()
            sleep(0.1)
            if (t==1):
                self.driver.find_by_id('seatType_1').find_by_value(self.seatType).click()
                t = t+1
  
  
    def submitOrder(self):
        sleep(0.1)
        self.driver.find_by_id('submitOrder_id').click()
        print(u"已提交订单!")


    def confirmSeat(self):
        # 若提交订单异常，请适当加大sleep的时间
        sleep(1)
        self.driver.find_by_id('qr_submit_id').click()
        print(u"已确认选座!")
        print(u"抢票成功！请尽快支付...")

    def buyTickets(self):
        t = time.clock()
        try:
            print(u"购票页面开始...")
            # 填充查询条件
            self.preStart()
            # 带着查询条件，重新加载页面
            self.driver.reload()
            # 指定车次预订
            self.specifyTrainNo()
 
            print(u"开始预订...")

            sleep(0.2)
            # 选择用户,确认订单
            self.confirmOrder()
            # 提交订单
            self.submitOrder()
            # 确认选座
            self.confirmSeat()
            # print(time.clock() - t)
        except Exception as e:
            print(e)

    """入口函数"""
    def start(self):
        # 初始化驱动
        self.driver=Browser(driver_name=self.driver_name,executable_path=self.executable_path)
        # 初始化浏览器窗口大小
        self.driver.driver.set_window_size(1300, 700)

        # 登录，自动填充用户名、密码，自旋等待输入验证码，输入完验证码，点登录后，访问 tick_url（余票查询页面）
        self.login()

        # 登录成功，访问余票查询页面
        self.driver.visit(self.ticket_url)

        # 自动购买车票
        self.buyTickets();

if __name__ == '__main__':
    print("===========hack12306 begin===========")
    hackTickets = hackTickets()
    hackTickets.start()
