import os
import uuid
import json
import math
import random
from datetime import datetime, timedelta
from typing import List, Dict, Any
from supabase import create_client
from server.chat import LlmChat
from server.memory import MemoryCategory
from server.environment import supabase_key, supabase_url
from server.memory import Memory
from server.store import VectorDatabase


# ── CONFIG ──
USER_ID = "8a13f1f5-9df0-4d31-a137-cb067ae0f855"
BATCH_SIZE = 50  # keep under PostgREST max body size

db = VectorDatabase(supabase_url, supabase_key)
mem = Memory()

# ── HELPERS ──
def random_unit_vector(dim: int) -> List[float]:
    vec = [random.gauss(0, 1) for _ in range(dim)]
    norm = math.sqrt(sum(x * x for x in vec))
    return [round(x / norm, 6) for x in vec]

def pick(options: list):
    return random.choice(options)

def pick_n(options: list, n: int) -> list:
    return random.sample(options, min(n, len(options)))

# ── TEMPLATES ──
SETTING_TEMPLATES = [
    ("User prefers {theme} mode in all applications", {"theme": ["dark", "light", "high contrast", "auto", "sepia", "solarized"]}),
    ("User has enabled {channel} notifications for {event}", {"channel": ["email", "push", "SMS", "in-app", "desktop", "slack"], "event": ["weekly summaries", "security alerts", "friend requests", "mentions", "price drops", "new releases"]}),
    ("User disabled {feature} in {area}", {"feature": ["auto-play", "sound effects", "animations", "video previews", "read receipts", "location tracking", "personalized ads"], "area": ["all apps", "browser", "mobile app", "desktop client", "video player", "social feed"]}),
    ("User's timezone is set to {tz}", {"tz": ["America/New_York", "Europe/London", "Asia/Tokyo", "America/Los_Angeles", "Australia/Sydney", "UTC", "America/Chicago", "Europe/Berlin"]}),
    ("User selected {lang} as their primary language", {"lang": ["English", "Spanish", "French", "German", "Japanese", "Portuguese", "Italian", "Korean", "Chinese (Simplified)"]}),
    ("User prefers {density} view density in dashboards", {"density": ["compact", "comfortable", "spacious", "minimal", "data-dense"]}),
    ("User turned on {privacy} mode for {scope}", {"privacy": ["incognito", "do not track", "enhanced privacy", "strict", "custom"], "scope": ["search", "browsing", "location", "analytics", "advertising", "profile"]}),
    ("User configured download quality to {quality}", {"quality": ["4K", "1080p", "720p", "480p", "audio only", "original", "high compression"]}),
    ("User requires {a11y} accessibility settings", {"a11y": ["screen reader", "high contrast", "reduced motion", "large text", "closed captions", "keyboard navigation", "colorblind mode"]}),
    ("User set refresh rate to {rate} for {display}", {"rate": ["60Hz", "120Hz", "144Hz", "240Hz", "auto"], "display": ["external monitor", "laptop screen", "all displays"]}),
    ("User prefers {format} date format", {"format": ["MM/DD/YYYY", "DD/MM/YYYY", "YYYY-MM-DD", "ISO 8601", "relative"]}),
    ("User enabled {backup} backup for {data}", {"backup": ["automatic cloud", "daily local", "encrypted offsite", "incremental", "real-time sync"], "data": ["documents", "photos", "code repositories", "database", "entire system"]}),
    ("User set currency display to {currency}", {"currency": ["USD", "EUR", "GBP", "JPY", "CAD", "AUD", "CHF", "local"]}),
    ("User blocked {category} content in {context}", {"category": ["mature", "violent", "political", "spoiler", "gambling", "sensational"], "context": ["feed", "recommendations", "search results", "email digest"]}),
    ("User selected {font} as the default font", {"font": ["Inter", "Roboto", "System Default", "OpenDyslexic", "Serif", "Monospace", "Atkinson Hyperlegible"]}),
]

