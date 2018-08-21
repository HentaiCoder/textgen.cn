#-*- coding: UTF-8 -*-

from selenium import webdriver
import time
import json


class Generator:
    def __init__(self, account, password):
        """
        getting the wechat account and password
        :param account: the wechat account
        :param password: pwd of the account
        """
        self.account = account
        self.password=password
        print("using generate() method...")

    def generate(self):
        driver = webdriver.Chrome()   #需要一个谷歌驱动的
        driver.get('https://mp.weixin.qq.com/')

        driver.find_element_by_xpath('//*[@id="header"]/div[2]/div/div/form/div[1]/div[1]/div/span/input').clear()   #保证重新开始输入
        driver.find_element_by_xpath('//*[@id="header"]/div[2]/div/div/form/div[1]/div[1]/div/span/input').send_keys(str(self.account))
        time.sleep(2)

        driver.find_element_by_xpath('//*[@id="header"]/div[2]/div/div/form/div[1]/div[2]/div/span/input').clear()
        driver.find_element_by_xpath('//*[@id="header"]/div[2]/div/div/form/div[1]/div[2]/div/span/input').send_keys(str(self.password))
        time.sleep(2)

        driver.find_element_by_xpath('//*[@id="header"]/div[2]/div/div/form/div[3]/label').click()
        time.sleep(3)

        driver.find_element_by_xpath('//*[@id="header"]/div[2]/div/div/form/div[4]/a').click()

        time.sleep(15)      #需要手动扫码
        cookies = driver.get_cookies()

        #print cookies                          #不是完整的cookies 不能够直接使用   每一项都是字典

        cookie = {}    # 创一个字典

        for items in cookies:
            cookie[items.get('name')] = items.get('value')

        with open('cookies.txt','w') as file:                    #把字典编程字符串  用json模块
            file.write(json.dumps(cookie))                        #写入转入字符串的字典