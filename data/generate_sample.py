"""
Synthetic Sample Social Media Data Generator (>= 5,000 records).
Generates realistic multi-platform posts (Reddit, YouTube, Telegram)
with coordinated clusters, spam, benign chatter, and high-risk narratives.
Outputs canonical RawPost format with salted SHA-256 author identifiers.
"""

import hashlib
import json
import os
import random
from datetime import datetime, timedelta, timezone

DEFAULT_SALT = os.getenv("AUTHOR_HASH_SALT", "socisenti_super_secret_salt_2026_change_in_production")


def hash_identifier(identifier: str, salt: str = DEFAULT_SALT) -> str:
    """Computes a salted SHA-256 hash of an author identifier or handle."""
    return hashlib.sha256(f"{salt}:{identifier}".encode()).hexdigest()


# Realistic narrative templates
HIGH_RISK_TEMPLATES = [
    "URGENT ALERT: Immediate bank run imminent at {bank}. Withdraw your liquid assets before 4 PM freeze! Pass this to every chat #BankCollapse #{bank}",
    "Coordinated pump operation scheduled at 18:00 UTC on token ${crypto}. Whales loaded. Guarantee 500x return. Join group {link} now! Don't miss out!",
    "LEAKED memo shows classified government project secretly deploying synthetic pathogens in municipal water supply in {city}. Share before censorship removes it!",
    "Mass protest flash mob forming at central plaza in {city} at 21:00. Bring masks, smoke devices and disrupt grid infrastructure. #OpDisrupt",
    "CRITICAL INTEL: Election vote counting servers in {city} compromised by remote backdoor. Military tribunal taking control tonight. #VoterFraud #StormIsComing",
    "Guaranteed return exploit on {bank} deposit system. Send 0.1 BTC to receive 1.5 BTC instantly through automated clearing vulnerability. #CryptoWealth",
]

SPAM_TEMPLATES = [
    "Make $4500 daily working 20 minutes from home! Legit opportunity! Click here: http://bit.ly/spam-{id} #WorkFromHome #PassiveIncome #EasyCash",
    "CHEAPEST ROLEX AND GUCCI REPLICAS AAA+ quality free worldwide shipping visit: www.luxury-fake-{id}.xyz discount code SAVE90!",
    "LOSE 30 LBS IN 10 DAYS WITHOUT DIETING OR EXERCISE doctors HATE this one simple bizarre ice hack: http://tinyurl.com/burn-{id}",
    "Crypto signals 99.8% win rate guaranteed VIP telegram channel access limited 5 spots left join t.me/pump_signals_{id} ! ! !",
    "Watch FREE HD streaming movies online no sign up no credit card required visit http://movie-stream-{id}.live immediately!",
]

BENIGN_TEMPLATES = [
    "Just tried out the new open-source LLM running locally with Ollama. The quantization improvements in 2026 are honestly staggering.",
    "Anyone watching the Champions League semifinal tonight? That extra-time counter attack was absolute football art.",
    "Quick question for the community: what's your preferred approach to database schema migrations in distributed FastAPI microservices?",
    "Morning run through {city} central park was freezing today but the sunrise over the reservoir made it completely worth it.",
    "Finally finished reading 'Designing Data-Intensive Applications'. The chapter on distributed consensus and Raft clarified so much.",
    "Our team just migrated our real-time streaming pipeline from RabbitMQ to Kafka KRaft. Latency dropped by 40% immediately.",
    "Beautiful weekend for hiking in the mountains. Here is a photo from the summit trail. Nature always resets the mind.",
    "Testing out recipes for sourdough bread. Third attempt yielded the perfect crust and airy crumb structure!",
    "The new TypeScript 5.5 features for inferred type predicates simplify complex frontend filtering logic tremendously.",
    "Excited to announce our open source project just reached 1,000 GitHub stars! Thank you to all the contributors.",
]

COORDINATED_TEMPLATES = [
    "ALERT #{batch}: Systemic liquidity crisis hitting {target_institution}. All reserve accounts frozen according to internal whistleblowers! #UrgentWithdrawal",
    "URGENT #{batch}: Insiders confirm {target_institution} insolvency filing scheduled for midnight. Move funds immediately to decentralized custody! #LiquidityRisk",
    "BREAKING #{batch}: Regulatory enforcement action targeting {target_institution}. Run on bank branch locations already reported in major metros! #FinanceAlert",
]

CITIES = ["Zurich", "Frankfurt", "Chicago", "London", "Tokyo", "Singapore", "New York", "Toronto", "Sydney"]
BANKS = ["NordicCapital", "ApexReserve", "VanguardGlobal", "PacificTrust", "MeridianCredit"]
CRYPTOS = ["AURA", "NEXUS", "ZENITH", "PULSE", "VOLT"]


