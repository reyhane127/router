from .link_monitor import LinkMonitor
from .decision_engine import DecisionEngine
from .route_manager import RouteManager
from . import config
import time

class NetworkManager:
    
    def __init__(self):
        
     self.monitor=LinkMonitor()
     self.decision_engine = DecisionEngine()
     self.route_manager = RouteManager()
     self.current_link = self.get_current_link()
     self.runnig = False
    
    def check_all_links(self):
        
        results = {}
        
        for link in config.LINKS:
            
            results[link] = self.monitor.check_link(link)
 
        return results
    
    def  decide_link(self):
        
        results=self.check_all_links()
        
        selected_link=self.decision_engine.decide(results)
        
        return selected_link
    
    def apply_decision(self,selected_link):
        if selected_link is None:
            return False
        
        if selected_link == self.current_link:
            return False
        
        result = self.route_manager.apply_link(selected_link) 
          
        if result is not None and result.returncode == 0:
            
            self.current_link = selected_link 
                
            return True
        
        return False
        
    #interface --> link  
    def get_current_link(self):
    
      route_info = self.route_manager.get_default_route_info()

      if route_info is None:
        return None

      current_interface = route_info['interface']

      for link, link_config in config.LINKS.items():

        if link_config['interface'] == current_interface:
            return link

      return None
    
    def run_once(self): 
        selected_link = self.decide_link() 
        
        self.apply_decision(selected_link)
        
        
    def monitor_loop(self):
        
        self.runnig = True
        
        while self.runnig:
            
            self.run_once()
            
            time.sleep(config.CHECK_INTERVAL)
            
            
    def start(self):
        
        self.monitor_loop()
        
    def stop(self):
        
        self.runnig = False
    