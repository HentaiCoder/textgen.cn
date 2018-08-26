import pymysql
import json
import random
import requests
import re
import time
import threading
import multiprocessing
import os
from bs4 import BeautifulSoup
from utils.WeChatCrawler.download import Download
from utils.WeChatCrawler.cookie_generator import Generator

"""
@Author: 张琪琪&lee
@Date: 2018-8-5
此爬虫用作对微信公众号文章的爬取，v1只是用作关键词搜索，请将search_type设置为True
"""
class WeChatCrawler(Download, threading.Thread):
    def __init__(self, keyword, hostname,port, username, password, schema, tablename, search_type=True):
        """
        initializing the WeChat crawler(mainly setup the local db), input some key params and generate the cookies
        :param keyword: the searching words
        :param search_type: the searching method: by_type: True or by_author: False
        """
        Download.__init__(self)
        threading.Thread.__init__(self)
        self.query = keyword
        self.search_type = search_type
        self.headers = {'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36'}
        self.db = pymysql.connect(str(hostname),str(username),str(password), str(schema),port=port)
        self.tablename=tablename
        if not os.path.exists('cookies.txt'):
            account = input("pls enter ur wechat account: ")
            pwd = input("pls enter ur wechat password: ")
            generator = Generator(account=account, password=pwd)
            generator.generate()
        cursor = self.db.cursor()
        sql = """CREATE TABLE IF NOT EXISTS {} (
                        id INT NOT NULL AUTO_INCREMENT,
                        article_type TINYTEXT NOT NULL,
                        article_title TINYTEXT NOT NULL, 
                        wechat_author TINYTEXT NOT NULL,
                        wechat_nickname TINYTEXT NOT NULL,
                        fetch_date DATETIME NOT NULL,
                        url TINYTEXT NOT NULL,
                        Content TEXT NOT NULL,
                        PRIMARY KEY (id)
                        )  ENGINE=INNODB
                            DEFAULT CHARACTER SET utf8mb4""".format(tablename)
        cursor.execute(sql)

    def crawling(self, max_article=10000):
        """
        Main function, it will calling request to fetch data and analyzer to store specific data into db
        :param max_article: limit for max article number
        :return:
        """
        if self.search_type:
            search_url = 'https://mp.weixin.qq.com/cgi-bin/operate_appmsg?sub=check_appmsg_copyright_stat'
            headers = {
                'User-Agent': 'Opera/9.80 (Macintosh; Intel Mac OS X 10.6.8; U; en) Presto/2.8.131 Version/11.11',
                'Referer': 'https://mp.weixin.qq.com/cgi-bin/appmsg?t=media/appmsg_edit_v2&action=edit&isNew=1&type=10&share=1&token=738037669&lang=zh_CN',
                'Host': 'mp.weixin.qq.com'
            }
            with open('cookies.txt', 'r') as file:
                cookie = file.read()
            cookies = json.loads(cookie)
            response = requests.get(url='https://mp.weixin.qq.com/', headers=headers, cookies=cookies)
            token = re.findall(r'token=(\d+)', str(response.url))[0]
            print(token)
            data = {
                'token': token,
                'lang': 'zh_CN',
                'f': 'json',
                'ajax': '1',
                'random': random.random(),
                'url': self.query,
                'begin': '0',
                'count': '20',
            }
            while True:
                try:
                    response = self.request(search_url=search_url, cookies=cookies, data=data, headers=headers, proxy=None, num_retries=6)
                    max_num = response.json().get('total')
                except Exception as e:
                    print("Bad Response, try to regain the data after 2s...")
                    time.sleep(2)
                if max_num is not None:
                    break

            if max_num > max_article:
                print("the total number of articles({}) exceeds the limit, crawler will fetching {} articles only, "
                      "if u wanna fetch more articles, pls turns up the limit".format(max_num, max_article))
                time.sleep(3)
                max_num = max_article
            else:
                print("the total number of articles({}) is below the limit, it is enough?".format(max_num))
                time.sleep(3)

            begin = 0  #  each post will start from the position of begin
            index = 0

            while max_num> begin-int(data['count']):
                data['begin']='{}'.format(begin)
                response = self.request(search_url=search_url, cookies=cookies, data=data, headers=headers, proxy=None,
                                        num_retries=6)
                if response is not None:
                    article_list = response.json().get("list")
                    if article_list is not None:
                        former_index = index
                        for article in article_list:
                            cursor = self.db.cursor()
                            sql = """
                                    SELECT 
                                        id
                                    FROM
                                        {}
                                    WHERE
                                        url='{}'
                            """.format(self.tablename, article.get('url'))
                            try:
                                cursor.execute(sql)
                                res = cursor.fetchone()
                                if res:
                                    print(index)
                                    print("This article is already analyzed!")
                                    index +=1
                                    continue
                            except pymysql.Error as e:
                                print("error occurred in ELIMINATION operation! ")
                                self.db.rollback()
                                continue
                            print(index)
                            rstr = r"[\/\\\:\*\?\"\<\>\|]"  # '/ \ : * ? " < > |'
                            title = re.sub(rstr, "_", article['title'])
                            print("Title: "+title)
                            print("Author: "+article.get("author"))
                            content = self.analyzer(article['content'])

                            sql = """
                                    INSERT INTO {}(article_type, article_title, wechat_author, wechat_nickname, fetch_date, url, Content)
                                    VALUES('{}','{}','{}','{}',now(), '{}','{}')
                            """.format(self.tablename, article['article_type'], title, article['author'], article['nickname'], str(article['url']), content)
                            try:
                                cursor.execute(sql)
                                self.db.commit()
                                print("INSERTION SUCCESS! " +
                                      "Thread info: "+threading.currentThread().name+", "+str(threading.currentThread().ident)+
                                      ". Process info:" + multiprocessing.current_process().name+", "+str(multiprocessing.current_process().ident))
                            except pymysql.Error as e:
                                print(repr(e))
                                print("Error occurred in INSERT operation!")
                                self.db.rollback()
                                continue
                            index += 1
                        begin += index-former_index
                    else:
                        print(response.text)
                        print("Bad Response, try to regain the data after 2s...")
                        time.sleep(2)
                else:
                    print("requesting error!")
                    time.sleep(10)

        else:
            print("Next version coming soon...")

    def analyzer(self, html):
        soup = BeautifulSoup(html, 'lxml')
        return soup.get_text()

    def dedup(self, article):
        """
        this function mainly focus on the deduplication of articles, using url method and tf-idf(similarity) method
        in this function, url will be used firstly to eliminate the same article which is already in db, and then,
        using similarity(compute by some target articles which are given in advance) to eliminate the less-relevance article
        :param article: incoming article
        :return: True: distinct or False: duplicated
        """
        #  URL method
        cursor = self.db.cursor()
        sql = """
                                            SELECT 
                                                id
                                            FROM
                                                {}
                                            WHERE
                                                url='{}'
                                    """.format(self.tablename, article.get('url'))
        try:
            cursor.execute(sql)
            res = cursor.fetchone()
            if res:
                print("This article is already analyzed!")
                return False
        except pymysql.Error as e:
            print("error occurred in ELIMINATION operation! ")
            self.db.rollback()
            return False


