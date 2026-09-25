from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Response, Body, status
from typing import List, Dict, Any
from backend.middleware.auth_deps import get_current_user, require_not_observer
from backend.services.import_service import (
    parse_docx_bytes, parse_xlsx_bytes, parse_csv_bytes,
    validate_import_data, confirm_import, get_import_history,
    generate_excel_template, generate_csv_template
)

router = APIRouter(prefix="/api/import", tags=["Import"])

MAX_FILE_SIZE = 15 * 1024 * 1024 # 15MB

@router.post("/validate")
async def validate_uploaded_file(file: UploadFile = File(...), current_user: dict = Depends(require_not_observer)):
    filename = file.filename or "unknown"
    ext = filename.split(".")[-1].lower()
    
    if ext not in ["docx", "xlsx", "csv"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Faqat .docx, .xlsx yoki .csv formatdagi fayllar qabul qilinadi"
        )
        
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="Fayl hajmi 15MB dan oshmasligi kerak")
    if len(content) == 0:
        raise HTTPException(status_code=400, detail="Yuklangan fayl bo'sh")
        
    try:
        if ext == "docx":
            raw_rows = parse_docx_bytes(content)
        elif ext == "xlsx":
            raw_rows = parse_xlsx_bytes(content)
        else: # csv
            raw_rows = parse_csv_bytes(content)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Faylni o'qishda xatolik yuz berdi: {str(e)}")
        
    if not raw_rows:
        raise HTTPException(status_code=400, detail="Faylda jadval yoki ma'lumot qatorlari topilmadi")
        
    validation_res = validate_import_data(raw_rows, filename)
    validation_res["file_type"] = ext
    return validation_res

@router.post("/confirm")
def execute_import(payload: Dict[str, Any] = Body(...), current_user: dict = Depends(require_not_observer)):
    rows = payload.get("rows", [])
    file_name = payload.get("file_name", "manual_import")
    file_type = payload.get("file_type", "xlsx")
    
    if not rows:
        raise HTTPException(status_code=400, detail="Import qilish uchun qatorlar topilmadi")
        
    return confirm_import(rows, file_name, file_type, current_user)

@router.get("/history")
def import_logs(limit: int = 20, offset: int = 0, current_user: dict = Depends(get_current_user)):
    return get_import_history(limit, offset)

@router.get("/template/excel")
def download_excel_template():
    content = generate_excel_template()
    return Response(
        content=content,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=ttj_talabalar_shablon.xlsx"}
    )

@router.get("/template/csv")
def download_csv_template():
    content = generate_csv_template()
    return Response(
        content=content,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=ttj_talabalar_shablon.csv"}
    )
