#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2019, Guillaume Martinez (lunik@tiwabbit.fr)
# Copyright: (c) 2018, Marcus Watkins <marwatk@marcuswatkins.net>
# Based on code:
# Copyright: (c) 2013, Phillip Gentry <phillip@cx.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type
import pdb

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
module: gogs_deploy_key
short_description: Manages gogs project deploy keys.
description:
     - Adds, updates and removes project deploy keys
version_added: "2.6"
author:
  - Marcus Watkins (@marwatk)
  - Guillaume Martinez (@Lunik)
requirements:
  - python >= 2.7
  - python-gogs python module
extends_documentation_fragment:
    - auth_basic
options:
  api_token:
    description:
      - gogs token for logging in.
    version_added: "2.8"
    type: str
    aliases:
      - private_token
      - access_token
  project:
    description:
      - Id or Full path of project in the form of group/name
    required: true
    type: str
  title:
    description:
      - Deploy key's title
    required: true
    type: str
  key:
    description:
      - Deploy key
    required: true
    type: str
  domain:
    description:
      - gogs server domain
    required: true
    type: str
  can_push:
    description:
      - Whether this key can push to the project
    type: bool
    default: no
  state:
    description:
      - When C(present) the deploy key added to the project if it doesn't exist.
      - When C(absent) it will be removed from the project if it exists
    required: true
    default: present
    type: str
    choices: [ "present", "absent" ]
'''

EXAMPLES = '''
- name: "Adding a project deploy key"
  gogs_deploy_key:
    domain: gogs.example.com
    api_token: "{{ access_token }}"
    project: "my_group/my_project"
    title: "Jenkins CI"
    state: present
    key: "ssh-rsa AAAAB3NzaC1yc2EAAAABJQAAAIEAiPWx6WM4lhHNedGfBpPJNPpZ7yKu+dnn1SJejgt4596k6YjzGGphH2TUxwKzxcKDKKezwkpfnxPkSMkuEspGRt/aZZ9w..."

- name: "Update the above deploy key to add push access"
  gogs_deploy_key:
    domain: gogs.example.com
    api_token: "{{ access_token }}"
    project: "my_group/my_project"
    title: "Jenkins CI"
    state: present
    can_push: yes

- name: "Remove the previous deploy key from the project"
  gogs_deploy_key:
    domain: gogs.example.com
    api_token: "{{ access_token }}"
    project: "my_group/my_project"
    state: absent
    key: "ssh-rsa AAAAB3NzaC1yc2EAAAABJQAAAIEAiPWx6WM4lhHNedGfBpPJNPpZ7yKu+dnn1SJejgt4596k6YjzGGphH2TUxwKzxcKDKKezwkpfnxPkSMkuEspGRt/aZZ9w..."

'''

RETURN = '''
msg:
  description: Success or failure message
  returned: always
  type: str
  sample: "Success"

result:
  description: json parsed response from the server
  returned: always
  type: dict

error:
  description: the error message returned by the gogs API
  returned: failed
  type: str
  sample: "400: key is already in use"

deploy_key:
  description: API object
  returned: always
  type: dict