def _spidertask(tasks, hostname,port, username, password, schema, tablename, search_type=True):
    spider = WeChatCrawler(keyword=None, hostname=hostname, port=int(port), username=username, password=password, schema=schema, tablename=tablename, search_type=search_type)
    for task in tasks:
        spider.query=task
        spider.crawling(max_article=35000)

def _taskAssign(tasklist, hostname,port, username, password, schema, tablename, search_type=True, thread_num=4):
    div_length = int(len(tasklist) / thread_num + 0.5)
    div_length = div_length if div_length>=1 else 1
    threads = []
    for i in range(0, len(tasklist), div_length):
        tasks = tasklist[i:i+div_length]
        thread = threading.Thread(target=_spidertask, args=(tasks, hostname, port, username, password, schema, tablename, search_type))
        threads.append(thread)
        thread.setDaemon(True)
        thread.start()
    for thread in threads:
        thread.join()

def spiderScheduler(hostname,port, username, password, schema, tablename, search_type=True, workers=3, thread_num=4):
    spiderlistpath = 'spider_list.txt'
    spiderlist = open(spiderlistpath, 'r', encoding='utf-8').readlines()
    spiderlist = [w.strip() for w in spiderlist]
    spidertasks = []
    for item in spiderlist:
         if item not in spidertasks:
             spidertasks.append(item)
    div_length = int(len(spidertasks)/workers+0.5)
    processlist = []
    for i in range(0, len(spidertasks), div_length):
        tasklist = spidertasks[i:i+div_length]
        process = multiprocessing.Process(target=_taskAssign, args=(tasklist, hostname, port, username, password, schema, tablename, search_type, thread_num))
        processlist.append(process)
        process.start()
    for process in processlist:
        process.join()


if __name__=='__main__':
    crawler = WeChatCrawler(keyword="互联网金融",hostname="140.143.116.206", port=10015 , username="root", password="text1023", schema="corpus", tablename="crawler_data", search_type=True)
    crawler.crawling(max_article=30000)