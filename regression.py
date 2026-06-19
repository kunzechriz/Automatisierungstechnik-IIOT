import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error
import os

# Load data
df = pd.read_csv('persistierung/database/data.csv')

# Prepare features
disp_df = df[df['event_type'].str.startswith('dispenser_')].copy()
temp_df = df[df['event_type'] == 'temperature'].copy()
disp_temp = pd.merge(disp_df, temp_df[['time', 'dispenser', 'temperature_C']], on=['time', 'dispenser'], how='left')
disp_temp.rename(columns={'temperature_C_y': 'temperature_C'}, inplace=True)

disp_temp = disp_temp[['bottle', 'dispenser', 'fill_level_grams', 'vibration_index', 'temperature_C']]

# Pivot
pivot_df = disp_temp.pivot_table(index='bottle', columns='dispenser', values=['fill_level_grams', 'vibration_index', 'temperature_C'], aggfunc='first')
pivot_df.columns = [f"{col[0]}_{col[1]}" for col in pivot_df.columns]
pivot_df.reset_index(inplace=True)

# Final weight
weight_df = df[df['event_type'] == 'final_weight'][['bottle', 'final_weight']].dropna()

# Merge all
final_df = pd.merge(pivot_df, weight_df, on='bottle', how='inner').dropna()

# Features defined by user + others
combinations = [
    ['fill_level_grams_red'],
    ['fill_level_grams_red', 'vibration_index_red'],
    ['fill_level_grams_red', 'vibration_index_red', 'temperature_C_red'],
    ['fill_level_grams_red', 'fill_level_grams_blue', 'fill_level_grams_green'],
    ['fill_level_grams_red', 'vibration_index_red', 'temperature_C_red', 
     'fill_level_grams_blue', 'vibration_index_blue', 'temperature_C_blue',
     'fill_level_grams_green', 'vibration_index_green', 'temperature_C_green']
]

y = final_df['final_weight']

best_mse = float('inf')
best_model = None
best_features = None

results = []

for features in combinations:
    X = final_df[features]
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    model = LinearRegression()
    model.fit(X_train, y_train)
    
    y_pred_train = model.predict(X_train)
    y_pred_test = model.predict(X_test)
    
    mse_train = mean_squared_error(y_train, y_pred_train)
    mse_test = mean_squared_error(y_test, y_pred_test)
    
    results.append({
        'Genutzte Spalten (X)': str(features),
        'Modell-Typ': 'Linear',
        'MSE (Training)': round(mse_train, 4),
        'MSE (Test)': round(mse_test, 4)
    })
    
    if mse_test < best_mse:
        best_mse = mse_test
        best_model = model
        best_features = features

# Build Markdown Table
print("Markdown Table:")
print("| Genutzte Spalten (X) | Modell-Typ | MSE (Training) | MSE (Test) |")
print("|---|---|---|---|")
for r in results:
    print(f"| {r['Genutzte Spalten (X)']} | {r['Modell-Typ']} | {r['MSE (Training)']} | {r['MSE (Test)']} |")

# Check if X.csv exists to make prediction, otherwise predict on data.csv
if os.path.exists('X.csv'):
    x_df = pd.read_csv('X.csv')
    try:
        preds = best_model.predict(x_df[best_features]).round(1)
        out_df = pd.DataFrame({'Flaschen ID': x_df['bottle'], 'y_hat': preds})
        out_df.to_csv('reg_Gruppe1.csv', index=False)
        print("Predictions written to reg_Gruppe1.csv from X.csv")
    except Exception as e:
        print("Could not process X.csv:", e)
else:
    # Use final_df (from data.csv)
    X_all = final_df[best_features]
    final_df['y_hat'] = best_model.predict(X_all).round(1)
    out_df = final_df[['bottle', 'y_hat']].rename(columns={'bottle': 'Flaschen ID'})
    out_df['Flaschen ID'] = out_df['Flaschen ID'].astype(int)
    out_df.to_csv('reg_Gruppe1.csv', index=False)
    print("\nPredictions written to reg_Gruppe1.csv from data.csv")

print(f"\nBest features: {best_features}")
coefs = best_model.coef_
intercept = best_model.intercept_
formula = "y = " + " + ".join([f"{coef:.4f} * {feat}" for coef, feat in zip(coefs, best_features)]) + f" + {intercept:.4f}"
print(f"Formula:\n{formula}")

from sklearn.model_selection import ShuffleSplit, cross_val_score

print("\n--- Cross Validation (ShuffleSplit) ---")
X_best = final_df[best_features]
cv = ShuffleSplit(n_splits=10, test_size=0.2, random_state=42)
scores = cross_val_score(LinearRegression(), X_best, y, cv=cv, scoring='neg_mean_squared_error')
mse_scores = -scores

print(f"MSE values across 10 random 80/20 splits: {[round(s, 6) for s in mse_scores]}")
print(f"Average MSE: {mse_scores.mean():.6f}")
print("\nErklärung: Wenn der MSE über viele zufällige Splits konstant bei ~0.0 bleibt, liegt KEIN Overfitting vor. Es bedeutet vielmehr, dass das simulierte Endgewicht der Learning Factory tatsächlich durch eine exakte deterministische (lineare) Funktion dieser 9 Sensorwerte berechnet wird.")
