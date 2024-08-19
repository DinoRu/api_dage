from io import BytesIO

from openpyxl.workbook import Workbook

from app.models.meter import Meter
from app.utils.excel.draw_excel_file import draw_report_header


def get_file_from_database(meters: list[Meter]) -> BytesIO:
    workbook = Workbook()
    worksheet = workbook.active
    draw_report_header(worksheet)
    for meter in meters:
        worksheet.append(
            (
                meter.code, meter.address, meter.owner_name, None,
                meter.meter_number, meter.previous_reading, meter.current_reading,
                meter.completion_date, meter.latitude, meter.longitude,
                meter.photo1_url, meter.photo2_url, meter.supervisor, meter.comment
            )
        )
    buffer = BytesIO()
    workbook.save(buffer)
    return buffer