PREFERENCE_TEMPLATES = [
    ("User prefers {style} responses over {opposite}", {"style": ["concise", "detailed", "structured", "casual", "formal", "step-by-step", "ELI5"], "opposite": ["verbose", "brief", "freeform", "rigid", "academic", "high-level", "technical"]}),
    ("User likes {content} delivered in the {time}", {"content": ["recommendations", "news", "summaries", "reminders", "reports", "digests"], "time": ["morning", "evening", "afternoon", "weekend", "lunchtime", "before bed"]}),
    ("User prefers {format} for lists and data", {"format": ["bullet points", "tables", "numbered steps", "mind maps", "JSON", "markdown", "prose"]}),
    ("User dislikes {dislike} unless {exception}", {"dislike": ["technical jargon", "sarcasm", "pop-ups", "long paragraphs", "passive voice", "acronyms"], "exception": ["absolutely necessary", "requested", "simplified first", "avoided completely"]}),
    ("User prefers {system} units for measurements", {"system": ["metric", "imperial", "SI", "hybrid", "local standard"]}),
    ("User enjoys {genre} content during {activity}", {"genre": ["science fiction", "true crime", "comedy", "educational", "ambient", "lo-fi", "classical", "documentary"], "activity": ["commute", "work", "exercise", "cooking", "relaxing", "travel", "study"]}),
    ("User likes to receive {feedback} style feedback", {"feedback": ["direct and blunt", "sandwich method", "constructive with examples", "positive reinforcement only", "actionable", "data-driven"]}),
    ("User prefers {cuisine} food when dining out", {"cuisine": ["Italian", "Japanese", "Mexican", "Indian", "Thai", "Mediterranean", "Vietnamese", "Korean", "Middle Eastern", "vegetarian"]}),
    ("User favors {brand} over alternatives for {product}", {"brand": ["open-source", "premium", "eco-friendly", "budget", "local", "established", "innovative"], "product": ["software", "hardware", "clothing", "food brands", "services", "transportation"]}),
    ("User prefers {communication} for urgent matters", {"communication": ["phone call", "text message", "email", "instant message", "video call", "in-person"]}),
    ("User likes {temp} room temperature", {"temp": ["cool (65-68°F)", "warm (72-75°F)", "temperate (68-72°F)", "variable by season"]}),
    ("User prefers to study in {environment}", {"environment": ["complete silence", "ambient noise", "coffee shop bustle", "nature sounds", "lo-fi music", "classical music"]}),
    ("User likes to receive {gift_type} as gifts", {"gift_type": ["experiences", "books", "tech gadgets", "handmade items", "charity donations", "cash/gift cards", "consumables"]}),
    ("User prefers {social} social settings", {"social": ["small groups (2-4)", "one-on-one", "large parties", "online communities", "solitary", "structured meetups"]}),
    ("User favors {organization} organization style", {"organization": ["minimalist", "everything labeled", "visual boards", "digital notes", "paper planners", "automated rules"]}),
]

