from . import config


class DecisionEngine:
    
    def __init__(self):
        
        self.failure_count={
            link:0
            for link in config.LINKS
        }
        
        self.recovery_count={
            link:0
            for link in config.LINKS
        }
        
        self.active_link=None
        
        
   
    def update_link_state(self,link,alive):
        
        if alive:
            self.failure_count[link] = 0
        
        else:
            self.failure_count[link] += 1
            
            
    def decide(self, results):
            priority= config.PROFILES[config.ACTIVE_PROFILE]["priority"]
            #update state of all links
            for link in priority:
                
              self.update_link_state(
                  link,
                  results[link]["alive"]
              )
              
            
            if self.active_link is not None:
                
                if self.failure_count[self.active_link] <config.FAILURE_THRESHOLD:
                    return self.active_link
            
            for link in priority:
                
              if (results[link]["alive"]
                  and self.failure_count[link] < config.FAILURE_THRESHOLD):
                  
                  self.active_link = link
                  return link
            
            self.active_link=None 
            return None
            