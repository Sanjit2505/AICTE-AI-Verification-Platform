import os
import re
from datetime import datetime
from PIL import Image, ImageChops, ImageEnhance
import imagehash
from app.config import UPLOAD_DIR

SUSPICIOUS_SOFTWARE = ["photoshop", "gimp", "canva", "coreldraw", "nitro", "sejda", "ilovepdf", "pdfescape", "inkscape"]

def generate_ela_heatmap(image_path: str, output_path: str, quality: int = 90) -> float:
    """
    Performs Error Level Analysis (ELA) on an image or converted PDF page.
    Saves the enhanced error difference heatmap as an artifact.
    Returns anomaly intensity score (0.0 to 1.0).
    """
    try:
        orig = Image.open(image_path).convert('RGB')
        temp_resave = str(output_path) + ".temp.jpg"
        orig.save(temp_resave, 'JPEG', quality=quality)
        resaved = Image.open(temp_resave)
        
        # Calculate difference
        diff = ImageChops.difference(orig, resaved)
        
        # Extrapolate difference to visual levels
        extrema = diff.getextrema()
        max_diff = max([ex[1] for ex in extrema])
        scale = 255.0 / max_diff if max_diff > 0 else 1.0
        diff = ImageEnhance.Brightness(diff).enhance(scale)
        diff.save(output_path, 'PNG')
        
        if os.path.exists(temp_resave):
            os.remove(temp_resave)
            
        anomaly_score = min(round(max_diff / 50.0, 3), 0.98)
        return anomaly_score
    except Exception as e:
        print(f"ELA Error: {e}")
        return 0.15

def calculate_phash(file_path: str) -> str:
    try:
        img = Image.open(file_path)
        return str(imagehash.phash(img))
    except Exception:
        # Fallback pseudo-phash
        with open(file_path, "rb") as f:
            chunk = f.read(1024)
        return format(abs(hash(chunk)) % (16**16), '016x')

def inspect_metadata(doc_info: dict) -> list[dict]:
    """
    Examines PDF/Image metadata for signs of tampering, editing software, or timeline manipulation.
    """
    anomalies = []
    producer = doc_info.get("producer", "").lower()
    creator = doc_info.get("creator", "").lower()
    
    for sw in SUSPICIOUS_SOFTWARE:
        if sw in producer or sw in creator:
            anomalies.append({
                "type": "METADATA_TAMPER",
                "severity": "HIGH",
                "title": "Document Re-saved with Image Editing Software",
                "reason": f"Document metadata indicates manipulation using '{sw.capitalize()}'. Potential forgery or alteration of original authority seal/values.",
                "confidence": 0.94,
                "evidence": {
                    "kind": "METADATA",
                    "snippet": f"Producer: {doc_info.get('producer')}, Creator: {doc_info.get('creator')}"
                }
            })
            break
            
    # Check date discrepancies
    mod_date_str = doc_info.get("mod_date")
    issue_date_str = doc_info.get("issue_date")
    if mod_date_str and issue_date_str:
        try:
            mod_dt = datetime.fromisoformat(mod_date_str[:10])
            issue_dt = datetime.fromisoformat(issue_date_str[:10])
            if mod_dt > issue_dt and (mod_dt - issue_dt).days > 365:
                anomalies.append({
                    "type": "CHRONOLOGY_ANOMALY",
                    "severity": "MEDIUM",
                    "title": "Metadata Modification Timeline Inconsistency",
                    "reason": f"File digital modification date ({mod_date_str[:10]}) is substantially later than claimed issue date ({issue_date_str[:10]}).",
                    "confidence": 0.88,
                    "evidence": {
                        "kind": "METADATA",
                        "snippet": f"Stated Issue: {issue_date_str} vs File Mod: {mod_date_str}"
                    }
                })
        except Exception:
            pass
            
    return anomalies

def check_dates_logic(issue_date_str: str, expiry_date_str: str, application_date_str: str = None) -> list[dict]:
    flags = []
    try:
        now = datetime.utcnow()
        if issue_date_str:
            issue_dt = datetime.strptime(issue_date_str[:10], "%Y-%m-%d")
            if issue_dt > now:
                flags.append({
                    "type": "FUTURE_DATE",
                    "severity": "HIGH",
                    "title": "Future-Dated Document Detected",
                    "reason": f"The document issue date ({issue_date_str}) is in the future. Potential synthetic or fraudulent certificate.",
                    "confidence": 0.98
                })
                
        if expiry_date_str:
            exp_dt = datetime.strptime(expiry_date_str[:10], "%Y-%m-%d")
            app_dt = datetime.strptime(application_date_str[:10], "%Y-%m-%d") if application_date_str else now
            if exp_dt < app_dt:
                flags.append({
                    "type": "EXPIRED_DOCUMENT",
                    "severity": "HIGH",
                    "title": "Expired Mandatory Clearance/NOC",
                    "reason": f"Certificate expired on {expiry_date_str}, which is prior to the active approval cycle date ({app_dt.strftime('%Y-%m-%d')}).",
                    "confidence": 0.99
                })
    except Exception as e:
        print(f"Date check error: {e}")
    return flags
