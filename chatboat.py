import json
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
import pickle

# Load updated FAQ JSON
with open("data/chat.json", "r") as f:
    data = json.load(f)

faqs = data["faq"]

# Prepare training data
X = []
y = []

for faq in faqs:
    for keyword in faq["keywords"]:
        X.append(keyword.lower())
        y.append(faq["answer"])
    # Optional: add natural sentence variations
    X.append(f"how to reach {faq['keywords'][0]}")
    y.append(faq["answer"])
    X.append(f"tell me about {faq['keywords'][0]}")
    y.append(faq["answer"])

# Train model
model = Pipeline([
    ('tfidf', TfidfVectorizer()),
    ('clf', LogisticRegression(max_iter=200))
])
model.fit(X, y)

# Test model
for q in ["where is your shop", "contact number", "who owns this shop"]:
    print(f"Q: {q} --> A: {model.predict([q])[0]}")

# Save model
with open("models/faq_model.pkl", "wb") as f:
    pickle.dump(model, f)

print("Model retrained and saved as faq_model.pkl")
