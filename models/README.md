# models/

This folder is a placeholder for a future trained ML scam-classification
model (e.g. a scikit-learn pipeline saved with `joblib`, or a fine-tuned
transformer).

The current prototype uses a transparent, rule-based `risk_engine.py` so
that every point in the score is explainable during a hackathon demo.

## How to upgrade later

1. Train a classifier (e.g. `TfidfVectorizer` + `LogisticRegression` from
   scikit-learn) on a labeled dataset of scam vs. legitimate postings.
2. Save it here as `scam_classifier.joblib`.
3. In `modules/risk_engine.py`, add a new function `calculate_risk_ml()`
   that loads this model and blends its probability output with the
   existing rule-based factors (e.g. as an additional weighted factor
   called "ML Model Confidence").
4. Keep the existing rule-based factors as a fallback/explainability layer
   even after adding ML -- students trust a system more when it can show
   its reasoning.
