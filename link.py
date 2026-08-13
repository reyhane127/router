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
    It does not change routing or network configuration.
    """

    def __init__(self):

        self.running = False

    # Ping

    def run_ping(self, target):

        command = [
            "ping",
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

        except subprocess.TimeoutExpired:

            return None

        except FileNotFoundError:

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

        if ping_result.returncode != 0:
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
            r"(\d+)% packet loss",
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

    def check_http(self, targets):

        for target in targets:

            try:

                result = subprocess.run(
                    [
                        "curl",
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

    def check_ping_targets(self):

        results = []

        for target in config.PING_TARGETS:

            ping_result = self.run_ping(target)

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

    # Full Link Check

    def check_link(self, link):

        ping_results = self.check_ping_targets()

        successful_pings = [
            result
            for result in ping_results
            if result["alive"]
        ]

        if successful_pings:

            average_latency = sum(
                result["latency"]
                for result in successful_pings
                if result["latency"] is not None
            ) / len(successful_pings)

        else:

            average_latency = None

        total_packet_loss = sum(
            result["packet_loss"]
            for result in ping_results
        ) / len(ping_results)

        status = {

            "link": link,

            "alive": len(successful_pings) > 0,

            "latency": average_latency,

            "packet_loss": total_packet_loss,

            "dns": self.check_dns(
                config.DNS_TARGETS
            ),

            "http": self.check_http(
                config.HTTP_TARGETS
            )
        }

        return status

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