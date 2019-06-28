. activate web_test27


ansible -i /Users/guoyuanpei/workspace/pworkspace/ansible/hosts --connection=ssh test03 -m setup -a "filter=ansible_default_ipv4"
ansible-playbook -i /Users/guoyuanpei/workspace/pworkspace/ansible/hosts /Users/guoyuanpei/workspace/pworkspace/ansible/playbook/mysql_run.yml



ansible-playbook -i /Users/guoyuanpei/workspace/pworkspace/ansible/hosts /Users/guoyuanpei/workspace/pworkspace/ansible/playbook/test.yml