'''

import requests
from lxml import etree

from ansible.module_utils.api import basic_auth_argument_spec
from ansible.module_utils.basic import AnsibleModule


class GogsDeployKey(object):
    def __init__(self, module, params):
        self._module = module
        self._params = params
        self.base_url = "http://{}".format(self._params["domain"])
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
        self.cookies = self._params.get("api_token")
        if not self.cookies:
            url = self.base_url + "/user/login"
            login_get = requests.get(url, headers=self.headers)

            # 获取初始化的 cookies
            login_csrf = etree.HTML(login_get.text).xpath('//input[@name="_csrf" and @type="hidden"]/@value')[0]
            self.cookies = login_get.cookies.get_dict()
            i_like_gogs = login_get.cookies.get("i_like_gogs")
            lang = login_get.cookies.get("lang")

            # 登录使 i_like_gogs 生效
            self.headers.update(Cookie='lang={lang}; i_like_gogs={i_like_gogs}; _csrf={_csrf}'.format(**self.cookies))
            data = {'user_name': self._params["api_username"], 'password': self._params["api_password"], 'login_source': "1", '_csrf': login_csrf}
            requests.post(url, headers=self.headers, data=data)

            # 访问 home 页获取最终 _csrf
            self.headers.update(Cookie='lang={lang}; i_like_gogs={i_like_gogs};'.format(**self.cookies))
            home_page = requests.get(self.base_url, headers=self.headers)

            access_token = home_page.cookies.get("_csrf")
            private_token = etree.HTML(home_page.text).xpath("//meta[@name='_csrf']/@content")[0]
            if not access_token or not private_token:
                self._module.fail_json(msg="username or password error")

            self.cookies = dict(private_token=private_token, access_token=access_token, i_like_gogs=i_like_gogs, lang=lang)
        else:
            self.cookies.update(lang="zh-CN")

    def get_keyid(self):
        '''
        通过 秘钥 名称 获取秘钥 id
        :return:  false 是 error, 0 为 项目错误, None 为没有对应的 title
        '''
        url = self.base_url + "/{0}/settings/keys".format(self._params["project"])
        self.headers.update(Cookie='lang={lang}; i_like_gogs={i_like_gogs}; _csrf={access_token}'.format(**self.cookies))
        result = requests.get(url, headers=self.headers)

        key_id = False
        if result.status_code == 404:
            return 0
        elif result.status_code == 200:
            xpather = etree.HTML(result.text)

            elements = xpather.xpath("//div[@class='item ui grid']")
            key_id = None
            for element in elements:
                name = element.xpath("div[@class='eleven wide column']/strong/text()")[0]
                if name == self._params["title"]:
                    key_id = element.xpath("div[@class='two wide column']/button/@data-id")[0]
                    break

        return key_id

    def delete_key(self, key_id):
        '''
        删除 key
        :param key_id:
        :param project: 所属项目
        :return:
        '''
        url = self.base_url + "/{0}/settings/keys/delete".format(self._params["project"])
        self.headers.update(
            Cookie='lang={lang}; i_like_gogs={i_like_gogs}; _csrf={access_token}'.format(**self.cookies))

        data = dict(
            id=key_id,
            _csrf=self.cookies["private_token"]
        )
        result = requests.post(url, headers=self.headers, data=data)

        return result

    def add_key(self):
        '''
        添加 key
        :return:
        '''
        url = self.base_url + "/{0}/settings/keys".format(self._params["project"])
        self.headers.update(
            Cookie='lang={lang}; i_like_gogs={i_like_gogs}; _csrf={access_token}'.format(**self.cookies))

        data = dict(
            title=self._params["title"],
            content=self._params["key"],
            _csrf=self.cookies["private_token"],
        )
        result = requests.post(url, headers=self.headers, data=data)
        return result


def deprecation_warning(module):
    deprecated_aliases = ['private_token', 'access_token']

    module.deprecate("Aliases \'{aliases}\' are deprecated".format(aliases='\', \''.join(deprecated_aliases)), "2.10")


def main():
    # argument_spec = basic_auth_argument_spec()
    argument_spec = dict(
        api_username=dict(type='str'),
        api_password=dict(type='str', no_log=True),
        api_token=dict(type='str', no_log=True, aliases=["private_token", "access_token", "i_like_gogs"]),
        state=dict(type='str', default="present", choices=["absent", "present"]),
        project=dict(type='str', required=True),
        key=dict(type='str', required=True),
        can_push=dict(type='bool', default=False),
        title=dict(type='str', required=True),
        domain=dict(type='str', required=True)
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        mutually_exclusive=[
            ['api_username', 'api_token'],
            ['api_password', 'api_token']
        ],
        required_together=[
            ['api_username', 'api_password']
        ],
        required_one_of=[
            ['api_username', 'api_token']
        ],
        supports_check_mode=True,
    )

    state = module.params["state"]
    title = module.params["title"]
    project = module.params["project"]

    deprecation_warning(module)
    gogs_instance = GogsDeployKey(module, module.params)

    key_id = gogs_instance.get_keyid()
    if key_id == 0:
        module.fail_json(msg="Failed to get deploy key: project %s doesn't exists" % project)

    if key_id is False:
        module.fail_json(msg="Failed to get deploy key: servcie error" % project)

    if state == 'absent':
        if key_id is not None:
            r = gogs_instance.delete_key(key_id)
            if r.status_code == 200:
                module.exit_json(changed=True, msg="Successfully deleted deploy key %s" % title)
            else:
                module.fail_json(changed=False, msg="failure deleted deploy key %s" % title)
        else:
            module.exit_json(changed=False, msg="Deploy key does not exists")

    if state == 'present':
        if key_id:
            gogs_instance.delete_key(key_id)
            r = gogs_instance.add_key()
            if r.status_code == 200:
                module.exit_json(changed=True, msg="updated the deploy key %s" % title)
            else:
                module.fail_json(changed=False, msg="failure to  created the deploy key %s" % title)

        else:
            r = gogs_instance.add_key()
            if r.status_code == 200:
                module.exit_json(changed=True, msg="Successfully to created the deploy key %s" % title)
            else:
                module.fail_json(changed=False, msg="failure to created the deploy key %s" % title)


if __name__ == '__main__':
    main()
