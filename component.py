from flask import request,abort
import datetime
from .models.evaluate_system import Evaluate_Type


PAGE_SHELF = 10
DATE_FORMAT = '%m-%d-%Y'
WILL_EXPIRE_DAY = 7
RATE = 5

def pagination(request,selection,role = 'nah'):

    page = request.args.get('page', 1, type=int)
    start = (page - 1) * PAGE_SHELF
    end = start + PAGE_SHELF
    content = None
    #
    if role == 'nah':
        content = [s.format() for s in selection]
    else:
        content = [s.format(role) for s in selection]

    current_content = content[start:end]

    #page_number = math.ceil(content / PAGE_SHELF)
        
    return current_content, page

def getRoleAR(role):
    if role == 'Educational_Supervisor':
        return 'مشرف تربوي'
    elif role == 'Laboratory_Manager':
        return 'محضر مختبر'
    elif role == 'Science_Teacher':
        return 'معلم علوم'
    elif role == 'School_Manager':
        return 'قائد المدرسة'
    elif role == 'System_Administrator':
        return 'مدير النظام'
    elif role == 'Support':
        return 'الدعم الفني'
    else:
        return ''

def check_date_format(date):
    #Format Month/Day/Year = 1/30/2021 
    try:
        return datetime.datetime.strptime(date, DATE_FORMAT)
    except ValueError:
        abort(400, 'الرجاء كتابة التاريخ بالصيغة الصحيحة')

def getReasonAR(reason):

    if reason == 'broke':
        return 'كسر'
    elif reason == 'tainted':
        return 'تالف'
    elif reason == 'expired':
        return 'انتهاء صلاحية'
    elif reason == 'lost':
        return 'فقد'
    elif reason == 'used':
        return 'مستهلك'
    else:
        return ''

def initiate_evaluate_type(db):
    try:
        type_1 = Evaluate_Type(id=1,title='evaluate_experiment')
        type_2 = Evaluate_Type(id=2,title='evaluate_laboratory')
        type_3 = Evaluate_Type(id=3,title='evaluate_laboratory_manager')
        db.session.add(type_1)
        db.session.add(type_2)
        db.session.add(type_3)
        db.session.commit()
    except:
        db.session.rollback()

def getEvaluateTypeAR(type):    
    switcher={
            1:'تقييم التجربة',
            2:'تقييم المختبر',
            3:'تقييم محضر المختبر'
            }
    return switcher.get(int(type))

def get_class_number(time):
    #get only the hour right now 
    now = time.strftime('%H')
    #check the time if greater or equal to 7 else will return 0 (mean yesterday or past)
    if int(now) >= 7:
        switcher={
                7:1,
                8:2,
                9:3,
                10:4,
                11:5,
                12:6,
                13:7
                }
    else:
        return 0
    return switcher.get(int(now),8)

'''   
def get_class_number(time):
    #get only the hour right now 
    hour = time.strftime('%H')
    minute = time.strftime('%M')

    now = int(hour) + convert_min(int(minute))
    #check the time in which class number 
    if 7 <= now and now <= 8.24:
        return 1
    elif 8.25 <= now and now <= 9.49:
        return 2
    elif 9.5 <= now and now <= 10.74:
        return 3
    elif 10.75 <= now and now <= 11.59:
        return 4
    elif 12 <= now and now <= 13.24:
        return 5
    elif 13.25 <= now and now <= 14.49:
        return 6  
    elif 14.5 <= now and now <= 15.74:
        return 7
    elif 15.75 <= now:
        return 8
    else:
        return 0

def convert_min(minute):
    #convert the min to fraction number
    if 0 <= minute and minute <= 14:
        return 0.0
    elif 15 <= minute and minute <= 29:
        return 0.25
    elif 30 <= minute and minute <= 44:
        return 0.5
    elif 45 <= minute and minute <= 59:
        return 0.75 
'''