PERSONAL_FACT_TEMPLATES = [
    ("User is a {job} working {mode} from {city}", {"job": ["software engineer", "product manager", "data scientist", "designer", "teacher", "nurse", "marketing manager", "consultant", "writer", "chef"], "mode": ["remotely", "hybrid", "on-site", "from a co-working space"], "city": ["Seattle", "Austin", "New York", "London", "Berlin", "Tokyo", "Toronto", "Denver", "Portland", "Singapore"]}),
    ("User has a {severity} {allergy} allergy", {"severity": ["severe", "mild", "moderate", "life-threatening", "seasonal"], "allergy": ["gluten", "peanut", "shellfish", "dairy", "pollen", "dust", "cat dander", "latex", "soy"]}),
    ("User speaks {lang1} and {lang2} {level}", {"lang1": ["English", "Spanish", "French", "Mandarin", "German", "Japanese", "Portuguese", "Arabic", "Hindi"], "lang2": ["Spanish", "French", "German", "Japanese", "Italian", "Korean", "Russian", "Dutch", "Polish"], "level": ["fluently", "conversationally", "at a beginner level", "professionally", "natively"]}),
    ("User works from a {setup} with {equipment}", {"setup": ["dedicated home office", "spare bedroom", "kitchen table", "co-working desk", "corner of living room", "standing desk setup"], "equipment": ["dual monitors", "ultrawide monitor", "laptop only", "ergonomic chair", "mechanical keyboard", "drawing tablet", "webcam and mic"]}),
    ("User is {handed}-handed and uses {tool}", {"handed": ["left", "right", "ambidextrous"], "tool": ["a left-handed mouse", "a standard mouse", "a trackpad", "a stylus", "a trackball", "a vertical mouse"]}),
    ("User completed a {degree} in {field} at {school}", {"degree": ["Bachelor's", "Master's", "PhD", "Associate's", "bootcamp certificate", "professional certification"], "field": ["Computer Science", "Design", "Business", "Psychology", "Biology", "Engineering", "English Literature", "Data Science"], "school": ["State University", "Tech Institute", "Online University", "Ivy League School", "Community College", "European University"]}),
    ("User has {n} years of experience in {industry}", {"n": ["2", "5", "8", "12", "15", "20", "1", "25"], "industry": ["tech", "healthcare", "finance", "education", "retail", "manufacturing", "media", "government", "non-profit"]}),
    ("User lives in a {housing} in {climate} climate", {"housing": ["house", "apartment", "condo", "townhouse", "houseboat", "tiny home", "duplex"], "climate": ["temperate", "humid subtropical", "arid", "mediterranean", "continental", "tropical", "rainy"]}),
    ("User has {pet_type} named {name} who is {age} years old", {"pet_type": ["a golden retriever", "a tabby cat", "a beagle", "a parrot", "a rabbit", "a hamster", "a German shepherd", "a Siamese cat", "a goldfish"], "name": ["Cooper", "Luna", "Bella", "Max", "Charlie", "Milo", "Daisy", "Rocky", "Simba", "Coco"], "age": ["3", "5", "1", "7", "10", "2", "4", "12", "8"]}),
    ("User wears corrective lenses: {type}", {"type": ["glasses for reading", "contact lenses", "progressive glasses", "sunglasses prescription", "blue light glasses", "no corrective lenses"]}),
    ("User's blood type is {blood}", {"blood": ["O+", "A+", "B+", "AB+", "O-", "A-", "B-", "AB-"]}),
    ("User commutes by {method} taking about {time}", {"method": ["car", "public transit", "bike", "walking", "e-scooter", "motorcycle", "carpool"], "time": ["15 minutes", "30 minutes", "45 minutes", "1 hour", "5 minutes", "90 minutes"]}),
    ("User is {height} tall and {build}", {"height": ["5'6\"", "5'10\"", "6'0\"", "5'4\"", "6'2\"", "5'2\""], "build": ["athletic build", "slim build", "average build", "broad build", "petite build", "tall and lanky"]}),
    ("User has {condition}", {"condition": ["Type 1 diabetes", "asthma", "migraines", "ADHD", "anxiety", "perfect health", "high blood pressure", "insomnia", "none reported"]}),
    ("User plays {instrument} at {skill} level", {"instrument": ["piano", "guitar", "violin", "drums", "flute", "ukulele", "saxophone", "no instrument"], "skill": ["beginner", "intermediate", "advanced", "hobby", "professional", "learning"]}),
    ("User is {marital} with {n} children", {"marital": ["married", "single", "divorced", "in a partnership", "widowed", "engaged"], "n": ["0", "1", "2", "3", "4", "no"]}),
]

