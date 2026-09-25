from fastapi import APIRouter, HTTPException, Depends, Query, Response
from backend.middleware.auth_deps import get_current_user
from backend.services.report_service import (
    get_report_data, export_report_csv, export_report_excel, export_report_pdf, REPORT_TITLES
)

router = APIRouter(prefix="/api/reports", tags=["Hisobotlar"])

@router.get("/types")
def list_report_types(current_user: dict = Depends(get_current_user)):
    return [{"id": k, "title": v} for k, v in REPORT_TITLES.items()]

@router.get("/{report_type}")
def get_report_preview(report_type: str, current_user: dict = Depends(get_current_user)):
    if report_type not in REPORT_TITLES:
        raise HTTPException(status_code=404, detail="Hisobot turi topilmadi")
    title, headers, rows = get_report_data(report_type)
    return {
        "title": title,
        "headers": headers,
        "rows": rows[:100],
        "total_rows": len(rows)
    }

@router.get("/{report_type}/export")
def export_report(report_type: str, format: str = Query("excel", regex="^(excel|csv|pdf)$"), current_user: dict = Depends(get_current_user)):
    if report_type not in REPORT_TITLES:
        raise HTTPException(status_code=404, detail="Hisobot turi topilmadi")
        
    filename_base = f"ttj_hisobot_{report_type}"
    if format == "csv":
        content = export_report_csv(report_type)
        return Response(
            content=content,
            media_type="text/csv; charset=utf-8",
            headers={"Content-Disposition": f"attachment; filename={filename_base}.csv"}
        )
    elif format == "excel":
        content = export_report_excel(report_type)
        return Response(
            content=content,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename_base}.xlsx"}
        )
    elif format == "pdf":
        content = export_report_pdf(report_type)
        return Response(
            content=content,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename_base}.pdf"}
        )
