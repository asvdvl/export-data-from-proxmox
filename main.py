import os
from dotenv import load_dotenv, set_key
from proxmoxer import ProxmoxAPI

env_path = '.env'
load_dotenv(env_path)

host = os.getenv('HOST', 'localhost')
user = os.getenv('USERNAME', 'root@pam')
token_name = os.getenv('TOKEN_NAME', 'exporting')
token_value = os.getenv('TOKEN_VALUE', 'token_value')

if not os.path.exists(env_path):
    with open(env_path, 'w') as f:
        f.write(f'HOST={host}\n')
        f.write(f'## when you create token you will get string like this: `root@pam!exporting`.\n')
        f.write(f'## here `root@pam` - USERNAME and `exporting` - TOKEN_NAME\n')
        f.write(f'USERNAME={user}\n')
        f.write(f'TOKEN_NAME={token_name}\n')
        f.write(f'TOKEN_VALUE={token_value}\n')
        exit('Please fill .env and start script again')

proxmox = ProxmoxAPI(host, user=user, token_name=token_name, token_value=token_value, verify_ssl=False)

def status_translation(status):
    match status:
        case 'running':
            return 'active'
        case 'stopped':
            return 'offline'
        case _:
            return 'failed'

with open('vms.csv', 'w') as f:
    def add_to_file(text):
        print(text, end='')
        f.write(f'{text}')
    add_to_file('id,name,status,device,vcpus,memory,tags,disk\n')
    for pve_node in proxmox.nodes.get():
        print("{0}:".format(pve_node['node']))

        #lxc
        for container in proxmox.nodes(pve_node['node']).lxc.get():
            add_to_file(f"{container['vmid']},")   #id
            add_to_file(f"{container['name']},")   #name
            add_to_file(f"{status_translation(container['status'])},")   #status
            add_to_file(f"{pve_node['node']},{container['cpus']},")      #device,vcpus
            add_to_file(f"{container['maxmem']/ 1024 / 1024:.0f},lxc,")       #memory,tags
            add_to_file(f"{container['maxdisk']/ 1024 / 1024:.0f}")                                            
            add_to_file(f"\n")
