from . import config


class DecisionEngine:

    def __init__(self):

        self.failure_count = {
            link: 0
            for link in config.LINKS
        }

        self.recovery_count = {
            link: 0
            for link in config.LINKS
        }

        self.active_link = None
        

    def is_link_healthy(self, status):

        if not status["alive"]:
            return False

        if status["latency"] is None:
            return False

        if status["latency"] > config.MAX_LATENCY:
            return False

        if status["packet_loss"] is None:
            return False

        if status["packet_loss"] >= config.MAX_PACKET_LOSS:
            return False

        if not status["dns"]:
            return False

        if not status["http"]:
            return False

        return True

    def update_link_state(self, link, healthy):

        if healthy:
            self.failure_count[link] = 0
            self.recovery_count[link] += 1

        else:
            self.failure_count[link] += 1
            self.recovery_count[link] = 0
            
    def select_healthy_link(self, links, healthy_links):
        for link in links:
            if healthy_links[link]:
             self.active_link = link
             return link

        return None

    def decide(self, results):

        priority = config.PROFILES[config.ACTIVE_PROFILE]["priority"]

        healthy_links={}
        
        for link in priority:

            healthy = self.is_link_healthy(results[link])
            healthy_links[link]=healthy
            self.update_link_state(
                link,
                healthy
            )

        if self.active_link is None:
            return self.select_healthy_link(priority,healthy_links)
        
        if self.active_link not in priority:
            self.active_link=None
            
            return self.select_healthy_link(priority,healthy_links)

        if (
            self.failure_count[self.active_link] 
            >= config.FAILURE_THRESHOLD
            ):
            
            selected_link = self.select_healthy_link(
                priority,
                healthy_links
            )
            
            if selected_link is not None:
             return selected_link
        
            self.active_link = None
            return None

            

        if not config.AUTO_FAILBACK:
            return self.active_link

        active_index = priority.index(self.active_link)

        higher_priority_links = priority[:active_index]

        for link in higher_priority_links:

            if (
                healthy_links[link]
                and
                self.recovery_count[link] >= config.RECOVERY_THRESHOLD
            ):

                self.active_link = link
                return link

        return self.active_link