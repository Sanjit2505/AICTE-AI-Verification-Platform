import re
from app.database import fetch_all, fetch_one

DEFAULT_HANDBOOK_CHUNKS = [
    {
        "source_doc": "AICTE Approval Process Handbook 2024-2027",
        "clause_ref": "Clause 2.4.1",
        "title": "Mandatory Clearance - Fire and Life Safety NOC",
        "text": "For Continuation of Approval (EoA) and introduction of new courses, an Institution must submit a valid Fire Safety Certificate / NOC issued by the Competent Fire Service Authority of the respective State or UT. If the validity of the NOC has expired, the Institution must provide an active renewal receipt or current inspection clearance. Applications with expired or fabricated fire safety clearance shall not be recommended for approval until rectified."
    },
    {
        "source_doc": "AICTE Approval Process Handbook 2024-2027",
        "clause_ref": "Clause 1.3.2",
        "title": "Expansion of Intake and Introduction of New Courses",
        "text": "Institutions seeking increase in intake or additional divisions must possess valid National Board of Accreditation (NBA) accreditation for at least 50% of eligible technical programmes. The total intake expansion is capped at 60 seats per application cycle, unless the institution ranks within the top 100 NIRF or holds NAAC A++ grading."
    },
    {
        "source_doc": "AICTE Approval Process Handbook 2024-2027",
        "clause_ref": "Appendix 7.1",
        "title": "Faculty Cadre and Student-to-Faculty Ratio (SFR)",
        "text": "For Undergraduate Engineering and Technology degree programmes, the mandatory Student-to-Faculty Ratio (SFR) is 1:15 based on sanctioned intake. The Faculty Cadre ratio shall be maintained as 1:2:6 (Professor : Associate Professor : Assistant Professor). Faculty members must be dedicated, appointed through a duly constituted selection committee, and possess verified qualification credentials without concurrent dual employment."
    },
    {
        "source_doc": "AICTE Approval Process Handbook 2024-2027",
        "clause_ref": "Appendix 4.2",
        "title": "Land and Building Infrastructure Norms",
        "text": "Land requirement for technical institutions situated in Mega and Metro cities is minimum 1.5 acres; in Urban areas minimum 2.5 acres; and in Rural areas minimum 7.5 acres. The land parcel must be contiguous, registered in the name of the sponsoring Trust or Society by registered sale deed or registered lease deed of at least 30 years duration, free from any non-educational encumbrances."
    },
    {
        "source_doc": "AICTE Approval Process Handbook 2024-2027",
        "clause_ref": "Appendix 5.1",
        "title": "Essential Computing Facilities & Internet Bandwidth",
        "text": "The minimum number of desktop terminals/laptops required for technical courses is 1 terminal for every 4 students in Engineering UG, and 1 terminal for every 2 students in MCA/M.Tech. Continuous Internet bandwidth of minimum 100 Mbps (for intake <= 300) or 300 Mbps (for intake > 300) must be operational and verified through valid ISP speed bills."
    },
    {
        "source_doc": "AICTE Approval Process Handbook 2024-2027",
        "clause_ref": "Clause 3.8",
        "title": "Anti-Ragging Undertaking and Affidavit Submission",
        "text": "Every institution must upload statutory affidavits regarding Anti-Ragging compliance under Regulation F.No.37-3/Legal/AICTE/2009. The affidavit must be sworn before an Executive Magistrate or Notary Public within 12 months of the active approval cycle. Submitting dated or non-notarized affidavits constitutes a deficiency."
    }
]

def query_handbook_copilot(query: str) -> dict:
    """
    RAG Copilot: answers officer queries citing exact handbook clauses.
    If no clause matches query concepts, returns 'not found in the provided documents.'
    """
    chunks = fetch_all("SELECT clause_ref, title, text, source_doc FROM handbook_chunks")
    if not chunks:
        chunks = DEFAULT_HANDBOOK_CHUNKS

    query_words = set(re.findall(r'\w+', query.lower()))
    stop_words = {"is", "a", "the", "for", "in", "of", "and", "or", "what", "how", "can", "to", "are", "by", "with", "does"}
    keywords = query_words - stop_words

    if not keywords:
        return {
            "answer": "Please ask a specific regulatory question regarding AICTE handbook clauses, norms, intake, faculty, or documentation.",
            "citations": []
        }

    scored_chunks = []
    for chunk in chunks:
        chunk_text = (chunk["title"] + " " + chunk["text"] + " " + chunk["clause_ref"]).lower()
        score = sum(1 for kw in keywords if kw in chunk_text)
        if score > 0:
            scored_chunks.append((score, chunk))

    scored_chunks.sort(key=lambda x: x[0], reverse=True)

    if not scored_chunks:
        return {
            "answer": "Not found in the provided documents. No specific clause in the loaded AICTE Approval Process Handbook directly addresses this inquiry.",
            "citations": []
        }

    top_chunk = scored_chunks[0][1]
    clause_ref = top_chunk["clause_ref"]
    title = top_chunk["title"]
    text = top_chunk["text"]

    # Generate grounded natural answer
    answer = f"According to **{top_chunk['source_doc']} ({clause_ref} - {title})**:\n\n{text}\n\n*Key Compliance Takeaway*: Officers must verify official records and check that all documentary evidence aligns directly with this stipulation."

    citations = [
        {
            "clause": clause_ref,
            "title": title,
            "source": top_chunk["source_doc"],
            "snippet": text[:200] + "..."
        }
    ]

    return {
        "answer": answer,
        "citations": citations
    }
