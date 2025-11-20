import streamlit as st
import requests
from bs4 import BeautifulSoup
import spacy
import re
from transformers import pipeline

# -----------------------------
# 📰 Scrape News Articles
# -----------------------------
def scrape_news_articles(url):
    """Fetch article content from a news URL."""
    st.info("📰 Fetching article content...")
    response = requests.get(url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        paragraphs = soup.find_all('p')
        article_text = ' '.join(p.text for p in paragraphs)
        st.success("✅ Article fetched successfully.")
        return article_text
    else:
        st.error(f"❌ Failed to fetch article. Status code: {response.status_code}")
        return ""

# -----------------------------
# 📋 Event Extraction
# -----------------------------
def extract_events(text):
    """Extract events with details like who, what, where, when, and why."""
    st.info("📋 Extracting events from text...")
    nlp = spacy.load("en_core_web_sm")
    doc = nlp(text)
    events = []

    for sent in doc.sents:
        event = {'who': [], 'what': '', 'where': [], 'when': '', 'why': '', 'sentence': sent.text}
        for ent in sent.ents:
            if ent.label_ in ['PERSON', 'ORG']:
                event['who'].append(ent.text)
            if ent.label_ in ['GPE', 'LOC']:
                event['where'].append(ent.text)
            if ent.label_ in ['DATE', 'TIME']:
                event['when'] = ent.text

        for token in sent:
            if token.dep_ == "ROOT" and token.pos_ == "VERB":
                event['what'] = token.text
                break

        if event['what']:
            events.append(event)

    st.success(f"✅ Extracted {len(events)} events.")
    return events

# -----------------------------
# 🔗 Temporal Event Linking
# -----------------------------
def extract_temporal_relationships(text):
    """Identify temporal relationships like 'before', 'after', and 'during'."""
    st.info("⏳ Extracting temporal relationships...")
    temporal_clues = ['before', 'after', 'during', 'when']
    temporal_relationships = []

    for clue in temporal_clues:
        matches = re.finditer(rf'(.+?)\b{clue}\b(.+?)\.', text, re.IGNORECASE)
        for match in matches:
            temporal_relationships.append({
                'context': match.group(1).strip(),
                'relation': clue,
                'related_event': match.group(2).strip()
            })

    st.success(f"✅ Extracted {len(temporal_relationships)} temporal relationships.")
    return temporal_relationships

# -----------------------------
# 🧠 Outcome Prediction
# -----------------------------
def predict_outcomes(event_sentences):
    """Predict the outcome of each event."""
    st.info("🧠 Predicting outcomes...")
    classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")
    possible_outcomes = ["political change", "economic shift", "social unrest", "policy change", "no impact"]
    predictions = []

    for event in event_sentences:
        result = classifier(event, possible_outcomes)
        predicted_outcome = result['labels'][0]
        predictions.append({
            'event': event,
            'predicted_outcome': predicted_outcome
        })
        st.write(f"**Event:** {event}")
        st.write(f"**Predicted Outcome:** {predicted_outcome}")
    return predictions

# -----------------------------
# 🎯 Streamlit UI
# -----------------------------
def main():
    st.title("📰 News Event Analysis Dashboard")
    st.write("Extract events, analyze relationships, and predict outcomes from news articles.")

    url = st.text_input("🔗 Enter a News Article URL:")
    if st.button("🚀 Run Pipeline"):
        if url.startswith("http"):
            article_text = scrape_news_articles(url)
            if article_text:
                st.subheader("📋 Extracted Events")
                events = extract_events(article_text)
                for i, event in enumerate(events):
                    st.write(f"**Event {i+1}:**")
                    st.write(f"**Who:** {', '.join(event['who']) if event['who'] else 'N/A'}")
                    st.write(f"**What:** {event['what']}")
                    st.write(f"**Where:** {', '.join(event['where']) if event['where'] else 'N/A'}")
                    st.write(f"**When:** {event['when'] if event['when'] else 'N/A'}")
                    st.write(f"**Sentence:** {event['sentence']}")

                st.subheader("🔗 Temporal Relationships")
                temporal_relationships = extract_temporal_relationships(article_text)
                for i, relation in enumerate(temporal_relationships):
                    st.write(f"**Relation {i+1}:** {relation['context']} → {relation['relation']} → {relation['related_event']}")

                st.subheader("🧠 Predicted Outcomes")
                event_sentences = [event['sentence'] for event in events]
                predictions = predict_outcomes(event_sentences)
        else:
            st.warning("⚠ Please enter a valid URL.")

if __name__ == "__main__":
    main()
