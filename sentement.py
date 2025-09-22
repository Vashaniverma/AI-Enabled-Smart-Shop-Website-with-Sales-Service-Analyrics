import json
import random

# Define message templates with keywords
positive_msgs = [
    {"message": "Great job on the project!", "keywords": ["great", "job", "project"], "sentiment": "positive"},
    {"message": "Everything is running smoothly.", "keywords": ["running", "smoothly"], "sentiment": "positive"},
    {"message": "I am very happy with the results.", "keywords": ["happy", "results"], "sentiment": "positive"},
    {"message": "Excellent work by the team.", "keywords": ["excellent", "work", "team"], "sentiment": "positive"},
    {"message": "I'm impressed with the progress.", "keywords": ["impressed", "progress"], "sentiment": "positive"},
    {"message": "The updates look perfect.", "keywords": ["updates", "perfect"], "sentiment": "positive"},
    {"message": "Good job completing the task on time.", "keywords": ["good", "task", "time"], "sentiment": "positive"},
    {"message": "I love the new design.", "keywords": ["love", "new", "design"], "sentiment": "positive"},
    {"message": "Everything is fine and working well.", "keywords": ["fine", "working", "well"], "sentiment": "positive"},
    {"message": "The client is satisfied.", "keywords": ["client", "satisfied"], "sentiment": "positive"}
]

negative_msgs = [
    {"message": "I am disappointed with the delay.", "keywords": ["disappointed", "delay"], "sentiment": "negative"},
    {"message": "The report is not correct.", "keywords": ["report", "not correct"], "sentiment": "negative"},
    {"message": "We have a serious issue here.", "keywords": ["serious", "issue"], "sentiment": "negative"},
    {"message": "This work is unacceptable.", "keywords": ["work", "unacceptable"], "sentiment": "negative"},
    {"message": "The quality is very poor.", "keywords": ["quality", "poor"], "sentiment": "negative"},
    {"message": "I am unhappy with the results.", "keywords": ["unhappy", "results"], "sentiment": "negative"},
    {"message": "The errors are too many.", "keywords": ["errors", "many"], "sentiment": "negative"},
    {"message": "Not satisfied with the current progress.", "keywords": ["not", "satisfied", "progress"], "sentiment": "negative"},
    {"message": "This project needs urgent attention.", "keywords": ["project", "urgent", "attention"], "sentiment": "negative"},
    {"message": "Deadlines are being missed frequently.", "keywords": ["deadlines", "missed", "frequently"], "sentiment": "negative"}
]

neutral_msgs = [
    {"message": "Please update me on the progress.", "keywords": ["update", "progress"], "sentiment": "neutral"},
    {"message": "The meeting is scheduled for 3 PM.", "keywords": ["meeting", "scheduled"], "sentiment": "neutral"},
    {"message": "We need to discuss the requirements.", "keywords": ["discuss", "requirements"], "sentiment": "neutral"},
    {"message": "Please submit the document.", "keywords": ["submit", "document"], "sentiment": "neutral"},
    {"message": "No major issues reported.", "keywords": ["no", "issues", "reported"], "sentiment": "neutral"},
    {"message": "The deadline is next week.", "keywords": ["deadline", "next week"], "sentiment": "neutral"},
    {"message": "We have a call scheduled today.", "keywords": ["call", "scheduled"], "sentiment": "neutral"},
    {"message": "The system is functioning normally.", "keywords": ["system", "functioning", "normally"], "sentiment": "neutral"},
    {"message": "Please review the attached file.", "keywords": ["review", "attached", "file"], "sentiment": "neutral"},
    {"message": "We will discuss this in tomorrow's meeting.", "keywords": ["discuss", "tomorrow", "meeting"], "sentiment": "neutral"}
]

data = []

# Generate multiple samples randomly for each sentiment to reach 200+
for _ in range(70):  # positive
    data.append(random.choice(positive_msgs))
for _ in range(70):  # negative
    data.append(random.choice(negative_msgs))
for _ in range(60):  # neutral
    data.append(random.choice(neutral_msgs))

# Shuffle data
random.shuffle(data)

# Save as JSON
with open("data/admin_sentiment_keywords_large.json", "w") as f:
    json.dump(data, f, indent=4)

print("Generated 200+ admin messages with keywords and saved as admin_sentiment_keywords_large.json")

import json
import random
import pickle
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline

# --- 1. Generate or load dataset ---
# For simplicity, we will use the large dataset you generated earlier
with open("data/admin_sentiment_keywords_large.json", "r") as f:
    data = json.load(f)

# Combine message + keywords for better prediction
X = [item['message'] + " " + " ".join(item['keywords']) for item in data]
y = [item['sentiment'] for item in data]

# --- 2. Create vectorizer and transform X ---
vectorizer = TfidfVectorizer()
X_vect = vectorizer.fit_transform(X)

# --- 3. Train Naive Bayes classifier ---
nb_model = MultinomialNB()
nb_model.fit(X_vect, y)

# --- 4. Save the model and vectorizer ---
with open("models/naive_bayes_model.pkl", "wb") as f:
    pickle.dump(nb_model, f)

with open("models/vectorizer.pkl", "wb") as f:
    pickle.dump(vectorizer, f)

print("Naive Bayes model saved as naive_bayes_model.pkl")
print("Vectorizer saved as vectorizer.pkl")

# --- 5. Optional: Test prediction ---
test_msgs = [
    "I am very happy with the progress!",
    "The project is falling behind schedule.",
    "Please submit the document on time."
]

for msg in test_msgs:
    vect = vectorizer.transform([msg])
    pred = nb_model.predict(vect)[0]
    print(f"Message: '{msg}' --> Sentiment: {pred}")
