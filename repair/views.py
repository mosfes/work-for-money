from django.shortcuts import render,redirect
from django.http import HttpResponse
from repair.models import Report,Number
from django.core.files.storage import FileSystemStorage
from django.utils import timezone
import locale
from datetime import datetime

THAI_MONTHS = [
    "", "มกราคม", "กุมภาพันธ์", "มีนาคม", "เมษายน", "พฤษภาคม", "มิถุนายน",
    "กรกฎาคม", "สิงหาคม", "กันยายน", "ตุลาคม", "พฤศจิกายน", "ธันวาคม"
]


# Create your views here.
def index(request):
    return render(request,"index.html")

def report(request):
    all2 = Report.objects.all()

    for item in all2:
        dt = timezone.localtime(item.data)
        day = dt.day
        month = dt.month
        year = dt.year + 543
        time = dt.strftime("%H:%M")

        # แยกเป็น date กับ time
        item.formatted_date = f"{day} {THAI_MONTHS[month]} {year}"
        item.formatted_time = f"{time} น."

    return render(request, "report.html", {"all2": all2})

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

