from pathlib import Path
import pandas as pd
from sklearn.metrics import accuracy_score,precision_score,recall_score,f1_score,confusion_matrix,classification_report
p=Path("evaluation/ground_truth.csv")
if not p.exists(): raise FileNotFoundError("evaluation/ground_truth.csv not found")
df=pd.read_csv(p); required={"video","frame","actual","predicted"}; missing=required-set(df.columns)
if missing: raise ValueError(f"Missing columns: {missing}")
actual=df["actual"].astype(str).str.lower().str.strip(); pred=df["predicted"].astype(str).str.lower().str.strip()
labels=["helmet","no_helmet"]
print("="*50); print("MODEL EVALUATION"); print("="*50)
print(f"Samples   : {len(df)}"); print(f"Accuracy  : {accuracy_score(actual,pred)*100:.2f}%")
print(f"Precision : {precision_score(actual,pred,average='weighted',zero_division=0)*100:.2f}%")
print(f"Recall    : {recall_score(actual,pred,average='weighted',zero_division=0)*100:.2f}%")
print(f"F1 Score  : {f1_score(actual,pred,average='weighted',zero_division=0)*100:.2f}%")
print("\nConfusion Matrix"); print(confusion_matrix(actual,pred,labels=labels))
print("\nClassification Report"); print(classification_report(actual,pred,labels=labels,zero_division=0))
