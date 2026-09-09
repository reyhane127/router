import subprocess
import re
import time
import socket
import random
import os
from . import config


class LinkMonitor:
    """
   Monitor the health of network links.

    Responsibilities:
    - Check interface availability
    - Ping targets
    - Measure latency
    - Measure packet loss
    - Check DNS connectivity
    - Check HTTP connectivity
    - Return a standardized health status

    This class does NOT:
    - Make routing decisions
    - Change the default route
    - Modify network configuration
    """

    def __init__(self):

        self.running = False
        
        
    def interface_exists(self,interface):
         
        if not interface:
            return False
        
        return os.path.exists(
            f"/sys/class/net/{interface}"
        )

    # Ping

    def run_ping(self, target, interface):

        command = [
            "ping",
            "-I",
            interface,
            "-c",
            str(config.PING_COUNT),
            "-W",
            str(config.PING_TIMEOUT),
            target
        ]

        try:
#stdout stderr
             return subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=config.PING_COMMAND_TIMEOUT,
                check=False
            )


        except (subprocess.TimeoutExpired, FileNotFoundError,OSError):

            return None

    # Ping Check
    

    def check_ping(self, ping_result):

        if ping_result is None:
            return False

        return ping_result.returncode == 0 #وضعیت پایان فرمان

    # Latency

    def measure_latency(self, ping_result):

        if ping_result is None:
            return None

        output = ping_result.stdout or ""
                #groups: 1:min  2:avg  3:max 4:mdve(انحراف معیار)
        match = re.search(
            r"=\s*([\d.]+)/([\d.]+)/([\d.]+)/([\d.]+)",
            output
        )
        
        if not match:
            return None
        
        try:
            # Average latency
            return float(match.group(2))

        except ValueError:
            return None
        
        
    # Packet Loss

    def measure_packet_loss(self, ping_result):
        #100% packet loss
        if ping_result is None:
            return 100.0

        output = ping_result.stdout or ""
        #4 packets transmitted, 4 received, 0% packet loss, time 3003ms
        #                                   ^^
                                    
        match = re.search(
            r"(\d+(?:\.\d+)?)%\s+packet loss",
            output
        )

        if not match:
            return 100.0
        try:

            return float(match.group(1))
        except ValueError:
            return 100.0
    # DNS Check

    def check_dns(self, targets,interface):
    
     for target in targets:

        for dns_server in config.DNS_SERVERS:

            sock = socket.socket(
                socket.AF_INET,
                socket.SOCK_DGRAM
            )

            try:

                sock.settimeout(config.DNS_TIMEOUT)

                sock.setsockopt(
                    socket.SOL_SOCKET,
                    socket.SO_BINDTODEVICE,
                    interface.encode() + b"\0"
                )

                transaction_id = random.randint(0, 65535)

                header = (
                    transaction_id.to_bytes(2, "big")
                    + b"\x01\x00"
                    + b"\x00\x01"
                    + b"\x00\x00"
                    + b"\x00\x00"
                    + b"\x00\x00"
                )

                question = b""

                for part in target.split("."):
                    question += (
                        bytes([len(part)])
                        + part.encode()
                    )

                question += b"\x00"
                question += b"\x00\x01"
                question += b"\x00\x01"

                query = header + question

                sock.sendto(
                    query,
                    (dns_server, 53)
                )

                response, _ = sock.recvfrom(512)

                if len(response) >= 12:

                    response_id = int.from_bytes(
                        response[0:2],
                        "big"
                    )

                    flags = int.from_bytes(
                        response[2:4],
                        "big"
                    )

                    response_is_valid =(
                        response_id == transaction_id
                        and (flags & 0x8000)
                        and (flags & 0x000F) == 0
                    )
                    
                    if response_is_valid:
                        return True

            except (
                socket.timeout,
                OSError
            ):
                continue

            finally:
                sock.close()

     return False

    # HTTP Check

    def check_http(self, targets, interface):

        for target in targets:
            command = [
                        "curl",
                        "--interface",
                        interface,
                        "-I",
                        "--max-time",
                        str(config.HTTP_TIMEOUT),
                        target
                    ]
            try:

                result = subprocess.run(
                    command,
                    capture_output=True,
                    text=True,
                    timeout=config.HTTP_COMMAND_TIMEOUT,
                    check=False
                )

            except (subprocess.TimeoutExpired
            ,FileExistsError,
            OSError
            ):
                continue

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
                    "alive": self.check_ping(ping_result) ,
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

        if not self.interface_exists(interface):
            return {
                "link": link,
                "interface": None,
                "alive": False,
                "latency": None,
                "packet_loss": 100.0,
                "dns": False,
                "http": False,
                "error": "Interface does not exist"
            }
            
        ping_results = self.check_ping_targets(
            interface
        )
        
        ping_health = self.calculate_ping_health(
            ping_results
        )
        
        dns_status = self.check_dns(
            config.DNS_TARGETS,
            interface
        )

        http_status = self.check_http(
            config.HTTP_TARGETS,
            interface
        )
        
        alive=(
            ping_health["alive"]
            and dns_status 
            and http_status
            )

        return {
            "link": link,
            "interface": interface,
            "alive": alive,
            "latency": ping_health["latency"],
            "packet_loss": ping_health["packet_loss"],
            "dns": dns_status,
            "http": http_status
        }
 
    # Monitor Loop

    def monitor_loop(self, link, callback=None):

        self.running = True

        while self.running:

            result = self.check_link(link)

            if callback is not None:
                callback(result)

            time.sleep(
                config.CHECK_INTERVAL
            )

    # Start

    def start(self, link, callback=None):

        self.monitor_loop(link , callback)

    # Stop

    def stop(self):

        self.running = False