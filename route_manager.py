import subprocess
import re
from . import config


class RouteManager:
    
    def get_default_route(self):
        
        result=subprocess.run(
            ['ip', 'route', 'show', 'default'],
            capture_output=True,
            text=True
                              )
        return result.stdout.strip()
        #output is: "default via 172.27.96.1 dev eth0 proto kernel"
    
    
    
    def get_default_route_info(self):
        route=self.get_default_route()
        
        match=re.search(
            r"default via (\S+) dev (\S+)",
            route
        )
        if match:
            return{
                "gateway": match.group(1),  # 172.27.96.1
                "interface":match.group(2)  # eth0
            }
        return None
    
    
    def set_default_route(self,interface,gateway):
        
        result=subprocess.run(
            [
                'ip',
                'route',
                'replace',
                'default',
                'via',
                gateway,
                'dev',
                interface
            ],
            capture_output=True,
            text=True
            )
        return result
    
    
    def apply_link(self,link):
        
        link_config=config.LINKS[link]
        
        interface=link_config["interface"]
        gateway=link_config["gateway"]
        
        if gateway is None:
            return None
        
        return self.set_default_route(
            interface,
            gateway
        )