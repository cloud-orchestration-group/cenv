from .base import BaseStorageProvider


class Manual(BaseStorageProvider):

    def provider_config(self):
        self.requirement('name', help = 'Unique name of storage mount in environment')
        self.requirement('fs_name', help = 'Name of the filesystem for storage mount in environment')
        self.requirement('region', help = 'Storage region name', config_name = 'manual_region')
        self.requirement('zone', help = 'Storage zone name', config_name = 'manual_zone')
        self.requirement('remote_host', help = 'Remote host to connect storage mount')
        
        self.option('remote_path', '/', help = 'Remote path to mount locally', config_name = 'manual_remote_path')
        self.option('mount_options', 'nfs4 rsize=1048576,wsize=1048576,hard,timeo=600,retrans=2 0 0', help = 'Mount options', config_name = 'manual_mount_options')
