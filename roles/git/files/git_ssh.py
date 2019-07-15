# coding: utf-8
# __author__: ""
from __future__ import unicode_literals

import requests
from lxml import etree
import argparse


class GitSSH:
    '''
    该类用来自动在 gogs(git托管工具) 上进行添加 ssh 项目部署 key
    在 ansible 的本地执行
    '''
    def __init__(self, user_name, password):
        self.user_name = user_name
        self.password = password
        self.base_url = "http://git.marcpoint.com"
        self.headers = {
            "Accept": "application/json, text/javascript, */*; q=0.01",
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36',
        }
        self.cookies = {}
        self.login()

    def login(self):
        '''
        登录 并获取 cookies
        :param user_name:
        :param password:
        :return:
        '''
        url = self.base_url + "/user/login"
        login_get = requests.get(url, headers=self.headers)

        # 获取初始化的 cookies
        login_csrf = etree.HTML(login_get.text).xpath('//input[@name="_csrf" and @type="hidden"]/@value')[0]
        self.cookies = login_get.cookies.get_dict()

        # 登录使 i_like_gogs 生效
        self.headers.update(Cookie='lang={lang}; i_like_gogs={i_like_gogs}; _csrf={_csrf}'.format(**self.cookies))
        data = {'user_name': self.user_name, 'password': self.password, 'login_source': "1", '_csrf': login_csrf}
        import pdb
        pdb.set_trace()
        requests.post(url, headers=self.headers, data=data)

        # 访问 home 页获取最终 _csrf
        self.headers.update(Cookie='lang={lang}; i_like_gogs={i_like_gogs};'.format(**self.cookies))
        home_page = requests.get(self.base_url, headers=self.headers)

        self.cookies.update(
            _csrf=home_page.cookies.get("_csrf"),
            o_csrf=etree.HTML(home_page.text).xpath("//meta[@name='_csrf']/@content")[0]
        )

    def get_keyid(self, key_name, project):
        '''
        通过 秘钥 名称 获取秘钥 id
        :param key_name:
        :param project: 所属项目
        :return:
        '''
        url = self.base_url + "/server/{0}/settings/keys".format(project)
        self.headers.update(Cookie='lang={lang}; i_like_gogs={i_like_gogs}; _csrf={_csrf}'.format(**self.cookies))
        xpather = etree.HTML(requests.get(url, headers=self.headers).text)

        elements = xpather.xpath("//div[@class='item ui grid']")
        key_id = None
        for element in elements:
            name = element.xpath("div[@class='eleven wide column']/strong/text()")[0]
            if name == key_name:
                key_id = element.xpath("div[@class='two wide column']/button/@data-id")[0]
                break

        return key_id

    def delete_key(self, key_id, project):
        '''
        删除 key
        :param key_id:
        :param project: 所属项目
        :return:
        '''
        url = self.base_url + "/server/{0}/settings/keys/delete".format(project)
        self.headers.update(Cookie='lang={lang}; i_like_gogs={i_like_gogs}; _csrf={_csrf}'.format(**self.cookies))

        data = dict(
            id=key_id,
            _csrf=self.cookies["o_csrf"]
        )
        requests.post(url, headers=self.headers, data=data)

    def add_key(self, key_name, key_text, project):
        '''
        删除 key
        :param key_name:
        :param key_text:
        :param project: 所属项目
        :return:
        '''
        url = self.base_url + "/server/{0}/settings/keys".format(project)
        self.headers.update(Cookie='lang={lang}; i_like_gogs={i_like_gogs}; _csrf={_csrf}'.format(**self.cookies))

        data = dict(
            title=key_name,
            content=key_text,
            _csrf=self.cookies["o_csrf"],
        )
        requests.post(url, headers=self.headers, data=data)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='manual to this script')
    parser.add_argument('--username', type=str, default=None)
    parser.add_argument('--password', type=str, default=None)
    parser.add_argument('--key_text', type=str, default=None)
    parser.add_argument('--key_name', type=str, default=None)
    parser.add_argument('--project', type=str, default=None)

    args = parser.parse_args()

    args.username = "yuanpei.guo"
    args.password = "******"
    args.key_text = 'ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQCp/Vwt8xWY9xeHNuBIYmtuoZ/l9hFRVuWEdxYdACoAyl7ghjAVrzEakxNhY2/Ut2dEgaBjZHMvHU1gVJXTGhzO2dfHYVYwFlsirXxY3DuoU44VW3mqRerKxWOOGk/iDmAw+R9iLxjG6UVmhbRz5WwI9xpky+nxtLtvY0J3IXT4qVnav2icXTshIWAaIYaY9B0Z+2U99k48D1IOF3aPULqJPPtQaYOHhG7O0+3Eqr699v6M7iKzoMkBBtxzhjTDluoQlDi3izbm8kEYnSoFyxA5HwUInVZ0ku2UiK9rKBDkK/wQ2irSgy6H84ZBWGxJIBdhdwPaAiNKPJwC6S9O0uKr test1'
    args.key_name = 'test1'
    args.project = "brand_health"

    gitSsh = GitSSH(args.username, args.password)
    gitSsh.add_key(args.key_name, args.key_text, args.project)