GOAL_TEMPLATES = [
    ("User wants to learn {skill} by {deadline}", {"skill": ["conversational Japanese", "Python programming", "data visualization", "public speaking", "digital photography", "financial modeling", "UX research", "machine learning", "woodworking", "Spanish"], "deadline": ["end of year", "Q2 2027", "next summer", "March 2027", "in 6 months", "by December 2026"]}),
    ("User is trying to {activity} {frequency}", {"activity": ["exercise", "meditate", "read", "journal", "cook healthy meals", "practice guitar", "write code", "stretch", "walk"], "frequency": ["three times per week", "daily", "every morning", "five times a week", "twice a weekend", "every evening", "four times a week"]}),
    ("User wants to reduce {target} by {amount}", {"target": ["screen time", "social media usage", "caffeine intake", "sugar consumption", "monthly spending", "carbon footprint", "clutter", "work hours"], "amount": ["one hour per day", "50%", "30 minutes before bed", "$500 per month", "2 hours on weekends", "20% overall"]}),
    ("User is saving for a {goal} to {destination} in {time}", {"goal": ["trip", "vacation", "sabbatical", "relocation", "pilgrimage", "tour"], "destination": ["Japan", "New Zealand", "Italy", "Patagonia", "Iceland", "Southeast Asia", "Norway", "Costa Rica"], "time": ["spring 2027", "summer 2027", "winter 2026", "fall 2027", "early 2028"]}),
    ("User wants to read {n} books this {period}", {"n": ["12", "24", "6", "52", "36", "10"], "period": ["year", "quarter", "summer", "semester", "month"]}),
    ("User aims to get promoted to {role} within {timeframe}", {"role": ["Senior Engineer", "Team Lead", "Product Director", "Principal Designer", "VP of Engineering", "Manager", "Staff Engineer"], "timeframe": ["1 year", "18 months", "2 years", "Q4 2027", "next review cycle"]}),
    ("User wants to build a {project} using {tech}", {"project": ["personal website", "mobile app", "smart home system", "e-commerce store", "blog platform", "AI assistant", "game"], "tech": ["React", "Python", "no-code tools", "Flutter", "Rust", "Unity", "Next.js", "Arduino"]}),
    ("User is training for a {event_type} in {event_date}", {"event_type": ["marathon", "half-marathon", "triathlon", "10K race", "century bike ride", "spartan race", "powerlifting competition"], "event_date": ["April 2027", "October 2026", "fall 2027", "spring 2028", "next year"]}),
    ("User wants to earn {cert} certification", {"cert": ["AWS Solutions Architect", "PMP", "CFA", "Google Cloud Professional", "CISSP", "Kubernetes Administrator", "CPA", "Scrum Master", "TensorFlow Developer"]}),
    ("User plans to buy a {big_item} by {buy_date}", {"big_item": ["house", "car", "new laptop", "electric vehicle", "home gym", "professional camera", "boat", "RV"], "buy_date": ["end of 2027", "mid-2027", "next year", "Q3 2027", "when savings reach $50k"]}),
    ("User wants to improve {metric} to {target_val}", {"metric": ["credit score", "bench press", "5K time", "sleep quality", "blood pressure", "savings rate", "portfolio return", "vocabulary size"], "target_val": ["750", "200 lbs", "under 25 minutes", "8 hours nightly", "120/80", "20%", "8% annually", "5000 words"]}),
    ("User aims to {social_goal} this year", {"social_goal": ["make 5 new friends", "attend 12 networking events", "volunteer 50 hours", "mentor 2 junior developers", "reconnect with 3 old friends", "join a club or community", "host monthly dinners"]}),
    ("User wants to start a {side_project} generating {income}", {"side_project": ["newsletter", "YouTube channel", "consulting gig", "Etsy shop", "podcast", "online course", "freelance design business"], "income": ["$500/month", "passive income", "$2000/month", "enough to cover rent", "a full-time salary"]}),
    ("User plans to declutter and donate {percent} of possessions", {"percent": ["30%", "50%", "20%", "40%", "one-third", "60%"]}),
    ("User wants to learn {cuisine} cooking and master {n} recipes", {"cuisine": ["Italian", "Thai", "French", "Mexican", "Japanese", "Indian", "Mediterranean", "Korean"], "n": ["10", "20", "5", "30", "15", "50"]}),
]

