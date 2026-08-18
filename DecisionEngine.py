from . import config


class DecisionEngine:
    
    def decide(self, results):
        priority= config.PROFILES[config.ACTIVE_PROFILE]["priority"]
        
        for link in priority:
            
            if results[link]['alive']:
                return link
        return None
        