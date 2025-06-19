import random
import string

# List of adjectives
adjectives = [
    "happy", "brave", "bright", "swift", "gentle", "clever", "bold", "calm",
    "eager", "fierce", "jolly", "kind", "lively", "mighty", "noble", "proud",
    "quick", "sharp", "strong", "wise", "agile", "alert", "brave", "crisp",
    "daring", "elegant", "fearless", "graceful", "heroic", "inspired"
]

# List of nouns
nouns = [
    "tiger", "eagle", "dolphin", "falcon", "lion", "wolf", "bear", "fox",
    "hawk", "owl", "phoenix", "dragon", "panther", "cheetah", "jaguar",
    "lynx", "raven", "shark", "whale", "python", "cobra", "viper", "mamba",
    "storm", "thunder", "lightning", "tornado", "blizzard", "avalanche"
]

def generate_unique_phrase() -> str:
    """Generate a unique phrase like 'happy-tiger-1234'"""
    adjective = random.choice(adjectives)
    noun = random.choice(nouns)
    number = ''.join(random.choices(string.digits, k=4))
    return f"{adjective}-{noun}-{number}"
