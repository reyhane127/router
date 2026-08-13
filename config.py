# Router Mode

MODE = "home"
# "home" or "industrial"


# Link Priority

LINK_PRIORITY = {

    "home": [
        "wifi",
        "wan",
        "lte",
    ],

    "industrial": [
        "wan",
        "lte",
        "wifi",
    ]
}

ACTIVE_LINK_PRIORITY = LINK_PRIORITY[MODE]

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
