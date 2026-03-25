"""Complete test catalog for Avishka Pathology."""

TEST_CATALOG = {
    "CBC": {
        "name": "Complete Blood Count",
        "price": 300,
        "category": "Blood",
        "preparation": "No fasting required",
        "description": "Detects infections, anemia, blood disorders. Measures RBC, WBC, platelets.",
        "duration": "Same Day",
        "icon": "🩸",
    },
    "BSF": {
        "name": "Blood Sugar Fasting",
        "price": 120,
        "category": "Diabetes",
        "preparation": "8–12 hours fasting required",
        "description": "Measures blood glucose levels after fasting. Essential for diabetes diagnosis.",
        "duration": "Same Day",
        "icon": "💉",
    },
    "BSPP": {
        "name": "Blood Sugar Post Prandial",
        "price": 120,
        "category": "Diabetes",
        "preparation": "2 hours after meal",
        "description": "Measures blood glucose 2 hours after eating. Monitors diabetes control.",
        "duration": "Same Day",
        "icon": "💉",
    },
    "BSRANDOM": {
        "name": "Blood Sugar Random",
        "price": 120,
        "category": "Diabetes",
        "preparation": "No fasting required",
        "description": "Checks blood glucose at any time. Quick diabetes screening.",
        "duration": "Same Day",
        "icon": "💉",
    },
    "LIPID": {
        "name": "Lipid Profile",
        "price": 350,
        "category": "Heart Health",
        "preparation": "12 hours fasting required",
        "description": "Checks total cholesterol, LDL, HDL, triglycerides. Essential for heart risk assessment.",
        "duration": "Same Day",
        "icon": "❤️",
    },
    "THYROID": {
        "name": "Thyroid Profile (T3, T4, TSH)",
        "price": 600,
        "category": "Thyroid",
        "preparation": "No fasting required",
        "description": "Evaluates thyroid gland function. Detects hypothyroidism & hyperthyroidism.",
        "duration": "Same Day",
        "icon": "🦋",
    },
    "LFT": {
        "name": "Liver Function Test",
        "price": 400,
        "category": "Organ Function",
        "preparation": "12 hours fasting required",
        "description": "Assesses liver health — enzymes, bilirubin, proteins. Detects liver disease.",
        "duration": "Same Day",
        "icon": "🏥",
    },
    "KFT": {
        "name": "Kidney Function Test",
        "price": 350,
        "category": "Organ Function",
        "preparation": "No fasting required",
        "description": "Evaluates kidney health — creatinine, urea, uric acid. Detects kidney disease.",
        "duration": "Same Day",
        "icon": "🏥",
    },
    "URINE": {
        "name": "Urine Routine & Microscopy",
        "price": 100,
        "category": "Urine",
        "preparation": "Early morning mid-stream sample preferred",
        "description": "Detects urinary infections, kidney disease, diabetes markers.",
        "duration": "Same Day",
        "icon": "🔬",
    },
    "VITD": {
        "name": "Vitamin D (25-OH)",
        "price": 800,
        "category": "Vitamins",
        "preparation": "No fasting required",
        "description": "Checks Vitamin D levels — essential for bone health, immunity, mood.",
        "duration": "1–2 Days",
        "icon": "☀️",
    },
    "VITB12": {
        "name": "Vitamin B12",
        "price": 600,
        "category": "Vitamins",
        "preparation": "No fasting required",
        "description": "Checks B12 levels — critical for nerve function and red blood cell production.",
        "duration": "1–2 Days",
        "icon": "🧬",
    },
    "HBA1C": {
        "name": "HbA1c (Glycated Hemoglobin)",
        "price": 350,
        "category": "Diabetes",
        "preparation": "No fasting required",
        "description": "3-month average blood sugar level. Gold standard for diabetes monitoring.",
        "duration": "Same Day",
        "icon": "📊",
    },
    "ECG": {
        "name": "ECG / Electrocardiogram",
        "price": 200,
        "category": "Heart Health",
        "preparation": "Wear comfortable, loose clothing",
        "description": "Records the heart's electrical activity. Detects arrhythmias, heart disease.",
        "duration": "Immediate",
        "icon": "💓",
    },
}

# Symptom → recommended tests mapping
SYMPTOM_TEST_MAP = {
    "fatigue":         ["CBC", "THYROID", "VITB12", "VITD"],
    "tired":           ["CBC", "THYROID", "VITB12"],
    "weakness":        ["CBC", "VITB12", "VITD"],
    "fever":           ["CBC", "URINE"],
    "infection":       ["CBC", "URINE"],
    "diabetes":        ["BSF", "BSPP", "HBA1C"],
    "sugar":           ["BSF", "HBA1C"],
    "high sugar":      ["BSF", "BSPP", "HBA1C"],
    "chest pain":      ["ECG", "LIPID"],
    "heart":           ["ECG", "LIPID"],
    "cholesterol":     ["LIPID"],
    "thyroid":         ["THYROID"],
    "weight gain":     ["THYROID", "BSF", "LIPID"],
    "weight loss":     ["THYROID", "CBC"],
    "kidney":          ["KFT", "URINE"],
    "urine problem":   ["URINE", "KFT"],
    "liver":           ["LFT"],
    "jaundice":        ["LFT"],
    "yellow eyes":     ["LFT"],
    "vitamin":         ["VITD", "VITB12"],
    "bone pain":       ["VITD", "CBC"],
    "hair fall":       ["THYROID", "VITB12", "VITD", "CBC"],
    "anemia":          ["CBC", "VITB12"],
    "headache":        ["CBC", "THYROID", "BSF"],
    "body pain":       ["CBC", "VITD", "VITB12"],
    "anxiety":         ["THYROID", "CBC"],
    "depression":      ["THYROID", "VITD", "VITB12"],
    "routine checkup": ["CBC", "BSF", "LIPID", "KFT", "LFT", "URINE"],
    "full body":       ["CBC", "BSF", "LIPID", "KFT", "LFT", "THYROID", "VITD", "VITB12"],
}


def recommend_tests(symptom_text: str) -> list[dict]:
    """Return recommended test details based on symptom keywords."""
    symptom_lower = symptom_text.lower()
    matched_codes: set = set()

    for keyword, codes in SYMPTOM_TEST_MAP.items():
        if keyword in symptom_lower:
            matched_codes.update(codes)

    # Default if no match
    if not matched_codes:
        matched_codes = {"CBC"}

    return [
        {**{"code": code}, **TEST_CATALOG[code]}
        for code in matched_codes
        if code in TEST_CATALOG
    ]


def get_test_by_code(code: str) -> dict | None:
    return TEST_CATALOG.get(code.upper())


def all_tests_list() -> list[dict]:
    return [{"code": k, **v} for k, v in TEST_CATALOG.items()]