RELATIONSHIP_TEMPLATES = [
    ("User is {relation} to {name} who works in {job}", {"relation": ["married", "engaged", "partnered", "divorced from", "separated from"], "name": ["Alex Chen", "Jordan Smith", "Taylor Wong", "Morgan Lee", "Casey Brown", "Riley Patel", "Quinn Garcia", "Avery Kim"], "job": ["healthcare", "education", "tech", "finance", "law", "marketing", "government", "retail", "non-profit"]}),
    ("User has a {animal} named {name} who is {age} years old", {"animal": ["golden retriever", "tabby cat", "beagle", "cockatoo", "rabbit", "Siamese cat", "bulldog", "hamster", "parakeet", "Maine Coon"], "name": ["Cooper", "Luna", "Bella", "Max", "Oliver", "Lucy", "Charlie", "Daisy", "Milo", "Rocky"], "age": ["3", "5", "1", "7", "10", "2", "4", "12", "8", "6"]}),
    ("User works with a team of {size} {role}", {"size": ["3", "5", "8", "12", "2", "20", "6", "15"], "role": ["product designers", "software engineers", "data analysts", "marketing specialists", "sales representatives", "research scientists", "content creators", "nurses"]}),
    ("User's {relation} lives in {location} and visits {frequency}", {"relation": ["sister", "brother", "parent", "cousin", "aunt", "uncle", "grandparent", "child", "best friend"], "location": ["Austin, Texas", "London, UK", "Vancouver, Canada", "Denver, Colorado", "Portland, Oregon", "Miami, Florida", "Chicago, Illinois", "Dublin, Ireland"], "frequency": ["monthly", "weekly", "twice a year", "every holiday season", "quarterly", "annually", "every summer"]}),
    ("User mentors a {level} named {name}", {"level": ["junior developer", "college student", "new designer", "recent graduate", "intern", "career changer", "startup founder"], "name": ["Jordan Smith", "Sam Rivera", "Chris Johnson", "Jamie Lee", "Pat Morales", "Drew Anderson", "Skyler White"]}),
    ("User reports to a manager named {name} who is {style}", {"name": ["Sarah Johnson", "David Chen", "Emily Rodriguez", "Michael Park", "Lisa Thompson", "James Wilson", "Maria Garcia"], "style": ["hands-off", "very supportive", "data-driven", "results-oriented", "collaborative", "detail-oriented", "visionary"]}),
    ("User is close friends with {name} from {context}", {"name": ["Alex", "Jordan", "Taylor", "Morgan", "Casey", "Riley", "Quinn", "Avery", "Sam", "Drew"], "context": ["college", "high school", "a previous job", "the gym", "a book club", "an online community", "a volunteer group", "a parenting group"]}),
    ("User has a {relation} who is a {profession} in {city}", {"relation": ["spouse", "sibling", "parent", "adult child", "partner", "close friend"], "profession": ["doctor", "teacher", "architect", "chef", "artist", "lawyer", "engineer", "journalist", "therapist"], "city": ["Seattle", "New York", "London", "Berlin", "Tokyo", "Sydney", "Toronto", "San Francisco"]}),
    ("User is part of a {group} with {n} members", {"group": ["running club", "D&D group", "investment circle", "parenting co-op", "book club", "coding meetup", "cooking class", "yoga studio community"], "n": ["4", "6", "8", "12", "15", "20", "3", "10"]}),
    ("User has a {relation} pet named {name} with {trait}", {"relation": ["support", "emotional support", "therapy", "service", "foster", "rescue"], "name": ["Buddy", "Coco", "Luna", "Max", "Rocky", "Daisy", "Bear", "Charlie"], "trait": ["separation anxiety", "high energy", "gentle demeanor", "excellent training", "a funny bark", "a fear of thunder", "a love of swimming"]}),
    ("User's roommate is {name} who prefers {pref}", {"name": ["Alex", "Jordan", "Taylor", "Sam", "Casey", "Morgan", "Riley"], "pref": ["quiet mornings", "late nights", "orderly spaces", "minimal cooking", "lots of plants", "temperature at 72°F", "hosting guests often"]}),
    ("User is {relation} to a local {community} organizer", {"relation": ["married", "siblings with", "cousins with", "dating", "childhood friends with"], "community": ["neighborhood watch", "food bank", "community garden", "mutual aid", "running club", "church group", "arts collective"]}),
    ("User has {n} {relation} under their management", {"n": ["2", "3", "5", "7", "10", "15"], "relation": ["direct reports", "contractors", "interns", "volunteers", "students", "team members"]}),
    ("User is estranged from their {relation} since {year}", {"relation": ["father", "mother", "sibling", "aunt", "uncle", "cousin", "child", "former partner"], "year": ["2019", "2020", "2021", "2022", "2018", "2015", "2023", "2017"]}),
    ("User has a {relation} bond with their {family}", {"relation": ["strong", "complicated", "repaired", "distant but respectful", "weekly phone call", "holiday-only"], "family": ["parents", "extended family", "in-laws", "siblings", "adult children", "step-family"]}),
]

