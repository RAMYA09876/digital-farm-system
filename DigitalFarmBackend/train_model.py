import pandas as pd
import joblib

from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import accuracy_score

from xgboost import XGBClassifier


# ===============================
# LOAD DATA
# ===============================
df = pd.read_csv("amu_residue_records_6000.csv")

print(df.columns)

# Features
X = df[["residue_mg_per_kg", "days_after_treatment", "mrl_limit_mg_per_kg"]]

# Target (Safe=0, Unsafe=1)
y = df["violation_flag"]


# ===============================
# TRAIN TEST SPLIT
# ===============================
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)


# ===============================
# DEFINE MODELS
# ===============================
models = {
    "RandomForest": RandomForestClassifier(),
    "LogisticRegression": LogisticRegression(max_iter=1000),
    "DecisionTree": DecisionTreeClassifier(),
    "XGBoost": XGBClassifier(use_label_encoder=False, eval_metric="logloss")
}

# ===============================
# TRAIN + EVALUATE
# ===============================

best_model = None
best_score = 0

print("\nModel Performance:\n")

for name, mdl in models.items():   # 🔥 change here (model → mdl)
    mdl.fit(X_train, y_train)
    preds = mdl.predict(X_test)
    acc = accuracy_score(y_test, preds)

    print(f"{name} Accuracy: {acc:.4f}")

    if acc > best_score:
        best_score = acc
        best_model = mdl

# ===============================
# SAVE BEST MODEL
# ===============================

import joblib
joblib.dump(best_model, "model.pkl")

print("\nBest model saved as model.pkl")
print(f"Best Accuracy: {best_score:.4f}")

# Save accuracy to file
with open("accuracy.txt", "w") as f:
    f.write(str(best_score))
