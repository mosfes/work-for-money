import os
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from datetime import timedelta

from googleapiclient.discovery import build
from google.oauth2 import service_account
from django.template.loader import render_to_string
from weasyprint import HTML
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.template import Template, Context
from weasyprint import HTML
import re

from googleapiclient.discovery import build
from google.oauth2 import service_account


from service import settings
from .models import Report, Number
from django.utils import timezone
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from .models import Report
import io
from django.urls import path
from . import views


THAI_MONTHS = [
    "",
    "มกราคม",
    "กุมภาพันธ์",
    "มีนาคม",
    "เมษายน",
    "พฤษภาคม",
    "มิถุนายน",
    "กรกฎาคม",
    "สิงหาคม",
    "กันยายน",
    "ตุลาคม",
    "พฤศจิกายน",
    "ธันวาคม",
]


# Create your views here.
def index(request):
    return render(request, "index.html")


def delete_old_completed_reports():
    # ทำเครื่องหมายว่า ให้งานที่ task_status = "1" และ status = "1" (หรือเทียบเท่าใน model ของคุณ)
    # และวันที่ data เกิน 30 วัน ลบออก
    threshold_date = timezone.now() - timedelta(days=30)
    # ถ้าฟิลด์วันที่ชื่อ data
    Report.objects.filter(
        task_status="1", status="1", data__lte=threshold_date
    ).delete()


def report(request):
    delete_old_completed_reports()
    all_reports = Report.objects.all().order_by("-data")

    total_count = all_reports.count()
    pending_count = all_reports.filter(task_status=0).count()
    completed_count = all_reports.filter(task_status=1).count()

    for item in all_reports:
        dt = timezone.localtime(item.data)
        day = dt.day
        month = dt.month
        year = dt.year + 543
        time = dt.strftime("%H:%M")

        item.formatted_date = f"{day} {THAI_MONTHS[month]} {year}"
        item.formatted_time = f"{time} น."

    context = {
        "all2": all_reports,
        "total_count": total_count,
        "pending_count": pending_count,
        "completed_count": completed_count,
    }

    return render(request, "report.html", context)


def report_form(request):
    if request.method == "POST":
        building = request.POST.get("building")
        floor = request.POST.get("floor")
        agency = request.POST.get("department")
        tel = request.POST.get("contact")
        report_text = request.POST.get("repair_items")
        image_file = request.FILES.get("image")

        # ดึงค่าเลขจาก Number แล้ว +1
        number_obj, created = Number.objects.get_or_create(pk=1, defaults={"number": 0})
        new_number = number_obj.number + 1

        # บันทึก Report
        report = Report.objects.create(
            building=building,
            floor=floor,
            agency=agency,
            tel=tel,
            report=report_text,
            image=image_file,
            number=new_number,
        )

        # อัปเดตเลขใน Number
        number_obj.number = new_number
        number_obj.save()

        # return redirect('success')

    return render(request, "index.html")


def update_repair_from_modal(request):
    # View นี้จะทำงานเมื่อฟอร์มใน Modal ถูก submit เท่านั้น
    if request.method == "POST":
        # 1. ดึงข้อมูลจากฟอร์มที่ส่งมา
        report_id = request.POST.get("report_id")
        status_result = request.POST.get(
            "status"
        )  # จาก <input name="status"> (value: 'done' หรือ 'notdone')
        details = request.POST.get("details", "")
        equipment = request.POST.get(
            "equipment", ""
        )  # ใส่ค่า default เป็นสตริงว่าง ถ้าไม่มีการส่งมา
        type_value = request.POST.get("type", "")

        # ตรวจสอบว่าได้รับ report_id มาหรือไม่
        if not report_id:
            # จัดการกรณีที่ไม่มี ID ส่งมา (อาจจะ redirect หรือแสดง error)
            print("Error: Report ID is missing!")
            return redirect("report")  # กลับไปหน้าแรก

        try:
            # 2. ค้นหางานซ่อมจาก ID ที่ได้รับมา
            report_item = get_object_or_404(Report, id=report_id)

            # 3. อัปเดตข้อมูลใน object นั้นๆ ตาม Model ของคุณ
            report_item.details = details
            report_item.equipment = equipment

            report_item.status = status_result

            report_item.task_status = "1"
            report_item.type = type_value

            # 4. บันทึกการเปลี่ยนแปลงลงฐานข้อมูล
            report_item.save()

            # 5. เมื่อเสร็จแล้ว ให้ redirect กลับไปที่หน้ารายการ
            return redirect("report")

        except Report.DoesNotExist:
            print(f"Error: Report with ID {report_id} not found.")
            return redirect("report")
        except Exception as e:
            print(f"An error occurred: {e}")
            return redirect("report")

    # ถ้ามีคนพยายามเข้า URL นี้โดยตรง (ไม่ใช่ POST) ให้ส่งกลับไปหน้าแรก
    return redirect("report")