EVENT_TEMPLATES = [
    ("User attended the {event} conference in {date}", {"event": ["AWS re:Invent", "Google I/O", "Apple WWDC", "Microsoft Build", "KubeCon", "NeurIPS", "DEF CON", "GDC", "SXSW", "Web Summit"], "date": ["November 2025", "March 2026", "June 2026", "September 2025", "May 2027", "October 2026", "January 2027", "August 2026"]}),
    ("User moved to a new {housing} in {location} in {date}", {"housing": ["apartment", "house", "condo", "townhouse", "co-living space", "duplex"], "location": ["downtown Seattle", "Brooklyn, New York", "East Austin", "Berlin Mitte", "Shibuya, Tokyo", "Kitsilano, Vancouver", "South Beach, Miami", "LoDo, Denver"], "date": ["March 2026", "June 2026", "January 2027", "September 2026", "December 2025", "April 2027", "July 2026"]}),
    ("User completed their first {achievement} on {date}", {"achievement": ["marathon", "triathlon", "century bike ride", "10K race", "open water swim", "rock climbing summit", "ski marathon", "ultra trail run"], "date": ["October 15, 2025", "April 22, 2026", "June 30, 2026", "November 8, 2025", "March 14, 2027", "September 20, 2026", "July 4, 2026"]}),
    ("User had a {review_type} with their {person} on {date}", {"review_type": ["performance review", "salary negotiation", "360-degree feedback", "quarterly check-in", "career planning session", "project retrospective"], "person": ["manager", "director", "skip-level manager", "HR partner", "peer reviewer", "mentor"], "date": ["last Tuesday", "January 15", "March 1", "Q2 2026", "June 12", "December 2025", "mid-July 2026"]}),
    ("User upgraded their {device} to {model} in {timeframe}", {"device": ["laptop", "phone", "smartwatch", "tablet", "monitor", "headphones", "camera", "gaming console"], "model": ["the latest model", "a 2026 model", "an M4 MacBook Pro", "a flagship Android device", "a professional-grade upgrade", "a lightweight model"], "timeframe": ["last month", "January 2026", "March 2026", "Q4 2025", "early 2027", "summer 2026"]}),
    ("User started a new job at {company} as a {role} in {date}", {"company": ["TechCorp", "Innovate Labs", "Global Solutions", "Nimbus Inc", "Acme Co", "Quantum Ventures", "Atlas Health", "Summit Finance"], "role": ["Senior Engineer", "Product Lead", "Data Scientist", "Staff Designer", "Engineering Manager", "Principal Architect", "DevOps Lead"], "date": ["February 2026", "October 2025", "June 2026", "January 2027", "August 2026", "March 2026"]}),
    ("User got {degree} in {month_year}", {"degree": ["married", "engaged", "a promotion", "a certification", "accepted to grad school", "a new passport", "a driver's license"], "month_year": ["June 2026", "December 2025", "March 2027", "September 2026", "July 2026", "November 2025"]}),
    ("User traveled to {destination} for {duration} in {season}", {"destination": ["Kyoto, Japan", "Paris, France", "Reykjavik, Iceland", "Cape Town, South Africa", "Barcelona, Spain", "Banff, Canada", "Santorini, Greece", "Bali, Indonesia"], "duration": ["two weeks", "a long weekend", "10 days", "one month", "a week", "five days"], "season": ["spring 2026", "summer 2027", "fall 2026", "winter 2026", "spring 2027", "autumn 2025"]}),
    ("User experienced a {health_event} in {timeframe}", {"health_event": ["minor surgery", "major dental procedure", "annual physical", "vision correction procedure", "allergic reaction", "successful physical therapy", "mental health breakthrough"], "timeframe": ["January 2026", "March 2026", "last quarter", "October 2025", "early 2027", "June 2026", "November 2026"]}),
    ("User bought their first {purchase} in {date}", {"purchase": ["home", "new car", "rental property", "investment property", "boat", "RV", "motorcycle", "classic car"], "date": ["March 2026", "July 2026", "December 2025", "April 2027", "September 2026", "January 2027"]}),
    ("User organized a {event} for {n} people", {"event": ["wedding", "charity gala", "team offsite", "birthday party", "housewarming", "retirement party", "baby shower", "networking dinner"], "n": ["50", "150", "12", "200", "30", "500", "25", "100"]}),
    ("User completed a {course} course on {platform} in {month}", {"course": ["machine learning", "advanced UX design", "financial accounting", "creative writing", "project management", "cloud architecture", "public speaking", "nutrition"], "platform": ["Coursera", "Udemy", "edX", "LinkedIn Learning", "Pluralsight", "Skillshare", "Frontend Masters", "DataCamp"], "month": ["January 2026", "March 2026", "June 2026", "October 2025", "December 2025", "April 2027"]}),
    ("User had a {meeting} with {person} about {topic}", {"meeting": ["one-on-one", "stakeholder meeting", "client presentation", "interview", "feedback session", "strategy alignment"], "person": ["the CEO", "a key client", "a venture capitalist", "their mentor", "the board", "an external auditor"], "topic": ["product roadmap", "Q3 funding", "acquisition strategy", "career development", "contract renewal", "market expansion"]}),
    ("User celebrated {holiday} in {location} this year", {"holiday": ["Thanksgiving", "Christmas", "New Year's Eve", "Lunar New Year", "Diwali", "Hanukkah", "Eid", "Independence Day"], "location": ["at their parents' house", "in Hawaii", "at a ski resort", "in their new home", "abroad in Europe", "with friends in the city", "at a beach rental"]}),
    ("User survived a {incident} while {activity}", {"incident": ["minor car accident", "data loss scare", "power outage", "flight cancellation", "identity theft attempt", "home flooding", "equipment failure"], "activity": ["commuting", "presenting to executives", "traveling abroad", "working from home", "moving apartments", "hosting a dinner party"]}),
]


