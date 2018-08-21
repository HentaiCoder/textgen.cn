import pymysql
import json
import random
import requests
import re
import time
from bs4 import BeautifulSoup
from utils.WeChatCrawler.cookie_generator import Generator
from utils.WeChatCrawler.download import Download

"""
@Author: 张琪琪&lee
@Date: 2018-8-21
@Version: 1.0.1
此爬虫用作对微信公众号文章的爬取，v1只是用作关键词搜索，请将search_type设置为True
"""
class Crawler(Download):
    def __init__(self, keyword, hostname, username, password, schema, tablename, search_type=True):
        """
        initializing the WeChat crawler(mainly setup the local db), input some key params and generate the cookies
        :param keyword: the searching words
        :param search_type: the searching method: by_type: True or by_author: False
        """
        Download.__init__(self)
        self.query = keyword
        self.search_type = search_type
        self.headers = {'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36'}
        self.db = pymysql.connect(str(hostname),str(username),str(password), str(schema))
        self.tablename=tablename
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
            response = self.request(search_url=search_url, cookies=cookies, data=data, headers=headers, proxy=None, num_retries=6)
            max_num = response.json().get('total')
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
                            print("Title: "+article.get("title"))
                            print("Author: "+article.get("author"))
                            content = self.analyzer(article['content'])
                            #print(content)
                            sql = """
                                    INSERT INTO {}(article_type, article_title, wechat_author, wechat_nickname, fetch_date, url, Content)
                                    VALUES('{}','{}','{}','{}',now(), '{}','{}')
                            """.format(self.tablename, article['article_type'], article['title'], article['author'], article['nickname'], article['url'], self.tablename)
                            try:
                                cursor.execute(sql)
                                self.db.commit()
                                print("INSERTION SUCCESS!")
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
        #  TF-IDF method