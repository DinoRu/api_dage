"""Meter import endpoints."""

from uuid import UUID

from fastapi import APIRouter, File, UploadFile, Query, status
from fastapi.responses import StreamingResponse

from app.api.deps import DatabaseSession, SupervisorOrAdmin
from app.core.exceptions import BadRequestException, ForbiddenException
from app.schema.meter import MeterImportResult
from app.services.meter_import_service import meter_import_service

router = APIRouter(prefix="/meters/import", tags=["Meter Import"])


@router.get("/template")
async def download_template(
    current_user: SupervisorOrAdmin
):
    """
    Download Excel template for meter import.
    
    **Supervisor or Admin only**
    
    The template includes:
    - Required column headers
    - Example data rows
    - Instructions sheet with detailed guidance
    - Field descriptions and valid values
    """
    template_bytes = meter_import_service.generate_template()
    
    return StreamingResponse(
        iter([template_bytes]),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": "attachment; filename=meter_import_template.xlsx"
        }
    )


@router.post("/validate")
async def validate_import_file(
    file: UploadFile = File(..., description="Excel file to validate"),
    current_user: SupervisorOrAdmin = None
):
    """
    Validate Excel file before importing.
    
    **Supervisor or Admin only**
    
    This endpoint checks:
    - File format is valid Excel (.xlsx)
    - Required columns are present
    - Data structure is correct
    - Preview of the first 5 rows
    
    **Does not create any meters** - only validates the file structure.
    """
    # Validate file type
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise BadRequestException(
            "Invalid file format. Only Excel files (.xlsx, .xls) are allowed"
        )
    
    # Read file content
    content = await file.read()
    
    # Validate
    validation_result = await meter_import_service.validate_file_before_import(
        io.BytesIO(content)
    )
    
    return validation_result


@router.post("/upload", response_model=MeterImportResult, status_code=status.HTTP_201_CREATED)
async def import_meters_from_excel(
    city_id: UUID = Query(..., description="City ID for all meters in the file"),
    file: UploadFile = File(..., description="Excel file with meter data"),
    db: DatabaseSession = None,
    current_user: SupervisorOrAdmin = None
):
    """
    Import meters from Excel file.
    
    **Supervisor or Admin only**
    
    **Process**:
    1. Upload Excel file with meter data
    2. System validates each row
    3. Creates meters for valid rows
    4. Returns detailed report with successes and errors
    
    **File Requirements**:
    - Format: Excel (.xlsx or .xls)
    - Required columns: code, owner_name, address, meter_number
    - Optional columns: previous_reading, status
    - Use the template from /meters/import/template
    
    **Restrictions**:
    - Supervisors can only import for their assigned city
    - All codes and meter numbers must be unique
    - Maximum 1000 meters per file recommended
    
    **Response includes**:
    - Total rows processed
    - Number of successful imports
    - Number of failed imports
    - Detailed error list with row numbers
    - IDs of created meters
    """
    # Validate file type
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise BadRequestException(
            "Invalid file format. Only Excel files (.xlsx, .xls) are allowed"
        )
    
    # Check permission
    if current_user.is_supervisor() and current_user.city_id != city_id:
        raise ForbiddenException("You can only import meters for your assigned city")
    
    # Read file content
    content = await file.read()
    
    # Process import
    result = await meter_import_service.process_excel_file(
        db,
        io.BytesIO(content),
        city_id,
        current_user
    )
    
    return result


@router.post("/upload-with-validation", response_model=MeterImportResult)
async def import_meters_with_pre_validation(
    city_id: UUID = Query(..., description="City ID for all meters"),
    file: UploadFile = File(..., description="Excel file with meter data"),
    db: DatabaseSession = None,
    current_user: SupervisorOrAdmin = None
):
    """
    Import meters with pre-validation step.
    
    **Supervisor or Admin only**
    
    This endpoint performs a two-step process:
    1. Validates the file structure and data
    2. Only imports if validation passes completely
    
    Use this for stricter validation - the import will fail if ANY row has errors.
    Use the regular /upload endpoint if you want partial imports with error reporting.
    """
    # Validate file type
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise BadRequestException(
            "Invalid file format. Only Excel files (.xlsx, .xls) are allowed"
        )
    
    # Check permission
    if current_user.is_supervisor() and current_user.city_id != city_id:
        raise ForbiddenException("You can only import meters for your assigned city")
    
    # Read file content
    content = await file.read()
    
    # First validate
    validation = await meter_import_service.validate_file_before_import(
        io.BytesIO(content)
    )
    
    if not validation.get("valid"):
        raise BadRequestException(validation.get("error", "File validation failed"))
    
    # Then import
    result = await meter_import_service.process_excel_file(
        db,
        io.BytesIO(content),
        city_id,
        current_user
    )
    
    # If any errors occurred, return error
    if result.error_count > 0:
        raise BadRequestException(
            f"Import failed with {result.error_count} error(s). "
            "Please fix the errors and try again."
        )
    
    return result


import io