# ── GENERATOR ──
def generate_from_templates(templates, category: str, count: int) -> List[Dict[str, Any]]:
    rows = []
    for i in range(0, len(templates)):
        values = {}
        for key, opts in templates[i][1].items():
            values[key] = random.choice(opts)

        content = templates[i][0].format(**values)

        # Build a richer entities dict from the used values
        entities = {k: v for k, v in values.items()}

        # Add variation to confidence and metadata
        confidence = round(random.uniform(0.75, 0.99), 2)
        metadata = {
            "source": "test_batch_generator",
            "batch_id": 1,
            # "template_idx": templates.index((templates[i], templates[i][1].items())),
            "generation_seed": i,
            "generated_at": datetime.utcnow().isoformat()
        }

        rows.append({
            "user_id": USER_ID,
            "content": content,
            "embedding": mem.embed(content),
            "metadata": metadata,
            "category": category,
            "confidence": confidence,
            "entities": entities,
        })
    return rows


# ── BUILD DATASET ──
random.seed(42)  # reproducible test data

all_records = []
all_records.extend(generate_from_templates(SETTING_TEMPLATES, "SETTING", 100))
all_records.extend(generate_from_templates(PREFERENCE_TEMPLATES, "PREFERENCE", 100))
all_records.extend(generate_from_templates(PERSONAL_FACT_TEMPLATES, "PERSONAL_FACT", 100))
all_records.extend(generate_from_templates(GOAL_TEMPLATES, "GOAL", 100))
all_records.extend(generate_from_templates(RELATIONSHIP_TEMPLATES, "RELATIONSHIP", 100))
all_records.extend(generate_from_templates(EVENT_TEMPLATES, "EVENT", 100))

# Shuffle to avoid category clustering in insertion order
random.shuffle(all_records)

print(f"Generated {len(all_records)} total records")
print(f"  SETTING:        {sum(1 for r in all_records if r['category'] == 'SETTING')}")
print(f"  PREFERENCE:     {sum(1 for r in all_records if r['category'] == 'PREFERENCE')}")
print(f"  PERSONAL_FACT:  {sum(1 for r in all_records if r['category'] == 'PERSONAL_FACT')}")
print(f"  GOAL:           {sum(1 for r in all_records if r['category'] == 'GOAL')}")
print(f"  RELATIONSHIP:   {sum(1 for r in all_records if r['category'] == 'RELATIONSHIP')}")
print(f"  EVENT:          {sum(1 for r in all_records if r['category'] == 'EVENT')}")

# ── BATCH INSERT ──
total_inserted = 0
for i in range(0, len(all_records), BATCH_SIZE):
    batch = all_records[i:i + BATCH_SIZE]
    db.save_batch_memories(batch)
    # print(f"  Batch {i//BATCH_SIZE + 1}: inserted {inserted} rows")

print(f"\nDone. Total inserted: {total_inserted}")