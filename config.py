
PROFILES = {
    "home": {
      "priority":[
        "wifi",
        "wan",
        "lte",
        ]
    },
    

    "industrial": {
      "priority":[
        "wan",
        "lte",
        "wifi",
    ]
    }
}
    #active profile

ACTIVE_PROFILE = "home"

# Link Configuration

LINKS = {
    "wan": {
        "interface": "eth0",
        "gateway":"172.27.96.1",
    },

    "wifi": {
        "interface": "wlan0",
        "gateway":None
    },

    "lte": {
        "interface": "wwan0",
        "gateway":None
    },
}

# Health Check

PING_TARGETS = [
    "1.1.1.1",
    "8.8.8.8",
    "9.9.9.9",
]

DNS_TARGETS = [
    "google.com",
    "cloudflare.com",
]

HTTP_TARGETS = [
    "https://www.google.com",
    "https://www.cloudflare.com",
]

# Timing

CHECK_INTERVAL = 2
PING_TIMEOUT = 1

# Failover

FAILURE_THRESHOLD = 3
RECOVERY_THRESHOLD = 5
AUTO_FAILBACK=True
