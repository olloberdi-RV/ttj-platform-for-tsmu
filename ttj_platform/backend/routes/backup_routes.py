import datetime
from fastapi import APIRouter, Depends, Response, UploadFile, File, HTTPException
from backend.middleware.auth_deps import require_role
from backend.services.backup_service import create_backup_json, restore_backup_json

router = APIRouter(prefix="/api/backup", tags=["Zaxira nusxasi"])

@router.get("/download")
def download_backup(current_user: dict = Depends(require_role(["super_admin"]))):
    json_data = create_backup_json()
    filename = f"ttj_backup_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    return Response(
        content=json_data,
        media_type="application/json",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@router.post("/restore")
async def restore_backup(file: UploadFile = File(...), current_user: dict = Depends(require_role(["super_admin"]))):
    content = await file.read()
    try:
        json_str = content.decode('utf-8')
        return restore_backup_json(json_str, current_user)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Zaxira nusxasini tiklashda xatolik: {str(e)}")
