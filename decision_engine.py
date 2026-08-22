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
            self.recovery_count[link]+=1
        
        else:
            self.failure_count[link] += 1
            self.recovery_count[link]=0
            
            
    def decide(self, results):
        
     priority = config.PROFILES[config.ACTIVE_PROFILE]["priority"]

    # Update state of all links
     for link in priority:

        self.update_link_state(
            link,
            results[link]["alive"]
        )

    # No active link yet
     if self.active_link is None:

        for link in priority:

            if results[link]["alive"]:
                self.active_link = link
                return link

        return None

    # Active link has failed
     if self.failure_count[self.active_link] >= config.FAILURE_THRESHOLD:

        # Find the first healthy backup
        for link in priority:

            if results[link]["alive"]:

                self.active_link = link
                return link

        # No healthy link available
        self.active_link = None
        return None

    # Active link is still healthy
     if not config.AUTO_FAILBACK:
        return self.active_link

    # Check for higher priority link
     active_index = priority.index(self.active_link)

     higher_priority_links = priority[:active_index]

     for link in higher_priority_links:

        if (
            results[link]["alive"]
            and
            self.recovery_count[link] >= config.RECOVERY_THRESHOLD
        ):

            self.active_link = link
            return link

    # Keep current link
     return self.active_link 