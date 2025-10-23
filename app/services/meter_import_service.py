"""Meter import service for Excel files."""

import io
import logging
from typing import BinaryIO, Optional
from uuid import UUID

import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequestException
from app.models.meter import MeterStatus
from app.models.user import User
from app.schema.meter import (
    MeterCreate, 
    MeterImportRow,
    MeterImportResult,
    MeterImportError
)

from app.services.meter_v2 import meter_service

logger = logging.getLogger(__name__)



RUS_COLS = {
    'code': 'Идентификационный код',
    'owner_name': 'Наименование объекта сети',
    'address': 'Адрес',
    'meter_number': 'Номер ПУ',
    'meter_type': 'Тип прибора учета',
    'previous_reading': 'Предыдущие показания',
    'current_reading': 'Текущие показания',
    'status': 'Статус'
}


class MeterImportService:
    """Service for importing meters from Excel files."""
    
    
    # Required columns in Excel file
    REQUIRED_COLUMNS = [
        RUS_COLS['code'],
        RUS_COLS['owner_name'],
        RUS_COLS['address'],
        RUS_COLS['meter_number'],
        RUS_COLS['meter_type']
    ]
    
    # Optional columns
    OPTIONAL_COLUMNS = [
        RUS_COLS['previous_reading'],
        RUS_COLS['status']
    ]
    
    # All valid columns
    ALL_COLUMNS = REQUIRED_COLUMNS + OPTIONAL_COLUMNS
    
    async def process_excel_file(
        self,
        db: AsyncSession,
        file: BinaryIO,
        city_id: UUID,
        user: User
    ) -> MeterImportResult:
        """
            Process Excel file and create meters.
            
            Args:
                db: Database session
                file: Excel file stream
                city_id: City ID for all meters
                user: User performing the import
                
            Returns:
                MeterImportResult with details of the operation
        """
        try:
            # Read Excel file
            df = pd.read_excel(file, engine='openpyxl', header=1)
        except Exception as e:
            raise BadRequestException(f"Failed to read Excel file: {str(e)}")
        
        # Validate columns
        self._validate_columns(df)
        
        # Clean data
        df = self._clean_dataframe(df)
        
        # Initialize result tracking
        errors: list[MeterImportError] = []
        created_meters: list[UUID] = []
        success_count = 0
        skipped_count = 0
        
        # Process each row
        for idx, row in df.iterrows():
            row_number = idx + 3  # Excel row number (1-indexed + header)
            
            try:
                # Skip empty rows
                if row.isna().all():
                    skipped_count += 1
                    continue
                
                # Validate and create meter
                meter = await self._process_row(
                    db,
                    row,
                    row_number,
                    city_id,
                    user
                )
                if meter:
                    created_meters.append(meter.id)
                    success_count += 1
                    
            except Exception as e:
                error = MeterImportError(
                    row_number=row_number,
                    code=str(row.get('code', '')) if not pd.isna(row.get('code')) else None,
                    meter_number=str(row.get('meter_number', '')) if not pd.isna(row.get('meter_number')) else None,
                    error=str(e),
                    field=self._extract_error_field(str(e))
                )
                errors.append(error)
                logger.warning(f"Row {row_number} failed: {str(e)}")
        
        # Calculate totals
        total_rows = len(df) - skipped_count
        error_count = len(errors)
        
        # Create result
        result = MeterImportResult(
            success=error_count == 0,
            total_rows=total_rows,
            success_count=success_count,
            error_count=error_count,
            skipped_count=skipped_count,
            errors=[error.model_dump() for error in errors],
            created_meters=created_meters,
            message=self._generate_summary_message(
                total_rows,
                success_count,
                error_count,
                skipped_count
            )
        )
        
        return result
    
    def _validate_columns(self, df: pd.DataFrame) -> None:
        """Validate that required columns are present."""
        df_columns = [col.lower().strip() for col in df.columns]
        required_columns_normalized = [col.lower().strip() for col in self.REQUIRED_COLUMNS]
        missing_columns = [
            col for col in required_columns_normalized
            if col not in df_columns
        ]
        
        if missing_columns:
            logger.error(f"Found columns: {list(df.columns)}")
            raise BadRequestException(
                f"Missing required columns: {', '.join(missing_columns)}"
            )
    
    def _clean_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and normalize dataframe."""
        # Normalize column names
        df.columns = [col.lower().strip() for col in df.columns]
        
        col_mapping = {v.lower().strip(): k for k, v in RUS_COLS.items()}  # Inverse RUS_COLS
        df = df.rename(columns=col_mapping)

        # Remove completely empty rows
        df = df.dropna(how='all')
        
        # Strip whitespace from string columns
        string_columns = df.select_dtypes(include=['object']).columns
        for col in string_columns:
            df[col] = df[col].apply(
                lambda x: x.strip() if isinstance(x, str) else x
            )
        
        return df
    
    async def _process_row(
        self,
        db: AsyncSession,
        row: pd.Series,
        row_number: int,
        city_id: UUID,
        user: User
    ) -> Optional[object]:
        """Process a single row and create meter."""
        # Extract data
        row_data = {
            'code': row.get('code'),
            'owner_name': row.get('owner_name'),
            'address': row.get('address'),
            'meter_number': row.get('meter_number'),
            'meter_type': row.get('meter_type'),
            'previous_reading': row.get('previous_reading'),
            'status': row.get('status', 'active')
        }
        
        # Remove None values
        row_data = {k: v for k, v in row_data.items() if not pd.isna(v)}
        
        # Validate row data
        try:
            meter_row = MeterImportRow(**row_data)
        except Exception as e:
            raise BadRequestException(f"Validation error: {str(e)}")
        
        # Check if meter already exists by code
        existing_code = await meter_service.get_by_code(db, meter_row.code)
        if existing_code:
            raise BadRequestException(f"Meter with code '{meter_row.code}' already exists")
        
        # Check if meter already exists by number
        existing_number = await meter_service.get_by_meter_number(db, meter_row.meter_number)
        if existing_number:
            raise BadRequestException(
                f"Meter with number '{meter_row.meter_number}' already exists"
            )
        
        # Validate status
        try:
            status = MeterStatus(meter_row.status)
        except ValueError:
            raise BadRequestException(f"Invalid status: {meter_row.status}")
        
        # Create meter
        meter_create = MeterCreate(
            code=meter_row.code,
            owner_name=meter_row.owner_name,
            address=meter_row.address,
            meter_number=meter_row.meter_number,
            meter_type=meter_row.meter_type,
            previous_reading=meter_row.previous_reading,
            status=status,
            city_id=city_id
        )
        
        # Check user permission for this city
        if not user.is_admin() and user.city_id != city_id:
            raise BadRequestException("You don't have permission to import meters for this city")
        
        meter = await meter_service.create(db, meter_create)
        
        return meter
    
    def _extract_error_field(self, error_message: str) -> Optional[str]:
        """Extract field name from error message."""
        for field in self.ALL_COLUMNS:
            if field in error_message.lower():
                return field
        return None
    
    def _generate_summary_message(
        self,
        total: int,
        success: int,
        errors: int,
        skipped: int
    ) -> str:
        """Generate summary message."""
        if errors == 0 and success > 0:
            return f"✅ Successfully imported {success} meter(s)"
        elif success == 0 and errors > 0:
            return f"❌ Failed to import all {errors} meter(s)"
        elif success > 0 and errors > 0:
            return f"⚠️ Partially successful: {success} imported, {errors} failed"
        elif skipped == total:
            return "ℹ️ No valid data found in the file"
        else:
            return "ℹ️ No meters were imported"
    
    def generate_template(self) -> bytes:
        """
        Generate Excel template for meter import.
        
        Returns:
            bytes: Excel file content
        """
        # Create workbook
        wb = Workbook()
        ws = wb.active
        ws.title = "Meters"
        
        # Define styles
        header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
        header_font = Font(bold=True, color="FFFFFF", size=12)
        example_fill = PatternFill(start_color="E7E6E6", end_color="E7E6E6", fill_type="solid")
        
        # Headers
        headers = [
            'code',
            'owner_name',
            'address',
            'meter_type',  
            'meter_number',
            'previous_reading',
            'status'
        ]
        
        # Write headers
        for col_num, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col_num)
            cell.value = header
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal='center', vertical='center')
        
        # Add instructions row
        instructions = [
            'MTR-001',
            'John Doe',
            '123 Main Street, Apartment 4B',
            'Water'
            'SN-2024-001',
            '1250.5',
            'active'
        ]
        
        for col_num, value in enumerate(instructions, 1):
            cell = ws.cell(row=2, column=col_num)
            cell.value = value
            cell.fill = example_fill
            cell.alignment = Alignment(horizontal='left', vertical='center')
        
        # Add more example rows
        examples = [
            ['MTR-002', 'Jane Smith', '456 Oak Avenue', 'Electricity', 'SN-2024-002', '850.0', 'active'],
            ['MTR-003', 'Bob Johnson', '789 Pine Road, Unit 12', 'Gas', 'SN-2024-003', '', 'maintenance'],
        ]
        
        for row_num, example in enumerate(examples, 3):
            for col_num, value in enumerate(example, 1):
                cell = ws.cell(row=row_num, column=col_num)
                cell.value = value
                cell.alignment = Alignment(horizontal='left', vertical='center')
        
        # Adjust column widths
        column_widths = {
            'A': 15,  # code
            'B': 25,  # owner_name
            'C': 40,  # address
            'D': 15, 
            'E': 20,  # meter_number
            'F': 18,  # previous_reading
            'G': 15,  # status
        }
        
        for col, width in column_widths.items():
            ws.column_dimensions[col].width = width
        
        # Add notes sheet
        notes_ws = wb.create_sheet("Instructions")
        
        instructions_data = [
            ["METER IMPORT TEMPLATE - INSTRUCTIONS", ""],
            ["", ""],
            ["REQUIRED FIELDS:", ""],
            ["• code", "Unique identifier for the meter (e.g., MTR-001)"],
            ["• owner_name", "Full name of the meter owner"],
            ["• address", "Complete address where the meter is located"],
            ["• meter_number", "Serial number of the physical meter (must be unique)"],
            ["", ""],
            ["OPTIONAL FIELDS:", ""],
            ["• previous_reading", "Last recorded reading value (numeric, leave empty if none)"],
            ["• status", "Meter status: active, inactive, maintenance, or decommissioned"],
            ["", ""],
            ["IMPORTANT NOTES:", ""],
            ["• Row 1 contains headers - DO NOT MODIFY", ""],
            ["• Row 2 shows an example - you can delete it before importing", ""],
            ["• All meter codes and serial numbers must be unique", ""],
            ["• Empty rows will be skipped automatically", ""],
            ["• Maximum 1000 meters per file recommended", ""],
            ["• File must be in .xlsx format", ""],
            ["", ""],
            ["VALID STATUS VALUES:", ""],
            ["• active", "Meter is operational and in use"],
            ["• inactive", "Meter is not currently in use"],
            ["• maintenance", "Meter is under maintenance"],
            ["• decommissioned", "Meter has been permanently retired"],
            ["", ""],
            ["TIPS FOR SUCCESS:", ""],
            ["• Check for duplicate codes before importing", ""],
            ["• Ensure all addresses are complete and accurate", ""],
            ["• Previous reading values should be numeric (no commas)", ""],
            ["• Use consistent formatting throughout the file", ""],
        ]
        
        for row_num, (instruction, description) in enumerate(instructions_data, 1):
            cell_a = notes_ws.cell(row=row_num, column=1)
            cell_b = notes_ws.cell(row=row_num, column=2)
            
            cell_a.value = instruction
            cell_b.value = description
            
            if "INSTRUCTIONS" in instruction:
                cell_a.font = Font(bold=True, size=14, color="366092")
            elif instruction.endswith(":"):
                cell_a.font = Font(bold=True, size=11)
            elif instruction.startswith("•"):
                cell_a.font = Font(bold=True)
        
        notes_ws.column_dimensions['A'].width = 30
        notes_ws.column_dimensions['B'].width = 60
        
        # Save to bytes
        excel_file = io.BytesIO()
        wb.save(excel_file)
        excel_file.seek(0)
        
        return excel_file.getvalue()
    
    async def validate_file_before_import(
        self,
        file: BinaryIO
    ) -> dict:
        """
            Validate Excel file before actual import.
            Returns:
                dict: Validation results with preview of data
        """
        try:
            df = pd.read_excel(file, engine='openpyxl')
        except Exception as e:
            raise BadRequestException(f"Failed to read Excel file: {str(e)}")
        
        # Validate columns
        df_columns = [col.lower().strip() for col in df.columns]
        missing_columns = [
            col for col in self.REQUIRED_COLUMNS
            if col not in df_columns
        ]
        
        if missing_columns:
            return {
                "valid": False,
                "error": f"Missing required columns: {', '.join(missing_columns)}",
                "required_columns": self.REQUIRED_COLUMNS,
                "found_columns": list(df.columns)
            }
        
        # Clean data
        df = self._clean_dataframe(df)
        
        # Count rows
        total_rows = len(df)
        non_empty_rows = len(df.dropna(how='all'))
        
        # Preview first few rows
        preview_data = []
        for idx, row in df.head(5).iterrows():
            preview_data.append({
                col: (str(row[col]) if not pd.isna(row[col]) else None)
                for col in df.columns
            })
        
        return {
            "valid": True,
            "total_rows": total_rows,
            "non_empty_rows": non_empty_rows,
            "columns": list(df.columns),
            "preview": preview_data,
            "message": f"File is valid. Ready to import {non_empty_rows} meter(s)."
        }


meter_import_service = MeterImportService()