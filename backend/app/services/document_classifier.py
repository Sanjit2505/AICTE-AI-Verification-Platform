import os
import joblib
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from app.config import BASE_DIR

MODEL_PATH = BASE_DIR / "app" / "services" / "trained_doc_classifier.pkl"

# Training corpus representing Indian statutory certificates under AICTE norms
TRAINING_SAMPLES = [
    # 0: Fire Safety NOC
    ("Delhi Fire Service headquarters Connaught Circus Form H Fire Safety Certificate NOC Rule 33 fire prevention firefighting measures valid up to operational hydrant extinguisher inspection", "Fire Safety NOC"),
    ("State Fire and Emergency Services Government of Tamil Nadu No Objection Certificate compliance with National Building Code Part 4 fire fighting equipment fire clearance certificate", "Fire Safety NOC"),
    ("Office of the Chief Fire Officer Karnataka Fire and Emergency Services clearance certificate issued under fire force act premises inspected valid till fire noc dispatch no", "Fire Safety NOC"),
    ("Fire safety inspection report building height 14.80 meters smoke detectors fire alarm system hose reel pump fire audit clearance issued to college", "Fire Safety NOC"),

    # 1: Land Title Deed
    ("Registered Sale Deed Sub Registrar office Khasra survey number plot schedule property registered in favour of educational trust absolute owner unencumbered educational use 30 years lease deed", "Land Title Deed"),
    ("Deed of conveyance registered transfer of property book volume page land measuring 2.50 acres bounded by survey khasra revenue district non-agricultural educational certification", "Land Title Deed"),
    ("Tahsildar office revenue department land possession certificate land conversion order patta chitta khata certificate registered under society registration act educational campus land deed", "Land Title Deed"),
    ("Registered 33 years perpetual lease deed lessor lessee registered trust land schedule survey no village taluk registration district sub-registrar seal and stamp", "Land Title Deed"),

    # 2: Structural Safety Certificate
    ("Structural stability certificate National Building Code 2016 Chartered Structural Engineer licensed certified that educational building designed seismic zone earthquake resistance safe load bearing capacity", "Structural Safety Certificate"),
    ("Form 4 Structural Engineers Certificate stability of building foundation column beam slab structural audit inspected educational institutional occupancy structural soundness", "Structural Safety Certificate"),
    ("Certificate of structural stability registered structural consultant municipal corporation safe for running technical college classroom laboratory load calculations", "Structural Safety Certificate"),

    # 3: Anti-Ragging Affidavit
    ("Affidavit under AICTE Regulation F.No.37-3/Legal/AICTE/2009 sworn before Notary Public Executive Magistrate undertaking curbing the menace of ragging solemn affirmation deponent", "Anti-Ragging Affidavit"),
    ("Statutory Undertaking Affidavit executed on non-judicial stamp paper deponent principal chairman trust will not indulge or abet ragging penal action under AICTE regulation", "Anti-Ragging Affidavit"),
    ("Notarized affidavit non-commercial character of trust no donations capitation fee compliance with AICTE approval process handbook 2024-2027 sworn before advocate notary public", "Anti-Ragging Affidavit"),

    # 4: Occupancy Certificate
    ("Municipal Corporation Building Proposal Department Occupancy Certificate Completion Certificate sanctioned building plan Ground plus three floors ready for occupation", "Occupancy Certificate"),
    ("Town and Country Planning Directorate Development Authority occupancy permission partial completion certificate architectural sanction plan approved educational use", "Occupancy Certificate"),
    ("Gram Panchayat Town Planning Department Building Completion Cum Occupancy Certificate inspected as per approved plan permitted occupancy", "Occupancy Certificate"),

    # 5: University Affiliation Order
    ("State Technical University Syndicate Resolution Affiliation Order continuation of provisional affiliation academic year B.Tech M.Tech programmes sanctioned intake approved by university", "University Affiliation Order"),
    ("Office of the Registrar Anna University VTU AKTU order grant of affiliation approved programmes academic council syndicate approval inspection committee report", "University Affiliation Order")
]

class AICTEDocumentClassifier:
    def __init__(self):
        self.model = None
        self._initialize_or_load()

    def _initialize_or_load(self):
        if os.path.exists(MODEL_PATH):
            try:
                self.model = joblib.load(MODEL_PATH)
                return
            except Exception:
                pass
        self._train_and_save()

    def _train_and_save(self):
        X = [text for text, label in TRAINING_SAMPLES]
        y = [label for text, label in TRAINING_SAMPLES]

        pipeline = Pipeline([
            ('tfidf', TfidfVectorizer(ngram_range=(1, 2), min_df=1, sublinear_tf=True)),
            ('clf', LogisticRegression(C=5.0, max_iter=200, random_state=42))
        ])

        pipeline.fit(X, y)
        self.model = pipeline
        try:
            joblib.dump(pipeline, MODEL_PATH)
        except Exception as e:
            print(f"Could not cache model: {e}")

    def classify(self, text: str, declared_category: str = "") -> dict:
        """
        Classifies document text into official AICTE regulatory certificate types.
        Detects if declared category contradicts actual content.
        """
        if not text or len(text.strip()) < 15:
            return {
                "predicted_category": declared_category or "Unclassified Document",
                "confidence": 0.50,
                "is_match": True,
                "category_anomaly": False
            }

        probs = self.model.predict_proba([text])[0]
        classes = self.model.classes_
        top_idx = np.argmax(probs)
        pred_label = classes[top_idx]
        confidence = float(probs[top_idx])

        # Normalize comparison
        is_match = True
        category_anomaly = False
        if declared_category:
            decl_norm = declared_category.lower().replace("_", " ").replace("-", " ")
            pred_norm = pred_label.lower().replace("_", " ").replace("-", " ")
            
            # Check key overlap
            tokens_decl = set(decl_norm.split())
            tokens_pred = set(pred_norm.split())
            common = tokens_decl.intersection(tokens_pred)
            
            if not common and confidence > 0.65:
                is_match = False
                category_anomaly = True

        return {
            "predicted_category": pred_label,
            "confidence": round(confidence, 3),
            "is_match": is_match,
            "category_anomaly": category_anomaly,
            "all_scores": {classes[i]: round(float(probs[i]), 3) for i in range(len(classes))}
        }

classifier = AICTEDocumentClassifier()
