import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional

from database import db, create_document, get_documents
from schemas import Rfp, Rfpsection, Aigeneration

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "AI RFP Backend Running"}

@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
            response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
                response["connection_status"] = "Connected"
            except Exception as e:
                response["database"] = f"⚠️ Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️ Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"
    return response

# --------- RFP Endpoints ---------

class RfpCreate(BaseModel):
    title: str
    description: Optional[str] = None

@app.post("/api/rfps")
def create_rfp(payload: RfpCreate):
    rfp = Rfp(title=payload.title, description=payload.description)
    rfp_id = create_document("rfp", rfp)
    return {"id": rfp_id, "message": "RFP created"}

@app.get("/api/rfps")
def list_rfps():
    docs = get_documents("rfp")
    # normalize _id
    for d in docs:
        d["id"] = str(d.pop("_id"))
    return docs

class SectionCreate(BaseModel):
    rfp_id: str
    heading: str
    content: str = ""
    order: int = 0

@app.post("/api/sections")
def create_section(payload: SectionCreate):
    section = Rfpsection(**payload.model_dump())
    sec_id = create_document("rfpsection", section)
    return {"id": sec_id, "message": "Section created"}

@app.get("/api/sections")
def list_sections(rfp_id: Optional[str] = None):
    filter_q = {"rfp_id": rfp_id} if rfp_id else {}
    docs = get_documents("rfpsection", filter_q)
    for d in docs:
        d["id"] = str(d.pop("_id"))
    # sort by order ASC
    docs.sort(key=lambda x: x.get("order", 0))
    return docs

# --------- Simple AI Generation Stub ---------
# Note: This uses a simple heuristic for now. You can wire up a real LLM later.

class GenerateRequest(BaseModel):
    rfp_title: str
    section_heading: str
    context: Optional[str] = ""
    tone: str = "professional"

@app.post("/api/generate")
def generate_text(req: GenerateRequest):
    # Very simple template-based generation as a placeholder
    intro = f"This section addresses '{req.section_heading}' for the RFP titled '{req.rfp_title}'."
    tone_map = {
        "professional": "We will deliver a reliable, scalable, and secure solution.",
        "concise": "We address the requirements directly and efficiently.",
        "persuasive": "Our proven track record ensures exceptional outcomes.",
    }
    tone_sentence = tone_map.get(req.tone, tone_map["professional"])
    ctx = (req.context or "").strip()
    body = (
        f"Approach: {tone_sentence}\n\n" +
        (f"Context provided: {ctx}\n\n" if ctx else "") +
        "Methodology:\n- Discovery and planning\n- Implementation with best practices\n- Quality assurance and validation\n- Knowledge transfer and support\n\nDeliverables:\n- Detailed documentation\n- Clear timelines and milestones\n- Ongoing communication and risk management"
    )
    output = f"{intro}\n\n{body}"

    # Save generation record
    try:
        gen = Aigeneration(rfp_id="", section_id=None, prompt=f"{req.section_heading} | {req.context}", output=output)
        create_document("aigeneration", gen)
    except Exception:
        pass

    return {"text": output}


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
