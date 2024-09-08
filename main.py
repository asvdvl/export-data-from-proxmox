import os
from dotenv import load_dotenv, set_key
import ipaddress as ipa
from proxmoxer import ProxmoxAPI

env_path = '.env'
id_mapping_path = 'id_mapping.csv'

load_dotenv(env_path)

host = os.getenv('HOST', 'localhost')
user = os.getenv('USERNAME', 'root@pam')
token_name = os.getenv('TOKEN_NAME', 'exporting')
token_value = os.getenv('TOKEN_VALUE', 'token_value')

if os.path.exists(id_mapping_path):
    print('Not implemented')

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

def add_to_file(text, file, need_comma):
    text = f'{text},' if need_comma else text

    print(text, end='')
    file.write(f'{text}')

f_vms = open('vms.csv', 'w')
def add_to_vms(text, need_comma = True):
    add_to_file(text, f_vms, need_comma)
add_to_vms('name,status,device,vcpus,memory,tags,disk,cluster\n', False)

f_int = open('interfaces.csv', 'w')
def add_to_interfaces(text, need_comma = True):
    add_to_file(text, f_int, need_comma)
add_to_interfaces('virtual_machine,name,enabled,mac_address,mtu\n', False)

f_ip = open('ips.csv', 'w')
def add_to_ips(text, need_comma = True):
    add_to_file(text, f_ip, need_comma)
add_to_ips('address,status,virtual_machine,interface\n', False)

def base_exporter(ct, is_lxc):
    add_to_vms(f"{status_translation(ct['status'])}")                   #status
    add_to_vms(f"{pve_node['node']},{ct['cpus']}")                      #device,vcpus
    add_to_vms(f"{ct['maxmem']/ 1024 / 1024:.0f}")                      #memory
    add_to_vms(f"{'lxc' if is_lxc else 'vm'}")                          #tags
    add_to_vms(f"{ct['maxdisk']/ 1024 / 1024 / 1024:.0f}")              #disk
    add_to_vms("CLUSTERNAME__CHANGEME__\n", False)

def std_addr(int_name, intr):
    add_to_ips('active')                        #status
    add_to_ips(int_name)                        #virtual_machine
    add_to_ips(f"{intr['name']}\n", False)      #interface

def validate_ip(address, req_type):
    try:
        intr = ipa.ip_interface(address)
        if type(intr) == req_type:
            return True
        return False
    except ValueError:
        return False


def param_str_to_dict(str):
    params = str.split(',')
    dict = {}
    for param in params:
        key, value = param.split('=', 1)
        dict[key] = value
    return dict

for pve_node in proxmox.nodes.get():
    print("{0}:".format(pve_node['node']))
    node = proxmox.nodes(pve_node['node'])

    #lxc
    for ct in node.lxc.get():
        name = f"{ct['vmid']} - {ct['name']}"
        add_to_vms(name)                 #id,name
        base_exporter(ct, True)

        config = node.lxc(ct['vmid']).config.get()

        for param in config:
            if param.startswith('net'):
                intr = param_str_to_dict(config[param])
                add_to_interfaces(name)                         #virtual_machine
                add_to_interfaces(f"{intr['name']}")            #name
                #add_to_interfaces(f"{intr['bridge']}")          #bridge(disabled because for netbox it is not a bridge of the node itself but an internal bridge inside the virtual machine)
                add_to_interfaces(f"true")                      #enabled
                add_to_interfaces(f"{intr['hwaddr']}")          #mac_address
                if 'mtu' in intr:
                    add_to_interfaces(f"{intr['mtu']}", False)  #mtu
                add_to_interfaces("\n", False)

                if 'ip' in intr:
                    ip = intr['ip']
                    if validate_ip(ip, ipa.IPv4Interface):
                        add_to_ips(ip)                              #address
                        std_addr(name, intr)
                
                if 'ip6' in intr:
                    ip6 = intr['ip6']
                    if validate_ip(ip6, ipa.IPv6Interface):
                        add_to_ips(ip6)                              #address
                        std_addr(name, intr)
    #vms
    for vm in node.qemu.get():
        name = f"{vm['vmid']} - {vm['name']}"
        add_to_vms(name)                 #id,name
        base_exporter(vm, False)

        config = node.qemu(vm['vmid']).config.get()
        for param in config:
            if param.startswith('net'):
                intr = param_str_to_dict(config[param])
                add_to_interfaces(name)                         #virtual_machine
                add_to_interfaces(f"{param}")                   #name
                #add_to_interfaces(f"{intr['bridge']}")         #bridge(same as for lxc)
                add_to_interfaces(f"true")                      #enabled

                if_mac = ''
                for iftype in ['virtio', 'e1000', 'e1000e', 'rtl8139', 'vmxnet3']:
                    if iftype in intr:
                        if_mac = intr[iftype]
                add_to_interfaces(f"{if_mac}")    #mac_address
                
                if 'mtu' in intr:
                    add_to_interfaces(f"{intr['mtu']}", False)  #mtu
                add_to_interfaces("\n", False)
