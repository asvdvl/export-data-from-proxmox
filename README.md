Here's a revised version of your README:

## Simple Proxmox Config Exporter to CSV

Default format for import into the NetBox VM tab. Currently, it exports data for both VMs and LXCs:
- Interface names
- Interface MAC addresses
- Interface bridges
- IPv4/IPv6 addresses if static
- Name, status, device (PVE name), vCPUs, memory, disk size

### 1. Installation

#### 1.1. Create Environment
I personally use Miniconda. Example:
```bash
conda create -y --name proxmoxer python=3.10
conda activate proxmoxer
```

#### 1.2. Install Package
```bash
pip install -r requirements.txt
```

#### 1.3. Create Token
In the datacenter, create a new API Token and disable `Privilege Separation`.

### 2. Running

```bash
python main.py
```
Fill out the `.env` file and rerun the command above.

If you want to use SSH as a connection method, it is not yet implemented. However, you can modify the script using the following links:
- [Proxmoxer Dependencies](https://proxmoxer.github.io/docs/latest/setup/)
- [OpenSSH Backend](https://proxmoxer.github.io/docs/latest/authentication/#openssh-backend)