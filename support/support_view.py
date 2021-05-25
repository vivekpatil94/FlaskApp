from flask import Blueprint,jsonify,request,abort
from app.models.support import Defect_Report
from app.models.users import User
from app.authentication import require_auth 
from app.public_route import send_notification_support,send_inform_user

support_route = Blueprint('support_route',__name__)

########## SUPPORT ##########

@support_route.route('/defect-report', methods=['POST'])
@require_auth(['School_Manager','Laboratory_Manager','Educational_Supervisor','Science_Teacher','System_Administrator'])
def create_new_report(payload):

    report_data = request.get_json()

    user = User.query.filter_by(id=payload['sub']).first_or_404('حدث خطأ, يرجى المحاولة لاحقاً')

    #create new report for defect
    report = user.create_report(report_data,user.id)
    report_id = report.id
    #send notification to service
    send_notification_support(report_id)
    send_inform_user(report.id,user.full_name(),user.email)

    user.close_session()
    
    return jsonify({
        'success': True,
        'message': 'تم رفع الشكوى بنجاح',
        'defectReportId': report_id
    })

'''
{
    "defectReportId": 7,
    "message": "تم رفع الشكوى بنجاح",
    "success": true
}
'''

@support_route.route('/defect-report', methods=['PATCH'])
@require_auth(['Support'])
def modify_report(payload):

    report_data = request.get_json()

    user = User.query.filter_by(id=payload['sub']).first_or_404('حدث خطأ, يرجى المحاولة لاحقاً')
    #change the status of report: not solved --> solved and solved --> not solved
    report = user.defect_solved(report_data,user.id)

    content = report.format()
    user.close_session()

    return jsonify({
        'success': True,
        'report': content
    })

'''
{
    "report": {
        "email": "aa@hotmail.com",
        "id": 2,
        "phone": "0557797377",
        "status": true,
        "text": "ماتظهر جميع الطلبات",
        "title": "الوجهات",
        "userId": 44
    },
    "success": true
}
'''

@support_route.route('/defect-report/<int:report_id>', methods=['GET'])
@require_auth(['Support'])
def get_specific_report(payload,report_id):

    #get specific report
    reports = Defect_Report.query.filter_by(id=report_id).first_or_404('لا يوجد تقرير عن خلل بهذا الرقم')
    content = reports.format()

    return jsonify({
        'success': True,
        'report': content
    })

'''
{
    "report": {
        "email": "aa@hotmail.com",
        "id": 5,
        "phone": "0557797377",
        "status": false,
        "text": "اغلب الطلبات تأتي بدون شرح",
        "title": "لا يوجد نص",
        "userId": 44
    },
    "success": true
}
'''

@support_route.route('/defect-report', methods=['GET'])
@require_auth(['Support'])
def get_all_reports(payload):

    #get all reports
    reports = Defect_Report.query.all()
    content = [r.format() for r in reports] 

    return jsonify({
        'success': True,
        'reports': content
    })

'''
{
    "reports": [
        {
            "email": "aa@hotmail.com",
            "id": 1,
            "phone": "0557797377",
            "status": true,
            "text": "ماتظهر جميع الطلبات",
            "title": "الوجهات",
            "userId": 44
        },
        {
            "email": "aa@hotmail.com",
            "id": 3,
            "phone": "0557797377",
            "status": false,
            "text": "اغلب الطلبات تأتي بدون شرح",
            "title": "لا يوجد نص",
            "userId": 44
        },
        {
            "email": "aa@hotmail.com",
            "id": 4,
            "phone": "0557797377",
            "status": false,
            "text": "اغلب الطلبات تأتي بدون شرح",
            "title": "لا يوجد نص",
            "userId": 44
        },
        {
            "email": "aa@hotmail.com",
            "id": 5,
            "phone": "0557797377",
            "status": false,
            "text": "اغلب الطلبات تأتي بدون شرح",
            "title": "لا يوجد نص",
            "userId": 44
        },
        {
            "email": "aa@hotmail.com",
            "id": 2,
            "phone": "0557797377",
            "status": false,
            "text": "ماتظهر جميع الطلبات",
            "title": "الوجهات",
            "userId": 44
        }
    ],
    "success": true
}
'''