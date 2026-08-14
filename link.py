import subprocess
import re
import time

from . import config


class LinkMonitor:
    """
    Network Link Health Monitor

    Responsibilities:
    - Ping check
    - Latency measurement
    - Packet loss measurement
    - DNS check
    - HTTP check

    This module only monitors.
    It does not make routing decisions.
    It does not change routing or network configuration.
    """

    def __init__(self):

        self.running = False

    # Ping

    def run_ping(self, target, interface):

        command = [
            "ping",
            "-I",
            interface,
            "-c",
            "4",
            "-W",
            str(config.PING_TIMEOUT),
            target
        ]

        try:

            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=5
            )

            return result

        except (subprocess.TimeoutExpired, FileNotFoundError):

            return None

    # Ping Check
    

    def check_ping(self, ping_result):

        if ping_result is None:
            return False

        return ping_result.returncode == 0

    # Latency

    def measure_latency(self, ping_result):

        if ping_result is None:
            return None

        output = ping_result.stdout

        match = re.search(
            r"=\s*([\d.]+)/([\d.]+)/([\d.]+)/([\d.]+)",
            output
        )

        if match:

            # Average latency
            return float(match.group(2))

        return None

    # Packet Loss

    def measure_packet_loss(self, ping_result):

        if ping_result is None:
            return 100.0

        output = ping_result.stdout

        match = re.search(
            r"(\d+(?:\.\d+)?)%\s+packet loss",
            output
        )

        if match:

            return float(match.group(1))

        return 100.0

    # DNS Check

    def check_dns(self, targets):

        for target in targets:

            try:

                result = subprocess.run(
                    [
                        "nslookup",
                        target
                    ],
                    capture_output=True,
                    text=True,
                    timeout=5
                )

            except subprocess.TimeoutExpired:

                continue

            except FileNotFoundError:

                return False

            if result.returncode == 0:

                return True

        return False

    # HTTP Check

    def check_http(self, targets, interface):

        for target in targets:

            try:

                result = subprocess.run(
                    [
                        "curl",
                        "--interface",
                        interface,
                        "-I",
                        "--max-time",
                        "3",
                        target
                    ],
                    capture_output=True,
                    text=True,
                    timeout=5
                )

            except subprocess.TimeoutExpired:

                continue

            except FileNotFoundError:

                return False

            if result.returncode == 0:

                return True

        return False

    # Ping All Targets

    def check_ping_targets(self, interface):

        results = []

        for target in config.PING_TARGETS:

            ping_result = self.run_ping(target,interface)
            

            results.append(
                {
                    "target": target,
                    "alive": self.check_ping(ping_result),
                    "latency": self.measure_latency(ping_result),
                    "packet_loss": self.measure_packet_loss(
                        ping_result
                    )
                }
            )

        return results
    
    #Calculate Ping Health
    
    def calculate_ping_health(self, ping_results):

        if not ping_results:
            
            return {
                "alive": False,
                "latency": None,
                "packet_loss": 100.0
            }

        successful_pings = [
            result
            for result in ping_results
            if result["alive"]
        ]

        latencies = [
            result["latency"]
            for result in successful_pings
            if result["latency"] is not None
        ]

        if latencies:
          average_latency = (
            sum(latencies) / len(latencies)
            )
        else:
            average_latency = None

        packet_losses = [
            result["packet_loss"]
            for result in ping_results
            if result["packet_loss"] is not None
        ]
        
        if packet_losses:
            average_packet_loss = (
                sum(packet_losses) / len(packet_losses)
            )
        else:
            average_packet_loss = 100.0

        return {
            "alive": len(successful_pings) > 0,
            "latency": average_latency,
            "packet_loss": average_packet_loss
        }


    # Full Link Check

    def check_link(self, link):
        if link not in config.LINKS:
    
            return {
                "link": link,
                "interface": None,
                "alive": False,
                "latency": None,
                "packet_loss": 100.0,
                "dns": False,
                "http": False,
                "error": "Unknown link"
            }

        interface = config.LINKS[link]["interface"]

        ping_results = self.check_ping_targets(
            interface
        )
        
        ping_health = self.calculate_ping_health(
            ping_results
        )
        
        dns_status = self.check_dns(
            config.DNS_TARGETS
        )

        http_status = self.check_http(
            config.HTTP_TARGETS,
            interface
        )

        return {
            "link": link,
            "interface": interface,
            "alive": ping_health["alive"],
            "latency": ping_health["latency"],
            "packet_loss": ping_health["packet_loss"],
            "dns": dns_status,
            "http": http_status
        }
 
    # Monitor Loop

    def monitor_loop(self, link):

        self.running = True

        while self.running:

            result = self.check_link(link)

            print(
                "Link Status:",
                result
            )

            time.sleep(
                config.CHECK_INTERVAL
            )

    # Start

    def start(self, link):

        self.monitor_loop(link)

    # Stop

    def stop(self):

        self.running = False