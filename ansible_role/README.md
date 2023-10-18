# Ansible-panu

Install a panu instance as a systemd service, according to vars passed to the role.

Assumes that:
- packages are already installed
- database is already installed and running
- shortener is configured somewhere else

In short, it's mostly useful to install new instances of the bot, or pull latest version of the repository on all running instances.

## Example playbook

``` yaml
---
- name: 'Playbook to deploy panu'
  hosts:
    - someserver
  become: true
  gather_facts: false
  vars:
    panu_user: 'panu'
    panu_group: 'panu'
    panu_home: '/opt/panu/'
    panu_external_url: 'http://ploudseeker.com'
    panu_jid: 'panu@chat.jabberfr.org'
    panu_pass: '{{ vault_panu_pass }}'
    panu_db_server: 'localhost'
    panu_db_user: 'panu'
    panu_db_pass: '{{ vault_panu_db_pass }}'
    panu_admin: 'Perdu'
    panu_bot_nick: 'panu'

  roles:
    - role: 'panu'
      vars:
        panu_server: 'chat.jabberfr.org'
        panu_room: 'test'
        panu_db_name: 'panu_test'

    - role: 'panu'
      vars:
        panu_server: 'chat.jabberfr.org'
        panu_room: 'test2'
        panu_db_name: 'panu_test2'
```
