import DecisionEngine

results = {
    "wifi": {"alive": False},
    "wan": {"alive": True},
    "lte": {"alive": True}
}

engine = DecisionEngine()

selected = engine.decide(results)

print("Selected link:", selected)