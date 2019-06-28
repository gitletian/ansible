mysql 的 安装
1、需要配置 自己的 mysql yum 源
2、暂时仅测试实现了
  centos6:
    - mysql5.5
    - mysql5.6
    - mysql5.7
    - mysql8.0
的安装, centos7 待续。

使用示例:
# ansible-playbook -i /Users/guoyuanpei/workspace/pworkspace/ansible/hosts /Users/guoyuanpei/workspace/pworkspace/ansible/playbook/mysql_run.yml
---
- hosts: test03
  connection: ssh
  become: yes
  become_user: root

  roles:
    - role: localRepo
    - role: mysql
      vars:
        mysql_version: 8.0.15    # 需要指明安装的 mysql 版本
        mysql_character_set_server: utf8
        mysql_collation_server: utf8_bin
        mysql_mysql_default_character_set: utf8
        mysql_client_default_character_set: utf8

        mysql_databases:
          - name: kcc
            encoding: utf8
            collation: utf8_bin

        mysql_users:
          - name: kcc
            host: "%"
            password: "Mp@3965122"
            priv: "kcc.*:ALL"

...