"""Export routes with PDF support."""
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response

from social_hunter.auth.middleware import AuthContext, require_auth, require_paid_plan
from social_hunter.models import ExportRequest, ExportResponse, SearchResponse
from social_hunter.services.pdf_generator import pdf_generator

router = APIRouter(prefix="/exports", tags=["exports"])


@router.post("", response_model=ExportResponse)
async def export_search(
    request: ExportRequest,
    context: Annotated[AuthContext, Depends(require_auth)],
) -> ExportResponse:
    """Export search results."""
    # ... existing JSON/CSV/Markdown logic ...

    if request.format == "pdf":
        # Check if user has export permission
        if not context.plan in ["hobby", "pro", "team"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="PDF export requires paid plan",
            )

        pdf_bytes, filename = await pdf_generator.generate_pdf_with_metadata(request.search)

        return ExportResponse(
            filename=filename,
            content_type="application/pdf",
            content=pdf_bytes.decode("latin-1"),  # FastAPI will encode properly
        )

    # ... rest of existing logic ...


@router.post("/pdf")
async def export_pdf(
    search: SearchResponse,
    context: Annotated[AuthContext, Depends(require_paid_plan)],
) -> Response:
    """Direct PDF download endpoint."""
    pdf_bytes, filename = await pdf_generator.generate_pdf_with_metadata(search)

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
        },
    )
