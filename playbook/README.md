. activate web_test27

anaconda


ansible -i /Users/guoyuanpei/workspace/pworkspace/ansible/hosts --connection=ssh test03 -m setup -a "filter=ansible_default_ipv4"
ansible-playbook -i /Users/guoyuanpei/workspace/pworkspace/ansible/hosts /Users/guoyuanpei/workspace/pworkspace/ansible/roles/mysql/tests/anaconda.yml
ansible-playbook -i /Users/guoyuanpei/workspace/pworkspace/ansible/hosts /Users/guoyuanpei/workspace/pworkspace/ansible/roles/localRepo/tests/test.yml
ansible-playbook -i /Users/guoyuanpei/workspace/pworkspace/ansible/hosts /Users/guoyuanpei/workspace/pworkspace/ansible/roles/anaconda/tests/mysql.yml
ansible-playbook -i /Users/guoyuanpei/workspace/pworkspace/ansible/hosts /Users/guoyuanpei/workspace/pworkspace/ansible/roles/nginx/tests/test.yml



