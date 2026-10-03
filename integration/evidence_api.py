from fastapi import APIRouter, HTTPException, Request
from blockchain.service import EvidenceService
from blockchain.chain_of_custody import ChainOfCustody

router = APIRouter(prefix="/evidence", tags=["Evidence Integrity"])

@router.post("/register")
async def register_evidence(request: Request):
    raw_email = await request.body()
    if not raw_email:
        raise HTTPException(status_code=400, detail="Email content is empty")
    try:
        return EvidenceService.register_evidence(raw_email)
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error))

@router.get("/{case_id}")
async def get_evidence(case_id: str):
    case = EvidenceService.get_case(case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    return case

@router.get("/{case_id}/audit")
async def get_audit_trail(case_id: str):
    trail = ChainOfCustody.get_audit_trail(case_id)
    if not trail:
        raise HTTPException(status_code=404, detail="Case not found or no audit events")
    return {"case_id": case_id, "audit_events": trail}

@router.post("/{case_id}/verify")
async def verify_evidence(case_id: str):
    try:
        return EvidenceService.verify_case_integrity(case_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{case_id}/anchor")
async def anchor_evidence(case_id: str):
    try:
        return EvidenceService.anchor_evidence(case_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
