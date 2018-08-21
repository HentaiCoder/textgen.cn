import requests
import random
import time
from bs4 import BeautifulSoup


class Download:
    def __init__(self):
        """
        initializing the ip pool and UA pool
        """
        self.iplist=[]
        html=requests.get(url="http://www.xicidaili.com/", headers={'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36'})
        soup = BeautifulSoup(html.text, 'lxml')
        iplisten = soup.select("table#ip_list tr.odd", limit=20)
        for ip in iplisten:
            self.iplist.append(ip.contents[3].string.strip())

        self.user_agent_list = [
            "Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_8; en-us) AppleWebKit/534.50 (KHTML, like Gecko) Version/5.1 Safari/534.50",
            "Mozilla/5.0 (Windows; U; Windows NT 6.1; en-us) AppleWebKit/534.50 (KHTML, like Gecko) Version/5.1 Safari/534.50",
            "Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; Trident/5.0)",
            "Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.0; Trident/4.0)",
            "Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.0)",
            "Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1)",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.6; rv,2.0.1) Gecko/20100101 Firefox/4.0.1",
            "Opera/9.80 (Macintosh; Intel Mac OS X 10.6.8; U; en) Presto/2.8.131 Version/11.11",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_7_0) AppleWebKit/535.11 (KHTML, like Gecko) Chrome/17.0.963.56 Safari/535.11",
            "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.1 (KHTML, like Gecko) Chrome/22.0.1207.1 Safari/537.1",
            "Mozilla/5.0 (X11; CrOS i686 2268.111.0) AppleWebKit/536.11 (KHTML, like Gecko) Chrome/20.0.1132.57 Safari/536.11",
            "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/536.6 (KHTML, like Gecko) Chrome/20.0.1092.0 Safari/536.6",
            "Mozilla/5.0 (Windows NT 6.2) AppleWebKit/536.6 (KHTML, like Gecko) Chrome/20.0.1090.0 Safari/536.6",
            "Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/537.1 (KHTML, like Gecko) Chrome/19.77.34.5 Safari/537.1",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/536.5 (KHTML, like Gecko) Chrome/19.0.1084.9 Safari/536.5",
            "Mozilla/5.0 (Windows NT 6.0) AppleWebKit/536.5 (KHTML, like Gecko) Chrome/19.0.1084.36 Safari/536.5",
            "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1063.0 Safari/536.3",
            "Mozilla/5.0 (Windows NT 5.1) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1063.0 Safari/536.3",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_8_0) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1063.0 Safari/536.3",
            "Mozilla/5.0 (Windows NT 6.2) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1062.0 Safari/536.3",
            "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1062.0 Safari/536.3",
            "Mozilla/5.0 (Windows NT 6.2) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1061.1 Safari/536.3",
            "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1061.1 Safari/536.3",
            "Mozilla/5.0 (Windows NT 6.1) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1061.1 Safari/536.3",
            "Mozilla/5.0 (Windows NT 6.2) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1061.0 Safari/536.3",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/535.24 (KHTML, like Gecko) Chrome/19.0.1055.1 Safari/535.24",
            "Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/535.24 (KHTML, like Gecko) Chrome/19.0.1055.1 Safari/535.24"
            ]

    def request(self, search_url, cookies, data, headers, proxy=None, num_retries=6):
        """
        Fetching layer for each post
        :param search_url: the url which receive the post request
        :param cookies: cookies is needed to bypass the authorization
        :param data: post form data
        :param headers: some camouflage to confuse the web's anti-crawler
        :param proxy: setting the ip proxy for request if needed
        :param num_retries: number of retry for each post, if failed using alternative( main ip -> proxy, proxy-> main ip)
        :return:None or Response Body
        """
        UA = random.choice(self.user_agent_list)
        headers['User-Agent'] = UA
        if proxy is None:
            try:
                return requests.post(url=search_url, data=data, cookies=cookies, headers=headers)
            except Exception as e:
                if num_retries > 0:
                    print('Requesting url failed, retry after 1s...')
                    time.sleep(1)
                    return self.request(search_url=search_url, cookies=cookies, data=data, headers=headers, proxy=proxy,  num_retries=num_retries - 1)
                else:
                    print('Retried too many times, consider using IP Proxy')
                    if len(self.iplist) == 0:
                        print("The IP pool don't contain any useful proxy, FAILURE!")
                        print("Retrieve the ip proxy and skip this post...")
                        html = requests.get(url="http://www.xicidaili.com/", headers={
                            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36'})
                        soup = BeautifulSoup(html.text, 'lxml')
                        iplisten = soup.select("table#ip_list tr.odd", limit=20)
                        for ip in iplisten:
                            self.iplist.append(ip.contents[3].string.strip())
                        return None
                    proxy = {'http': random.choice(self.iplist).strip()}
                    print("IP: {}".format(proxy['http']))
                    return self.request(search_url=search_url, cookies=cookies, data=data, headers=headers, proxy=proxy,
                                 num_retries=4)
        else:
            try:
                return requests.post(url=search_url, data=data, cookies=cookies, headers=headers)
            except Exception as e:
                if num_retries>0:
                    print('Requesting url failed, retry after 2s...')
                    time.sleep(2)
                    return self.request(search_url=search_url, cookies=cookies, data=data, headers=headers, proxy=proxy,
                                 num_retries=num_retries - 1)
                else:
                    print("Retried to many times, cancel using IP Proxy")
                    self.iplist.remove(proxy['http'])
                    print("{} proxies lasting....".format(len(self.iplist)))
                    return self.request(search_url=search_url, cookies=cookies, data=data, headers=headers, proxy=None,
                                 num_retries=6)