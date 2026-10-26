import os
from datetime import datetime
from PIL import Image, ImageChops, ImageEnhance
import imagehash
from app.config import UPLOAD_DIR

SUSPICIOUS_SOFTWARE = ["photoshop", "gimp", "canva", "coreldraw", "nitro", "sejda", "ilovepdf", "pdfescape", "inkscape", "foxit phantom"]

class ForensicAnalysisAgent:
    """
    Forensic Agent: Inspects digital document forensics, metadata, ELA heatmaps, and chronology.
    """
    def __init__(self):
        self.name = "Forensics & Metadata Agent"

    def analyze_metadata(self, metadata: dict) -> list[dict]:
        anomalies = []
        producer = str(metadata.get("producer", "")).lower()
        creator = str(metadata.get("creator", "")).lower()

        for sw in SUSPICIOUS_SOFTWARE:
            if sw in producer or sw in creator:
                anomalies.append({
                    "type": "METADATA_TAMPER",
                    "severity": "HIGH",
                    "title": "Document Edited with Image Manipulation Software",
                    "reason": f"File metadata identifies editing tool '{sw.title()}'. Indicates potential digital alteration of stamps, dates, or values.",
                    "confidence": 0.94,
                    "evidence_snippet": f"Producer: {metadata.get('producer')}, Creator: {metadata.get('creator')}"
                })
                break

        # Chronology inspection
        mod_date = str(metadata.get("mod_date", ""))
        creation_date = str(metadata.get("creation_date", ""))
        if mod_date and creation_date and len(mod_date) >= 8 and len(creation_date) >= 8:
            try:
                mod_yr = int(mod_date[2:6]) if mod_date.startswith("D:") else int(mod_date[:4])
                cre_yr = int(creation_date[2:6]) if creation_date.startswith("D:") else int(creation_date[:4])
                if mod_yr - cre_yr > 3:
                    anomalies.append({
                        "type": "CHRONOLOGY_ANOMALY",
                        "severity": "MEDIUM",
                        "title": "Unusual Digital Modification Gap",
                        "reason": f"File last modified {mod_yr}, while initial creation was {cre_yr}. Digital lifespan anomaly detected.",
                        "confidence": 0.82,
                        "evidence_snippet": f"Created: {creation_date} | Modified: {mod_date}"
                    })
            except Exception:
                pass

        return anomalies

    def generate_ela_heatmap(self, image_or_pdf_path: str, artifact_name: str) -> dict:
        """
        Error Level Analysis (ELA): Amplifies compression discrepancies to highlight spliced regions.
        """
        out_path = os.path.join(UPLOAD_DIR, artifact_name + ".ela.png")
        try:
            # If it's an image
            if image_or_pdf_path.lower().endswith((".png", ".jpg", ".jpeg")):
                orig = Image.open(image_or_pdf_path).convert("RGB")
            else:
                # PDF: rasterize first page using pypdfium2 if available, or generate blank heatmap
                try:
                    import pypdfium2 as pdfium
                    pdf = pdfium.PdfDocument(image_or_pdf_path)
                    page = pdf[0]
                    pil_img = page.render(scale=1.5).to_pil()
                    orig = pil_img.convert("RGB")
                except Exception:
                    return {"has_ela": False, "score": 0.05, "artifact_key": None}

            temp_resave = out_path + ".temp.jpg"
            orig.save(temp_resave, "JPEG", quality=90)
            resaved = Image.open(temp_resave)

            diff = ImageChops.difference(orig, resaved)
            extrema = diff.getextrema()
            max_diff = max([ex[1] for ex in extrema])
            scale = 255.0 / max_diff if max_diff > 0 else 1.0
            enhanced = ImageEnhance.Brightness(diff).enhance(scale)
            enhanced.save(out_path, "PNG")

            if os.path.exists(temp_resave):
                os.remove(temp_resave)

            anomaly_score = min(round(max_diff / 50.0, 3), 0.98)
            return {
                "has_ela": True,
                "score": anomaly_score,
                "artifact_key": artifact_name + ".ela.png",
                "is_spliced": anomaly_score > 0.85
            }
        except Exception as e:
            print(f"ELA generation note: {e}")
            return {"has_ela": False, "score": 0.05, "artifact_key": None}

    def check_dates(self, issue_date_str: str, expiry_date_str: str) -> list[dict]:
        flags = []
        now = datetime.utcnow()
        if issue_date_str:
            try:
                issue_dt = datetime.strptime(issue_date_str[:10], "%Y-%m-%d")
                if issue_dt > now:
                    flags.append({
                        "type": "FUTURE_DATE",
                        "severity": "HIGH",
                        "title": "Future-Dated Document Detected",
                        "reason": f"Issue date stated on certificate ({issue_date_str}) is in the future. Potential synthetic or fraudulent certificate.",
                        "confidence": 0.99
                    })
            except Exception:
                pass

        if expiry_date_str:
            try:
                exp_dt = datetime.strptime(expiry_date_str[:10], "%Y-%m-%d")
                if exp_dt < now:
                    flags.append({
                        "type": "EXPIRED_DOCUMENT",
                        "severity": "HIGH",
                        "title": "Statutory Clearance Has Expired",
                        "reason": f"Clearance expired on {expiry_date_str}. AICTE requires a current valid renewal prior to processing approval.",
                        "confidence": 0.99
                    })
            except Exception:
                pass

        return flags

forensic_agent = ForensicAnalysisAgent()
