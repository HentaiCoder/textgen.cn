"""
    该模块主要读取数据库中储存的爬虫数据，利用jieba分词进行处理，并储存为切分文本，储存的本地
"""
import jieba
import os
import re
import time
from utils.transwarp.DAO import create_engine
from utils.transwarp.ORM import Model
from utils.transwarp.ORM import StringField, IntegerField, FloatField, BooleanField, TextField, BlobField, VersionField


class crawler_data(Model):
    """ ORM 模型类
    该类通过类名指定数据库名称，通过各变量实现数据库字段映射
    """
    id = IntegerField(primary_key=True, updatable=False)
    article_type = StringField()
    article_title = StringField()
    wechat_author = StringField()
    wechat_nickname = StringField()
    url = StringField()
    content = StringField()
    fetch_date = StringField()


class TextCutting():
    def __init__(self, database, host='localhost',  port=3306, user='root', password='********'):
        self.engine = create_engine(user=user, password=password, database=database,  host=host, port= port)
        stopwordspath = 'stopwords.txt'
        stopwords = open(stopwordspath, 'r', encoding='utf-8').readlines()
        self.stopwords = [w.strip() for w in stopwords]

    def _tokenization(self, text):
        """
        using jieba to cut single text
        使用结巴分词切分单个文本
        :param text: the chinese text to be cut
        :return: text after cut
        """
        result = []
        words = jieba.cut(text, cut_all=False)
        for word in words:
            if word not in self.stopwords:
                result.append(word)
        return result

    def _mkdir(self, folder_path):
        """
        create folder and get into the folder
        创建文件夹并进入
        :param folder_path: file folder to store the text
        :return:
        """
        path = folder_path.strip()
        isExist = os.path.exists(path)
        if not isExist:
            print('Creating File....')
            os.makedirs(path)
            print('Creating Success!')
        else:
            print('File Already Exist!')
        print('Shift to store file', folder_path)
        os.chdir(folder_path)

    def Cutting(self, max_item=10000):
        """
        Main function, using ORM object to fetch data from db and using jieba cutting the text
        主函数，使用ORM对象获取数据，并使用结巴分词切分文本
        :param max_item: the max number of corpus
        :return:
        """
        print("begin cutting...")
        fetcher = crawler_data().find_all()
        self._mkdir("./cuttext")
        rstr = r"[\/\\\:\*\?\"\<\>\|]"  # '/ \ : * ? " < > |'
        max_num = len(fetcher)
        if max_item > len(fetcher):
            print("the total number of articles({}) exceeds the limit, will fetching {} articles only, "
                  "if u wanna fetch more articles, pls turns up the limit".format(len(fetcher), max_item))
            time.sleep(3)
            max_num = max_item
        else:
            print("the total number of articles({}) is below the limit, it is enough?".format(max_num))
            time.sleep(3)
        index = 1
        for item in fetcher:
            if index < max_num:
                print("Text Number: {}, Start Process...".format(index))
                str_out = " ".join(self._tokenization(item.Content))
                name = re.sub(rstr, "_", item.article_title) + '.txt'
                try:
                    fo = open(name, 'w', encoding='utf-8')
                    fo.write(str_out)
                except Exception as e:
                    print("Text Number: {},  Cut Failed!".format(index))
                    index = index + 1
                    continue
                print("Text Number: {},  Cut Success!".format(index))
                index = index + 1

if __name__=='__main__':
    host = input("pls enter ur db host: ")
    port = int(input("pls enter ur db port: "))
    database = input("pls enter ur database name: ")
    user= input("pls enter ur user account: ")
    pwd = input("pls enter ur account password: ")
    cutter = TextCutting(database=database, host=host, port=port, user= user, password=pwd)
    cutter.Cutting(max_item=20000)