import os
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from app.config import UPLOAD_DIR

def generate_synthetic_fire_noc(filename: str, noc_no: str, institute_name: str, issue_date: str, expiry_date: str, is_expired: bool = False) -> str:
    file_path = os.path.join(UPLOAD_DIR, filename)
    doc = SimpleDocTemplate(file_path, pagesize=letter, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'GovTitle',
        parent=styles['Heading1'],
        fontSize=14,
        textColor=colors.HexColor('#0f172a'),
        alignment=1, # Center
        spaceAfter=10
    )
    subtitle_style = ParagraphStyle(
        'GovSub',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#475569'),
        alignment=1,
        spaceAfter=15
    )
    body_style = ParagraphStyle(
        'GovBody',
        parent=styles['Normal'],
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#1e293b')
    )
    
    elements = []
    
    # Header
    elements.append(Paragraph("<b>GOVERNMENT OF NATIONAL CAPITAL TERRITORY OF DELHI</b>", title_style))
    elements.append(Paragraph("<b>HEADQUARTERS: DELHI FIRE SERVICE, CONNAUGHT CIRCUS, NEW DELHI</b>", subtitle_style))
    elements.append(Paragraph("<b>FORM 'H': FIRE SAFETY CERTIFICATE / NO OBJECTION CERTIFICATE (NOC)</b>", ParagraphStyle('H2', parent=title_style, fontSize=11, spaceAfter=15)))
    elements.append(Spacer(1, 10))
    
    data = [
        ["Certificate / Dispatch No.:", noc_no],
        ["Dated / Date of Issue:", issue_date],
        ["Issued To Institution:", institute_name],
        ["Type of Occupancy:", "Educational Building (Technical Campus)"],
        ["Maximum Building Height:", "14.80 Metres (Ground + 3 Upper Floors)"],
        ["Certificate Expiry Date:", expiry_date],
        ["Status of Compliance:", "EXPIRED - CLEARANCE LAPSED" if is_expired else "VERIFIED COMPLIANT"]
    ]
    
    t = Table(data, colWidths=[200, 320])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f8fafc')),
        ('TEXTCOLOR', (0,0), (-1,-1), colors.HexColor('#0f172a')),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold'),
        ('FONTNAME', (1,0), (1,-1), 'Helvetica'),
        ('FONTSIZE', (0,0), (-1,-1), 10),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
    ]))
    elements.append(t)
    elements.append(Spacer(1, 25))
    
    body_text = f"""
    Certified that the premises of <b>{institute_name}</b> comprised of Ground plus Three upper floors was inspected by the officers concerned of Delhi Fire Service in the presence of the authorised management representative and observed that the building has complied with the fire prevention and fire safety requirements in accordance with Rule 33 of Delhi Fire Service Rules, 2010.
    <br/><br/>
    The Fire Safety Certificate is valid up to <b>{expiry_date}</b> subject to condition that the fire detection and fighting system are maintained in operational condition at all times.
    """
    elements.append(Paragraph(body_text, body_style))
    elements.append(Spacer(1, 40))
    
    footer_data = [
        ["[QR CODE VALIDATED]", "DIRECTOR / CHIEF FIRE OFFICER"],
        [f"HASH: SHA256_{noc_no[:8]}", "DELHI FIRE SERVICE, GOVT OF NCT OF DELHI"]
    ]
    ft = Table(footer_data, colWidths=[260, 260])
    ft.setStyle(TableStyle([
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 9),
        ('ALIGN', (1,0), (1,-1), 'RIGHT'),
        ('TEXTCOLOR', (0,0), (-1,-1), colors.HexColor('#475569'))
    ]))
    elements.append(ft)
    
    doc.build(elements)
    return file_path
