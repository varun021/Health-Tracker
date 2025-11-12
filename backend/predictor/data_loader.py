import pandas as pd
from .models import Disease, Symptom, DiseaseSymptom

def import_disease_data(
     dataset_path='datasets/dataset.csv',                   # Main dataset: Disease → Symptom_1 ... Symptom_N
    description_path='datasets/symptom_Description.csv',   # Disease descriptions
    precaution_path='datasets/symptom_precaution.csv',     # Precautions/tips
    severity_path='datasets/Symptom-severity.csv'          # Symptom severity weights
):
    """
    Import dataset CSVs and populate Disease, Symptom, and DiseaseSymptom models.
    Supports the structure where each row = Disease + multiple Symptom_N columns.
    """

    # === 1. Load all CSVs ===
    df_data = pd.read_csv(dataset_path)
    df_desc = pd.read_csv(description_path)
    df_prec = pd.read_csv(precaution_path)
    df_sev = pd.read_csv(severity_path)

    # Clean column names
    df_data.columns = [c.strip() for c in df_data.columns]
    df_desc.columns = [c.strip() for c in df_desc.columns]
    df_prec.columns = [c.strip() for c in df_prec.columns]
    df_sev.columns = [c.strip().lower() for c in df_sev.columns]

    # === 2. Build severity lookup ===
    severity_map = {}
    for _, row in df_sev.iterrows():
        symptom_name = str(row.get('symptom', '')).strip()
        weight = int(row.get('weight', 5))
        if symptom_name:
            severity_map[symptom_name.lower()] = weight

    print(f"🧩 Loaded {len(df_data)} diseases and {len(severity_map)} symptom severity weights.")

    # === 3. Process each disease ===
    for _, row in df_data.iterrows():
        disease_name = str(row['Disease']).strip()
        if not disease_name or disease_name.lower() == 'nan':
            continue

        # === Get Description ===
        desc_row = df_desc[df_desc['Disease'].str.strip().str.lower() == disease_name.lower()].head(1)
        description = desc_row['Description'].iloc[0] if not desc_row.empty else ''

        # === Get Precautions ===
        pre_row = df_prec[df_prec['Disease'].str.strip().str.lower() == disease_name.lower()].head(1)
        precautions = ''
        if not pre_row.empty:
            pre_values = pre_row.iloc[0].drop('Disease').dropna().values
            precautions = '\n'.join([str(p).strip() for p in pre_values if str(p).strip()])

        # === Create or get Disease ===
        disease_obj, _ = Disease.objects.get_or_create(
            name=disease_name,
            defaults={
                'description': description,
                'lifestyle_tips': precautions,
                'diet_advice': '',
                'medical_advice': ''
            }
        )

        # === 4. Loop through symptom columns dynamically ===
        for col in df_data.columns:
            if col.lower().startswith('symptom') and pd.notna(row[col]):
                symptom_name = str(row[col]).strip()
                if not symptom_name or symptom_name.lower() == 'nan':
                    continue

                # Create or get Symptom
                symptom_obj, _ = Symptom.objects.get_or_create(name=symptom_name)

                # Get weight from severity map or fallback to 5
                weight = severity_map.get(symptom_name.lower(), 5)

                # Create disease-symptom relation if not exists
                DiseaseSymptom.objects.get_or_create(
                    disease=disease_obj,
                    symptom=symptom_obj,
                    defaults={'weight': weight}
                )

    print(f"✅ Successfully imported {Disease.objects.count()} diseases and {Symptom.objects.count()} symptoms with weighted severities.")