font_path = os.path.join(settings.BASE_DIR, "repair/static", "fonts", "THSarabun.ttf")

pdfmetrics.registerFont(TTFont("THSarabun", font_path))


def download_pdf(request, report_id):
    report = get_object_or_404(Report, pk=report_id)

    # ✅ 1) ดึง Google Docs
    SCOPES = ["https://www.googleapis.com/auth/documents.readonly"]
    DOCUMENT_ID = "1__zRCEMZpxr-WXTBNIsqn1xx2Rpms-NaNNhhU3E9q9Q"
    creds = service_account.Credentials.from_service_account_file(
        "credentials.json", scopes=SCOPES
    )
    service = build("docs", "v1", credentials=creds)
    doc = service.documents().get(documentId=DOCUMENT_ID).execute()

    # ✅ 2) เตรียมข้อมูลสำหรับแทนที่
    dt = timezone.localtime(report.data)
    day = dt.day
    month = dt.month
    year = dt.year + 543
    time_str = dt.strftime("%H:%M")
    formatted_date = f"{day} {THAI_MONTHS[month]} {year}"
    formatted_time = f"{time_str} "

    # สร้าง mapping สำหรับแทนที่
    replacements = {
        "{{number}}": str(report.id),
        "((number))": str(report.id),
        "{number}": str(report.id),
        "{{date}}": formatted_date,
        "((date))": formatted_date,
        "{date}": formatted_date,
        "{{time}}": formatted_time,
        "((time))": formatted_time,
        "{time}": formatted_time,
        "{{building}}": report.building or "",
        "((building))": report.building or "",
        "{building}": report.building or "",
        "{{floor}}": report.floor or "",
        "((floor))": report.floor or "",
        "{floor}": report.floor or "",
        "{{agency}}": report.agency or "",
        "((agency))": report.agency or "",
        "{agency}": report.agency or "",
        "{{tel}}": report.tel or "",
        "((tel))": report.tel or "",
        "{tel}": report.tel or "",
        "{{report}}": report.report or "",
        "((report))": report.report or "",
        "{report}": report.report or "",
        "{{details}}": report.details or "",
        "((details))": report.details or "",
        "{details}": report.details or "",
        "{{equipment}}": report.equipment or "",
        "((equipment))": report.equipment or "",
        "{equipment}": report.equipment or "",
    }

    # ✅ 3) แปลง Google Docs เป็น HTML โดยรักษาโครงสร้าง
    def parse_docs_to_html(content):
        html_parts = []

        for element in content:
            if "paragraph" in element:
                paragraph = element["paragraph"]
                style = paragraph.get("paragraphStyle", {})

                # ตรวจสอบการจัดตำแหน่ง
                alignment = style.get("alignment", "START")
                indent = style.get("indentStart", {}).get("magnitude", 0)

                # กำหนด CSS class
                css_class = ""
                if alignment == "CENTER":
                    css_class = "text-center"
                elif alignment == "END":
                    css_class = "text-right"

                # เริ่ม paragraph
                if css_class:
                    html_parts.append(f'<p class="{css_class}">')
                else:
                    html_parts.append("<p>")

                # ดึงข้อความ
                if "elements" in paragraph:
                    for run in paragraph["elements"]:
                        if "textRun" in run:
                            text = run["textRun"]["content"]
                            text_style = run["textRun"].get("textStyle", {})

                            # ใส่การจัดรูปแบบ
                            if text_style.get("bold"):
                                text = f"<strong>{text}</strong>"
                            if text_style.get("italic"):
                                text = f"<em>{text}</em>"
                            if text_style.get("underline"):
                                text = f"<u>{text}</u>"

                            # แทนที่ placeholder
                            for old, new in replacements.items():
                                text = text.replace(old, new)

                            html_parts.append(text)

                html_parts.append("</p>")

            elif "table" in element:
                table = element["table"]
                html_parts.append('<table class="form-table">')

                for row_index, row in enumerate(table["tableRows"]):
                    html_parts.append("<tr>")

                    for cell_index, cell in row["tableCells"]:
                        # กำหนด colspan ถ้ามี
                        colspan = cell.get("tableCellStyle", {}).get("columnSpan", 1)
                        if colspan > 1:
                            html_parts.append(f'<td colspan="{colspan}">')
                        else:
                            html_parts.append("<td>")

                        # ดึงเนื้อหาในเซลล์
                        for cell_element in cell["content"]:
                            if "paragraph" in cell_element:
                                para = cell_element["paragraph"]
                                if "elements" in para:
                                    for run in para["elements"]:
                                        if "textRun" in run:
                                            cell_text = run["textRun"]["content"]

                                            # แทนที่ placeholder ในตาราง
                                            for old, new in replacements.items():
                                                cell_text = cell_text.replace(old, new)

                                            html_parts.append(cell_text)

                        html_parts.append("</td>")

                    html_parts.append("</tr>")

                html_parts.append("</table>")

        return "".join(html_parts)

    # แปลงเนื้อหา
    doc_html = parse_docs_to_html(doc["body"]["content"])

    # ✅ 4) สร้าง HTML พร้อม CSS ที่จำลองรูปแบบ Google Docs
    # ✅ 4) สร้าง HTML พร้อม CSS ที่จำลองรูปแบบ Google Docs
    html_string = f"""
    <!DOCTYPE html>
    <html lang="th">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>รายงาน {report.id}</title>
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Sarabun:wght@300;400;500;600;700&display=swap');
        
            * {{
                box-sizing: border-box;
                margin: 0;
                padding: 0;
            }}
        
            body {{
                font-family: 'Sarabun', 'TH SarabunPSK', Arial, sans-serif;
                font-size: 14px;
                line-height: 1.6;
                color: #000;
                background: white;
                padding: 40px 60px;
                max-width: 210mm;
                margin: 0 auto;
            }}
        
            p {{
                margin: 8px 0;
                text-align: left;
                text-indent: 0;
            }}
            .text-center {{
                text-align: center !important;
            }}
        
            .text-right {{
                text-align: right !important;
            }}
        
            strong {{
                font-weight: 600;
            }}
        
            .form-table {{
                width: 100%;
                border-collapse: collapse;
                margin: 15px 0;
                font-size: 14px;
            }}

            .form-table td {{
                border: 1px solid #000;
                padding: 8px 10px;
                vertical-align: top;
                text-align: left;
                line-height: 1.4;
            }}


        .form-table td.center {{
            text-align: center;
        }}
        
        /* จำลองเส้นประสำหรับลายเซ็น */
        .dotted-line {{
            border-bottom: 1px dotted #333;
            display: inline-block;
            min-width: 200px;
            margin: 0 5px;
            height: 20px;
            vertical-align: bottom;
        }}
        
        /* จำลองช่องกรอกข้อมูล */
        .form-field {{
            border-bottom: 1px solid #000;
            display: inline-block;
            min-width: 150px;
            margin: 0 3px;
            padding: 2px 5px;
            vertical-align: bottom;
        }}
        
        /* Checkbox styling */
        .checkbox {{
            display: inline-block;
            width: 15px;
            height: 15px;
            border: 1px solid #000;
            margin: 0 5px;
            vertical-align: middle;
            position: relative;
        }}
        
        /* หัวเรื่องหลัก */
        .header {{
            text-align: center;
            font-weight: bold;
            margin: 15px 0;
            font-size: 16px;
            line-height: 1.4;
        }}
        
        .sub-header {{
            text-align: center;
            margin: 8px 0;
            font-size: 14px;
        }}
        
        /* ส่วนลายเซ็น - จัดให้อยู่ขวา */
        .signature-section {{
            margin-top: 40px;
            padding-top: 20px;
            text-align: right;
        }}
        
        .signature-row {{
            margin: 15px 0;
            text-align: right;
        }}
        
        .signature-field {{
            border-bottom: 1px dotted #333;
            display: inline-block;
            min-width: 200px;
            margin: 0 10px;
            padding: 2px;
            text-align: center;
        }}
        
        .date-field {{
            border-bottom: 1px dotted #333;
            display: inline-block;
            min-width: 120px;
            text-align: center;
            margin: 0 5px;
            padding: 2px;
        }}
        
        /* จัดตำแหน่งลายเซ็นผู้รับแจ้งให้ชิดขวาเท่ากับวันเวลา */
        .signature-right {{
            text-align: right !important;
            margin: 10px 0;
        }}
        
        /* สำหรับส่วนของแบบฟอร์ม */
        .form-section {{
            margin: 20px 0;
            padding: 10px 0;
        }}
        
        .form-title {{
            text-align: center;
            font-weight: bold;
            font-size: 16px;
            margin: 20px 0;
            text-decoration: underline;
        }}
        
        /* จัดรูปแบบข้อความในวงเล็บ */
        .parenthesis {{
            margin: 5px 0;
            text-align: center;
        }}
        
        /* สำหรับส่วนรายละเอียด */
        .details-section {{
            margin: 15px 0;
            line-height: 1.8;
        }}
        
        /* สำหรับหัวข้อย่อย */
        .section-title {{
            font-weight: bold;
            margin: 15px 0 10px 0;
            text-align: center;
            text-decoration: underline;
        }}
        
        @media print {{
            body {{
                padding: 20px 30px;
                font-size: 12px;
            }}
            
            .form-table {{
                font-size: 12px;
            }}
            
            .header {{
                font-size: 14px;
            }}
        }}
        </style>
    </head>
    <body>
        {doc_html}
    </body>
    </html>
    """

    # ✅ 5) แปลงเป็น PDF
    from weasyprint import HTML, CSS

    pdf_file = HTML(string=html_string).write_pdf(
        stylesheets=[
            CSS(
                string="""
            @page {
                size: A4;
                margin: 2cm;
            }
        """
            )
        ]
    )

    response = HttpResponse(pdf_file, content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="report_{report.id}.pdf"'

    return response


def replace_placeholders(text, data):
    # แทนที่ทุกรูปแบบ placeholder
    patterns = [
        r"\{\{\s*(\w+)\s*\}\}",  # {{field}}
        r"\(\(\s*(\w+)\s*\)\)",  # ((field))
        r"\{\s*(\w+)\s*\}",  # {field}
        r"\[\s*(\w+)\s*\]",  # [field]
    ]

    for pattern in patterns:
        text = re.sub(pattern, lambda m: str(data.get(m.group(1), m.group(0))), text)

    return text


# วิธีที่ง่ายที่สุด - Export เป็น HTML โดยตรง
def get_docs_as_html():
    service = build("drive", "v3", credentials=creds)
    request = service.files().export_media(fileId=DOCUMENT_ID, mimeType="text/html")
    html_content = request.execute().decode("utf-8")

    # แทนที่ placeholder
    for old, new in replacements.items():
        html_content = html_content.replace(old, new)

    return html_content


from django.http import JsonResponse
from django.db.models import Count
from .models import Report  # ถ้ายังไม่ได้ import


def report_type_counts_api(request):
    qs = (
        Report.objects.values("type")
        .exclude(type="")  # ไม่เอาข้อมูลว่าง
        .annotate(count=Count("id"))
        .order_by("type")
    )
    data = [{"type": r["type"], "count": r["count"]} for r in qs]
    return JsonResponse(data, safe=False)
