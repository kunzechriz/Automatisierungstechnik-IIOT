import pandas as pd
import numpy as np
import json
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split
from sklearn.neighbors import KNeighborsClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import f1_score, confusion_matrix

# Load data
df = pd.read_csv('persistierung/database/data.csv')

df['bottle'] = df['bottle'].ffill()

# Extract drop_oscillation and ground_truth
drops = df[df['event_type'] == 'drop_vibration'][['bottle', 'drop_oscillation']].dropna()

drops_direct = df[df['drop_oscillation'].notnull()][['bottle', 'drop_oscillation']]
cracks = df[df['event_type'] == 'ground_truth'][['bottle', 'is_cracked']].dropna()

merged = pd.merge(drops_direct, cracks, on='bottle', how='inner')

# Parse JSON to numpy arrays
merged['arr'] = merged['drop_oscillation'].apply(lambda x: np.array(json.loads(x), dtype=float))

# Extract statistical features
merged['mean'] = merged['arr'].apply(np.mean)
merged['std'] = merged['arr'].apply(np.std)
merged['max'] = merged['arr'].apply(np.max)
merged['min'] = merged['arr'].apply(np.min)
merged['yt-1'] = merged['arr'].apply(lambda x: x[-2]) # Second to last point

# Raw features (500 columns for time series points)
raw_df = pd.DataFrame(merged['arr'].tolist(), index=merged.index)
raw_features = raw_df.columns.tolist()
merged = pd.concat([merged, raw_df], axis=1)

y = merged['is_cracked']

feature_sets = [
    {'name': 'mean()', 'cols': ['mean']},
    {'name': 'mean(), yt-1', 'cols': ['mean', 'yt-1']},
    {'name': 'mean(), std(), max(), min()', 'cols': ['mean', 'std', 'max', 'min']},
    {'name': 'raw_series (500 pts)', 'cols': raw_features}
]

models = {
    'kNN': KNeighborsClassifier(),
    'Log. Regression': LogisticRegression(max_iter=3000)
}

results = []
best_f1 = -1
best_model = None
best_model_name = ""
best_features_name = ""
best_X_test = None
best_y_test = None

for fset in feature_sets:
    X = merged[fset['cols']]
    
    # Stratified split to handle class imbalance
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    
    # Cast column names to str for scikit-learn compatibility
    X_train.columns = X_train.columns.astype(str)
    X_test.columns = X_test.columns.astype(str)
    
    for m_name, m_inst in models.items():
        m_inst.fit(X_train, y_train)
        
        y_pred_train = m_inst.predict(X_train)
        y_pred_test = m_inst.predict(X_test)
        
        f1_train = f1_score(y_train, y_pred_train, zero_division=0)
        f1_test = f1_score(y_test, y_pred_test, zero_division=0)
        
        results.append({
            'Genutzte Features': fset['name'],
            'Modell-Typ': m_name,
            'F1-Score (Training)': round(f1_train, 4),
            'F1-Score (Test)': round(f1_test, 4)
        })
        
        if f1_test > best_f1:
            best_f1 = f1_test
            best_model = m_inst
            best_model_name = m_name
            best_features_name = fset['name']
            best_X_test = X_test
            best_y_test = y_test

print("Markdown Table:")
print("| Genutzte Features | Modell-Typ | F1-Score (Training) | F1-Score (Test) |")
print("|---|---|---|---|")
for r in results:
    print(f"| {r['Genutzte Features']} | {r['Modell-Typ']} | {r['F1-Score (Training)']} | {r['F1-Score (Test)']} |")

print(f"\nBest Model: {best_model_name} with {best_features_name}")

# Confusion Matrix for best model
y_pred_best = best_model.predict(best_X_test)
cm = confusion_matrix(best_y_test, y_pred_best)

print("\nConfusion Matrix:")
print("| | Predicted: 0 (Intakt) | Predicted: 1 (Defekt) |")
print("|---|---|---|")
print(f"| **Actual: 0 (Intakt)** | {cm[0][0]} | {cm[0][1]} |")
print(f"| **Actual: 1 (Defekt)** | {cm[1][0]} | {cm[1][1]} |")

# Plot
plt.figure(figsize=(6,4))
sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', 
            xticklabels=['Intakt (0)', 'Defekt (1)'], 
            yticklabels=['Intakt (0)', 'Defekt (1)'])
plt.ylabel('Actual')
plt.xlabel('Predicted')
plt.title(f'Confusion Matrix ({best_model_name} / {best_features_name})')
plt.tight_layout()
plt.savefig('confusion_matrix.png', dpi=150)
print("\nSaved confusion_matrix.png")
