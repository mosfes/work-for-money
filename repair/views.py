from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from .models import Report,Number
from django.utils import timezone

THAI_MONTHS = [
    "", "มกราคม", "กุมภาพันธ์", "มีนาคม", "เมษายน", "พฤษภาคม", "มิถุนายน",
    "กรกฎาคม", "สิงหาคม", "กันยายน", "ตุลาคม", "พฤศจิกายน", "ธันวาคม"
]


# Create your views here.
def index(request):
    return render(request,"index.html")

def report(request):
    all_reports = Report.objects.all().order_by('-data')

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
        'all2': all_reports,
        'total_count': total_count,
        'pending_count': pending_count,
        'completed_count': completed_count,
    }


    return render(request, "report.html", context)

def report_form(request):
    if request.method == 'POST':
        building = request.POST.get('building')
        floor = request.POST.get('floor')
        agency = request.POST.get('department')
        tel = request.POST.get('contact')
        report_text = request.POST.get('repair_items')
        image_file = request.FILES.get('image')

        # ดึงค่าเลขจาก Number แล้ว +1
        number_obj, created = Number.objects.get_or_create(pk=1, defaults={'number': 0})
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

    return render(request, 'index.html')

def update_repair_from_modal(request):
    # View นี้จะทำงานเมื่อฟอร์มใน Modal ถูก submit เท่านั้น
    if request.method == 'POST':
        # 1. ดึงข้อมูลจากฟอร์มที่ส่งมา
        report_id = request.POST.get('report_id')
        status_result = request.POST.get('status') # จาก <input name="status"> (value: 'done' หรือ 'notdone')
        details = request.POST.get('details', '')
        equipment = request.POST.get('equipment', '') # ใส่ค่า default เป็นสตริงว่าง ถ้าไม่มีการส่งมา
        type_value = request.POST.get('type', '')

        # ตรวจสอบว่าได้รับ report_id มาหรือไม่
        if not report_id:
            # จัดการกรณีที่ไม่มี ID ส่งมา (อาจจะ redirect หรือแสดง error)
            print("Error: Report ID is missing!")
            return redirect('report') # กลับไปหน้าแรก

        try:
            # 2. ค้นหางานซ่อมจาก ID ที่ได้รับมา
            report_item = get_object_or_404(Report, id=report_id)

            # 3. อัปเดตข้อมูลใน object นั้นๆ ตาม Model ของคุณ
            report_item.details = details
            report_item.equipment = equipment

            report_item.status = status_result

            # อัปเดต task_status
            # if status_result == 'done':
            #     report_item.status = "1"  # 1 = เสร็จสิ้น
            # elif status_result == 'notdone':
            #     report_item.task_status = "0"  # 2 = ไม่สามารถทำได้

            report_item.task_status = "1"
            report_item.type = type_value

            # 4. บันทึกการเปลี่ยนแปลงลงฐานข้อมูล
            report_item.save()

            # 5. เมื่อเสร็จแล้ว ให้ redirect กลับไปที่หน้ารายการ
            return redirect('report')

        except Report.DoesNotExist:
            print(f"Error: Report with ID {report_id} not found.")
            return redirect('report')
        except Exception as e:
            print(f"An error occurred: {e}")
            return redirect('report')

    # ถ้ามีคนพยายามเข้า URL นี้โดยตรง (ไม่ใช่ POST) ให้ส่งกลับไปหน้าแรก
    return redirect('report')