def generate_sample_dataset(count: int = 5000, seed: int = 42) -> list[dict]:
    random.seed(seed)
    posts = []
    base_time = datetime.now(timezone.utc) - timedelta(days=7)

    # 1. Generate Coordinated Cluster Posts (~15% of posts, e.g. 750 posts)
    # A set of 20 sockpuppet accounts posting near-identical messages in tight burst windows
    cluster_accounts = [f"sockpuppet_{i:03d}" for i in range(25)]
    coordinated_count = int(count * 0.15)

    for i in range(coordinated_count):
        account = random.choice(cluster_accounts)
        batch_id = (i // 50) + 1
        burst_offset = (batch_id * 1800) + random.randint(0, 120) # tight 2-minute burst per batch
        created_time = base_time + timedelta(seconds=burst_offset)
        target = random.choice(BANKS)
        template = random.choice(COORDINATED_TEMPLATES)
        text = template.format(batch=batch_id, target_institution=target)

        post_id = f"coord_{i:05d}"
        platform = random.choice(["telegram", "reddit", "youtube"])
        author_id_hash = hash_identifier(account)
        author_handle_hash = hash_identifier(f"@{account}")

        posts.append({
            "platform": platform,
            "post_id": post_id,
            "author_id_hash": author_id_hash,
            "author_handle_hash": author_handle_hash,
            "text": text,
            "lang_hint": "en",
            "created_at": created_time.isoformat(),
            "fetched_at": (created_time + timedelta(seconds=random.randint(5, 30))).isoformat(),
            "url": f"https://{platform}.com/intel/{post_id}",
            "engagement": {
                "likes": random.randint(50, 800),
                "shares": random.randint(30, 450),
                "replies": random.randint(10, 120)
            },
            "parent_id": None,
            "raw_payload": {
                "source_channel": f"channel_{batch_id}",
                "simulated_tag": "coordinated_burst",
                "cluster_batch": batch_id
            }
        })

    # 2. Generate High-Risk Individual Posts (~10% of posts, e.g. 500 posts)
    high_risk_count = int(count * 0.10)
    for i in range(high_risk_count):
        account = f"risk_actor_{random.randint(1, 200):04d}"
        created_time = base_time + timedelta(seconds=random.randint(0, 7 * 86400))
        template = random.choice(HIGH_RISK_TEMPLATES)
        text = template.format(
            bank=random.choice(BANKS),
            crypto=random.choice(CRYPTOS),
            city=random.choice(CITIES),
            link=f"t.me/pump_{random.randint(100, 999)}"
        )
        post_id = f"risk_{i:05d}"
        platform = random.choice(["reddit", "telegram", "youtube"])

        posts.append({
            "platform": platform,
            "post_id": post_id,
            "author_id_hash": hash_identifier(account),
            "author_handle_hash": hash_identifier(f"@{account}"),
            "text": text,
            "lang_hint": "en",
            "created_at": created_time.isoformat(),
            "fetched_at": (created_time + timedelta(seconds=random.randint(10, 60))).isoformat(),
            "url": f"https://{platform}.com/post/{post_id}",
            "engagement": {
                "likes": random.randint(5, 300),
                "shares": random.randint(2, 150),
                "replies": random.randint(1, 90)
            },
            "parent_id": None,
            "raw_payload": {
                "simulated_tag": "high_risk_narrative"
            }
        })

    # 3. Generate Spam Posts (~15% of posts, e.g. 750 posts)
    spam_count = int(count * 0.15)
    for i in range(spam_count):
        account = f"spambot_{random.randint(1, 300):04d}"
        created_time = base_time + timedelta(seconds=random.randint(0, 7 * 86400))
        template = random.choice(SPAM_TEMPLATES)
        text = template.format(id=random.randint(1000, 9999))
        post_id = f"spam_{i:05d}"
        platform = random.choice(["reddit", "youtube"])

        posts.append({
            "platform": platform,
            "post_id": post_id,
            "author_id_hash": hash_identifier(account),
            "author_handle_hash": hash_identifier(f"@{account}"),
            "text": text,
            "lang_hint": "en",
            "created_at": created_time.isoformat(),
            "fetched_at": (created_time + timedelta(seconds=random.randint(2, 20))).isoformat(),
            "url": f"https://{platform}.com/comment/{post_id}",
            "engagement": {
                "likes": random.randint(0, 3),
                "shares": 0,
                "replies": random.randint(0, 2)
            },
            "parent_id": None,
            "raw_payload": {
                "simulated_tag": "spam_bot"
            }
        })

    # 4. Generate Benign Normal Discussions (Remaining ~60%, e.g. 3000 posts)
    remaining_count = count - len(posts)
    for i in range(remaining_count):
        account = f"user_{random.randint(1, 1500):05d}"
        created_time = base_time + timedelta(seconds=random.randint(0, 7 * 86400))
        template = random.choice(BENIGN_TEMPLATES)
        text = template.format(city=random.choice(CITIES))
        post_id = f"benign_{i:05d}"
        platform = random.choice(["reddit", "youtube", "telegram"])
        lang = random.choices(["en", "es", "fr", "de"], weights=[0.85, 0.05, 0.05, 0.05])[0]

        posts.append({
            "platform": platform,
            "post_id": post_id,
            "author_id_hash": hash_identifier(account),
            "author_handle_hash": hash_identifier(f"@{account}"),
            "text": text,
            "lang_hint": lang,
            "created_at": created_time.isoformat(),
            "fetched_at": (created_time + timedelta(seconds=random.randint(15, 120))).isoformat(),
            "url": f"https://{platform}.com/discussion/{post_id}",
            "engagement": {
                "likes": random.randint(0, 150),
                "shares": random.randint(0, 25),
                "replies": random.randint(0, 40)
            },
            "parent_id": None,
            "raw_payload": {
                "simulated_tag": "benign_chatter"
            }
        })

    # Shuffle the dataset so posts appear in realistic mixed streams
    random.shuffle(posts)
    return posts


if __name__ == "__main__":
    target_dir = os.path.join(os.path.dirname(__file__), "sample")
    os.makedirs(target_dir, exist_ok=True)
    target_file = os.path.join(target_dir, "sample_posts.json")

    print("Generating 5,200 synthetic social intelligence posts...")
    dataset = generate_sample_dataset(count=5200, seed=42)
    with open(target_file, "w", encoding="utf-8") as f:
        json.dump(dataset, f, indent=2)

    print(f"Successfully generated {len(dataset)} posts to {target_file}")
    print(f"Sample file size: {os.path.getsize(target_file) / (1024 * 1024):.2f} MB")
