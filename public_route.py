from . import app
from .models.users import User, System_Administrator,School_Manager,School_Member,Science_Teacher,Laboratory_Manager,Educational_Supervisor
from .models.support import Valid_Token
from .models.resources import School
from .models.transactions import Invitation
from .models.evaluate_system import Evaluate
from flask import jsonify, Blueprint, request, abort
from werkzeug.security import generate_password_hash, check_password_hash
import re 
from .authentication import initiate_token,require_auth,initiate_reset_password_token,decode_auth_token
from cryptography.fernet import Fernet
from sqlalchemy import and_, or_
import smtplib 
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

public_route = Blueprint('public_route',__name__)

regex_email = '^\w+([\.-]?\w+)*@\w+([\.-]?\w+)*(\.\w{2,3})+$'
regex_phone = '^(009665|9665|\+9665|05|5)(5|0|3|6|4|9|1|8|7)(\d{7})$'
roles = ['Educational_Supervisor','Laboratory_Manager','Science_Teacher','School_Manager','System_Administrator']

def template_email_password(name,link):

    return """\
        <!DOCTYPE html>
        <html lang="ar" style="font-size:62.5%;">
        <head>
            <meta charset="UTF-8">
            <meta http-equiv="X-UA-Compatible" content="IE=edge">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <link rel="preconnect" href="https://fonts.gstatic.com">
            <link href="https://fonts.googleapis.com/css2?family=Almarai:wght@400;700&display=swap" rel="stylesheet">
            <title>مختبراتي</title>
            
        </head>
        <body style="-webkit-box-sizing:border-box;box-sizing:border-box;margin:0;padding:0;font-family:'Almarai', sans-serif;background-color:#f8f8f8 !important;">
            <div class="template-container" style="-webkit-box-sizing:border-box;box-sizing:border-box;margin:0;padding:0;width:100%;max-width:55rem;margin:0 auto;margin-top:2rem;padding:0 1rem;padding-bottom:1.5rem;-webkit-box-shadow:0 3px 6px rgba(0, 0, 0, .16);box-shadow:0 3px 6px rgba(0, 0, 0, .16);border-radius:3px;color:#555;font-family:'Almarai', sans-serif;background-color:white !important;">
            <header class="header" style="-webkit-box-sizing:border-box;box-sizing:border-box;margin:0;padding:0;">
                <div class="header__icon-logo" style="-webkit-box-sizing:border-box;box-sizing:border-box;margin:0;padding:0;text-align:center;padding:3rem 0;background-color:white;border-bottom:1rem solid #0FA591;">
                <img src="https://i.ibb.co/C0nj3g9/icon-logo.png" alt="مختبراتي" style="-webkit-box-sizing:border-box;box-sizing:border-box;margin:0;padding:0;width:80%;max-width:25rem;">
                </div>
            </header>
            <main class="content" style="-webkit-box-sizing:border-box;box-sizing:border-box;margin:0;padding:0;color:#555 !important;font-family:'Almarai', sans-serif !important;">
                <div class="content__image" style="-webkit-box-sizing:border-box;box-sizing:border-box;margin:0;padding:0;margin-top:4rem;text-align:center;">
                <img src="https://i.ibb.co/C2r0fmJ/forget-password.png" alt="forget-password" style="-webkit-box-sizing:border-box;box-sizing:border-box;margin:0;padding:0;width:80%;min-width:20rem;">
                </div>
                <div class="content__text" style="-webkit-box-sizing:border-box;box-sizing:border-box;margin:0;padding:0;color:#555;text-align:center;color:#555 !important;font-family:'Almarai', sans-serif !important;">
                <h2 class="content__text--title" style="-webkit-box-sizing:border-box;box-sizing:border-box;margin:0;padding:0;margin-bottom:1rem;font-size:2.3rem !important;color:#555 !important;font-family:'Almarai', sans-serif !important;">
                    نسيت كلمة المرور الخاصة بك؟
                            </h2>
                <p class="content__text--welcoming" style="-webkit-box-sizing:border-box;box-sizing:border-box;margin:0;padding:0;margin-bottom:2rem;line-height:2.5rem;font-size:1.6rem !important;color:#555 !important;font-family:'Almarai', sans-serif !important;">
                    أهلا {}
                                <br style="-webkit-box-sizing:border-box;box-sizing:border-box;margin:0;padding:0;">
                    !تم انشاء طلب لاعادة ضبط كلمة المرور من جديد
                            </p>
                <p class="content__text--reset-btn" style="-webkit-box-sizing:border-box;box-sizing:border-box;margin:0;padding:0;margin-top:2.5rem;margin-bottom:2.5rem;font-size:1.6rem !important;">
                    <a href={} style="-webkit-box-sizing:border-box;box-sizing:border-box;margin:0;padding:0;display:inline-block;text-decoration:none;padding:1rem 1.5rem;border-radius:5px;-webkit-transition:all .2s;-o-transition:all .2s;transition:all .2s;-webkit-box-shadow:0 3px 6px rgba(0, 0, 0, .16);box-shadow:0 3px 6px rgba(0, 0, 0, .16);color:white !important;background-color:#0FA591 !important;"> اعادة ضبط كلمة المرور</a>
                </p>
                <p class="content__text--warning" style="-webkit-box-sizing:border-box;box-sizing:border-box;margin:0;padding:0;font-size:1.6rem;line-height:2.5rem;margin-bottom:3rem;color:#555 !important;font-family:'Almarai', sans-serif !important;">
                    اذا لم تقم بانشاء الطلب, أو استطعت تذكر كلمة المرور الخاصة بك
                                <br style="-webkit-box-sizing:border-box;box-sizing:border-box;margin:0;padding:0;">
                    فقط قم بتجاهل هذة الرسالة
                            </p>
                </div>
            </main>
            <footer class="footer" style="-webkit-box-sizing:border-box;box-sizing:border-box;margin:0;padding:0;border-top:1rem solid #0FA591;">
                <div class="footer__direction-message" style="-webkit-box-sizing:border-box;box-sizing:border-box;margin:0;padding:0;width:100%;">
                </div>
                <div class="footer__nav" style="-webkit-box-sizing:border-box;box-sizing:border-box;margin:0;padding:0;width:100%;margin-top:1rem;">
                <ul class="nav" style="-webkit-box-sizing:border-box;box-sizing:border-box;margin:0;padding:0;list-style:none;text-align:center;">
                    <li class="nav-item" style="-webkit-box-sizing:border-box;box-sizing:border-box;margin:0;padding:0;font-size:1.6rem;color:#0FA591 !important;"><a href="http://localhost:3000/login" style="-webkit-box-sizing:border-box;box-sizing:border-box;margin:0;padding:0;text-decoration:none;color:#0FA591 !important;">تسجيل الدخول</a></li>
                </ul>
                </div>
            </footer>
            </div>
        </body>
        </html>""".format(name,link)

def template_email_service(report_id,link):

    return """\
        <!DOCTYPE html>
        <html lang="ar" style="font-size:62.5%;">
        <head>
            <meta charset="UTF-8">
            <meta http-equiv="X-UA-Compatible" content="IE=edge">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <link rel="preconnect" href="https://fonts.gstatic.com">
            <link href="https://fonts.googleapis.com/css2?family=Almarai:wght@400;700&display=swap" rel="stylesheet">
            <title>مختبراتي</title>
            
        </head>
        <body style="-webkit-box-sizing:border-box;box-sizing:border-box;margin:0;padding:0;font-family:'Almarai', sans-serif;background-color:#f8f8f8 !important;">
            <div class="template-container" style="-webkit-box-sizing:border-box;box-sizing:border-box;margin:0;padding:0;width:100%;max-width:55rem;margin:0 auto;margin-top:2rem;padding:0 1rem;padding-bottom:1.5rem;-webkit-box-shadow:0 3px 6px rgba(0, 0, 0, .16);box-shadow:0 3px 6px rgba(0, 0, 0, .16);border-radius:3px;color:#555;font-family:'Almarai', sans-serif;background-color:white !important;">
            <header class="header" style="-webkit-box-sizing:border-box;box-sizing:border-box;margin:0;padding:0;">
                <div class="header__icon-logo" style="-webkit-box-sizing:border-box;box-sizing:border-box;margin:0;padding:0;text-align:center;padding:3rem 0;background-color:white;border-bottom:1rem solid #0FA591;">
                <img src="https://i.ibb.co/C0nj3g9/icon-logo.png" alt="مختبراتي" style="-webkit-box-sizing:border-box;box-sizing:border-box;margin:0;padding:0;width:80%;max-width:25rem;">
                </div>
            </header>
            <main class="content" style="-webkit-box-sizing:border-box;box-sizing:border-box;margin:0;padding:0;color:#555 !important;font-family:'Almarai', sans-serif !important;">
                <div class="content__image" style="-webkit-box-sizing:border-box;box-sizing:border-box;margin:0;padding:0;margin-top:4rem;text-align:center;">
                <img src="https://i.ibb.co/GPGpSmT/support.png" alt="support" style="-webkit-box-sizing:border-box;box-sizing:border-box;margin:0;padding:0;width:80%;min-width:20rem;">
                </div>
                <div class="content__text" style="-webkit-box-sizing:border-box;box-sizing:border-box;margin:0;padding:0;color:#555;text-align:center;color:#555 !important;font-family:'Almarai', sans-serif !important;">
                <h2 class="content__text--title" style="-webkit-box-sizing:border-box;box-sizing:border-box;margin:0;padding:0;margin-bottom:1rem;font-size:2.3rem !important;color:#555 !important;font-family:'Almarai', sans-serif !important;">
                    تم انشاء بلاغ جديد من قبل المستخدمين
                            </h2>
                <p class="content__text--welcoming" style="-webkit-box-sizing:border-box;box-sizing:border-box;margin:0;padding:0;margin-bottom:2rem;line-height:2.5rem;font-size:1.6rem !important;color:#555 !important;font-family:'Almarai', sans-serif !important;">
                    البلاغ رقم {}
                                <br style="-webkit-box-sizing:border-box;box-sizing:border-box;margin:0;padding:0;">
                    يمكنك الرد على البلاغ من خلال حساب الدعم الخاص بالدعم التقني
                            </p>
                <p class="content__text--reset-btn" style="-webkit-box-sizing:border-box;box-sizing:border-box;margin:0;padding:0;margin-top:2.5rem;margin-bottom:2.5rem;font-size:1.6rem !important;">
                    <a href={} style="-webkit-box-sizing:border-box;box-sizing:border-box;margin:0;padding:0;display:inline-block;text-decoration:none;padding:1.2rem 2.4rem;border-radius:5px;-webkit-transition:all .2s;-o-transition:all .2s;transition:all .2s;-webkit-box-shadow:0 3px 6px rgba(0, 0, 0, .16);box-shadow:0 3px 6px rgba(0, 0, 0, .16);color:white !important;background-color:#0FA591 !important;"> عرض البلاغ</a>
                </p>
                </div>
            </main>
            <footer class="footer" style="-webkit-box-sizing:border-box;box-sizing:border-box;margin:0;padding:0;border-top:1rem solid #0FA591;">
                <div class="footer__direction-message" style="-webkit-box-sizing:border-box;box-sizing:border-box;margin:0;padding:0;width:100%;">
                </div>
                <div class="footer__nav" style="-webkit-box-sizing:border-box;box-sizing:border-box;margin:0;padding:0;width:100%;margin-top:1rem;">
                <ul class="nav" style="-webkit-box-sizing:border-box;box-sizing:border-box;margin:0;padding:0;list-style:none;text-align:center;">
                    <li class="nav-item" style="-webkit-box-sizing:border-box;box-sizing:border-box;margin:0;padding:0;font-size:1.6rem;color:#0FA591 !important;"><a href="http://localhost:3000/login" style="-webkit-box-sizing:border-box;box-sizing:border-box;margin:0;padding:0;text-decoration:none;color:#0FA591 !important;">تسجيل الدخول</a></li>
                </ul>
                </div>
            </footer>
            </div>
        </body>
        </html>""".format(report_id,link)

def template_email_inform_user(report_id,name):
        
        return """\
            <!DOCTYPE html>
            <html lang="ar" style="font-size:62.5%;">
            <head>
                <meta charset="UTF-8">
                <meta http-equiv="X-UA-Compatible" content="IE=edge">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <link rel="preconnect" href="https://fonts.gstatic.com">
                <link href="https://fonts.googleapis.com/css2?family=Almarai:wght@400;700&display=swap" rel="stylesheet">
                <title>مختبراتي</title>
                
            </head>
            <body style="-webkit-box-sizing:border-box;box-sizing:border-box;margin:0;padding:0;font-family:'Almarai', sans-serif;background-color:#f8f8f8 !important;">
                <div class="template-container" style="-webkit-box-sizing:border-box;box-sizing:border-box;margin:0;padding:0;width:100%;max-width:55rem;margin:0 auto;margin-top:2rem;padding:0 1rem;padding-bottom:1.5rem;-webkit-box-shadow:0 3px 6px rgba(0, 0, 0, .16);box-shadow:0 3px 6px rgba(0, 0, 0, .16);border-radius:3px;color:#555;font-family:'Almarai', sans-serif;background-color:white !important;">
                <header class="header" style="-webkit-box-sizing:border-box;box-sizing:border-box;margin:0;padding:0;">
                    <div class="header__icon-logo" style="-webkit-box-sizing:border-box;box-sizing:border-box;margin:0;padding:0;text-align:center;padding:3rem 0;background-color:white;border-bottom:1rem solid #0FA591;">
                    <img src="https://i.ibb.co/C0nj3g9/icon-logo.png" alt="مختبراتي" style="-webkit-box-sizing:border-box;box-sizing:border-box;margin:0;padding:0;width:80%;max-width:25rem;">
                    </div>
                </header>
                <main class="content" style="-webkit-box-sizing:border-box;box-sizing:border-box;margin:0;padding:0;color:#555 !important;font-family:'Almarai', sans-serif !important;">
                    <div class="content__image" style="-webkit-box-sizing:border-box;box-sizing:border-box;margin:0;padding:0;margin-top:4rem;text-align:center;">
                    <img src="https://i.ibb.co/d0jhc7p/success-sent.png" alt="success-sent"  style="-webkit-box-sizing:border-box;box-sizing:border-box;margin:0;padding:0;width:80%;min-width:20rem;">
                    </div>
                    <div class="content__text" style="-webkit-box-sizing:border-box;box-sizing:border-box;margin:0;padding:0;color:#555;text-align:center;color:#555 !important;font-family:'Almarai', sans-serif !important;">
                    <h2 class="content__text--title" style="-webkit-box-sizing:border-box;box-sizing:border-box;margin:0;padding:0;margin-bottom:1rem;font-size:2.3rem !important;color:#555 !important;font-family:'Almarai', sans-serif !important;">
                        !تم انشاء بلاغك رقم {} بنجاح
                                </h2>
                    <p class="content__text--welcoming" style="-webkit-box-sizing:border-box;box-sizing:border-box;margin:0;padding:0;margin-bottom:2rem;line-height:2.5rem;font-size:1.6rem !important;color:#555 !important;font-family:'Almarai', sans-serif !important;">
                        أهلا {}
                                    <br style="-webkit-box-sizing:border-box;box-sizing:border-box;margin:0;padding:0;">
                        شكرا لك على مساعدتنا في تحسين جودة خدمتنا, في حالة الحاجة الى مزيد من المعلومات لحل المشكلة اللتي واجهتك, سوف يقوم احد الفنيين في التواصل معك عبر وسائل التواصل الخاصة بك
                                </p>
                    <p class="content__text--reset-btn" style="-webkit-box-sizing:border-box;box-sizing:border-box;margin:0;padding:0;margin-top:2.5rem;margin-bottom:2.5rem;font-size:1.6rem !important;">
                        <a href="http://localhost:3000/" style="-webkit-box-sizing:border-box;box-sizing:border-box;margin:0;padding:0;display:inline-block;text-decoration:none;padding:1.2rem 2.4rem;border-radius:5px;-webkit-transition:all .2s;-o-transition:all .2s;transition:all .2s;-webkit-box-shadow:0 3px 6px rgba(0, 0, 0, .16);box-shadow:0 3px 6px rgba(0, 0, 0, .16);color:white !important;background-color:#0FA591 !important;"> الذهاب للمنصة</a>
                    </p>
                    </div>
                </main>
                <footer class="footer" style="-webkit-box-sizing:border-box;box-sizing:border-box;margin:0;padding:0;border-top:1rem solid #0FA591;">
                    <div class="footer__direction-message" style="-webkit-box-sizing:border-box;box-sizing:border-box;margin:0;padding:0;width:100%;">
                    </div>
                    <div class="footer__nav" style="-webkit-box-sizing:border-box;box-sizing:border-box;margin:0;padding:0;width:100%;margin-top:1rem;">
                    <ul class="nav" style="-webkit-box-sizing:border-box;box-sizing:border-box;margin:0;padding:0;list-style:none;text-align:center;">
                        <li class="nav-item" style="-webkit-box-sizing:border-box;box-sizing:border-box;margin:0;padding:0;font-size:1.6rem;color:#0FA591 !important;"><a href="http://localhost:3000/login" style="-webkit-box-sizing:border-box;box-sizing:border-box;margin:0;padding:0;text-decoration:none;color:#0FA591 !important;">تسجيل الدخول</a></li>
                    </ul>
                    </div>
                </footer>
                </div>
            </body>
            </html>""".format(report_id,name)

def check_email(email):  
    if(not (re.search(regex_email,email))):
        return True
    return False         

def check_phone(phone):  
    if(not (re.search(regex_phone,phone))):
        return True
    return False   

def check_register_value(register_data):

    ##############################
    #check digit
    #check email format 
    #check phone format
    #check the roles
    ##############################
    
    #check if any missing attribute 
    if not('fname' in register_data and 'mname' in register_data and 'lname' in register_data and 'password' in register_data and
     'secondPassword' in register_data and 'phone' in register_data and 'email' in register_data and 'role' in register_data):
        abort(400, 'لا يوجد قيم في الطلب')   
    
    fname = register_data['fname']
    mname = register_data['mname']
    lname = register_data['lname']
    password = register_data['password']
    secondPassword = register_data['secondPassword']
    phone = register_data['phone']
    email = register_data['email']
    role = register_data['role']

    #check if any attribute is missing 
    if fname == '' or mname == '' or lname == '' or password == '' or secondPassword == '' or phone == '' or email == '' or role == '':
        abort(400, ' الرجاء اكمال تسجيل البيانات المطلوبة') 
    if check_phone(phone):
        abort(400, 'تحقق من رقم الهاتف') 
    if check_email(email):
        abort(400, 'تحقق من البريد الالكتروني')
    if role not in roles:
        abort(400, 'لا يمكنك الوصول')
    if password != secondPassword:
        abort(400, 'كلمة السر غير متطابقة')
    
    hash_pass = generate_password_hash(password, method='sha256')

    new_user = User(fname=fname,mname=mname,lname=lname,password=hash_pass,phone=phone,email=email,role=role)
    return new_user.insert()

def checkHasSchool(user):
    if user.role == 'School_Manager':
        school = School.query.filter_by(school_manager_id=user.id).first()
        if school is not None:
            return True
    elif user.role == 'Laboratory_Manager':
        lab_mngr = Laboratory_Manager.query.filter(and_(Laboratory_Manager.id==user.id, Laboratory_Manager.activate == True)).first()
        if lab_mngr is not None:
            return True
    elif user.role == 'Science_Teacher':
        science_teacher = Science_Teacher.query.filter(and_(Science_Teacher.id==user.id, Science_Teacher.activate == True)).first()
        if science_teacher is not None:
            return True
    else:
        return False

def login_process(login_data):

    #check if any missing attribute  
    if not ('email' in login_data and 'password' in login_data):
        abort(400, 'لا يوجد قيم في الطلب')  

    email = login_data['email']
    password = login_data['password']

    #check if any attribute is missing 
    if email == '' or password == '':
        abort(400, ' الرجاء اكمال تسجيل البيانات المطلوبة')

    if check_email(email):
        abort(400, 'تحقق من البريد الالكتروني')
    #User verification
    user = User.query.filter_by(email=email).first_or_404(description='البريد الالكتروني او كلمة المرور خاطئة')
    #Password verification
    if not check_password_hash(user.password, password):
        abort(401, description='البريد الالكتروني او كلمة المرور خاطئة')

    #return token
    hasSchool = checkHasSchool(user)

    return initiate_token(user.id,user.role,user.fname,user.lname,hasSchool), user

def accept_invitation(invitation_data,user_id):

    #check if any missing attribute  
    if not ('schoolId' in invitation_data):
        abort(400, 'لا يوجد قيم في الطلب')  

    school_id = invitation_data['schoolId']

    #check if any attribute is missing 
    if school_id is None:
        abort(400, ' الرجاء اكمال تسجيل البيانات المطلوبة')

    school_member = School_Member.query.filter_by(id=user_id).first_or_404(description='حدث خطأ يرجى المحاولة لاحقاً')
    invitations = Invitation.query.filter(and_(Invitation.member_id==school_member.id, Invitation.school_id == school_id)).first_or_404(description='لا توجد دعوة بهذا الرقم')
    user_info = school_member.user
    if user_info.role == 'Laboratory_Manager':
        lab_mngr = Laboratory_Manager.query.filter(and_(Laboratory_Manager.id==user_info.id, Laboratory_Manager.school_id == school_id)).first()
        if lab_mngr is not None:
            lab_mngr.update_activate(True)
        else:
            lab_mngr = Laboratory_Manager(id=user_info.id,school_id=school_id,activate=True)
            lab_mngr.insert()
    elif user_info.role == 'Science_Teacher':
        science_teacher = Science_Teacher.query.filter(and_(Science_Teacher.id==user_info.id, Science_Teacher.school_id == school_id)).first()
        if science_teacher is not None:
            science_teacher.update_activate(True)
        else:
            science_teacher = Science_Teacher(id=user_info.id,school_id=school_id,activate=True)
            science_teacher.insert()


    #delete all invitations 
    [s.delete() for s in school_member.invited_list]
    return initiate_token(user_info.id,user_info.role,user_info.fname,user_info.lname,True)

def reject_invitation(invitation_data,user_id):
    #check if any missing attribute  
    if not ('schoolId' in invitation_data):
        abort(400, 'لا يوجد قيم في الطلب')  

    school_id = invitation_data['schoolId']
    #check if any attribute is missing 
    if school_id is None:
        abort(400, ' الرجاء اكمال تسجيل البيانات المطلوبة')

    school_member = School_Member.query.filter_by(id=user_id).first_or_404(description='حدث خطأ يرجى المحاولة لاحقاً')
    invitation = Invitation.query.filter(and_(Invitation.member_id==school_member.id, Invitation.school_id == school_id)).first_or_404(description='لا توجد دعوة بهذا الرقم')
    invitation.delete()
    invitation.close()

def edit_profile(profile_data, user):

    if not('fname' in profile_data and 'mname' in profile_data and 'lname' in profile_data and 'oldPassword' in profile_data and
     'newPassword' in profile_data and 'phone' in profile_data and 'email' in profile_data):
        abort(400, 'لا يوجد قيم في الطلب')   
    
    fname = profile_data['fname']
    mname = profile_data['mname']
    lname = profile_data['lname']
    oldPassword = profile_data['oldPassword']
    newPassword = profile_data['newPassword']
    phone = profile_data['phone']
    email = profile_data['email']

    if fname == '' or mname == '' or lname == '' or phone == '' or email == '':
        abort(400, 'لا يوجد قيم في الطلب')

    #check if any modification happened on data 
    changed = False
    if fname != user.fname:
        user.update_fname(fname)
        changed = True
    if mname != user.mname:
        user.update_mname(mname)
        changed = True
    if lname != user.lname:
        user.update_lname(lname)
        changed = True
    if phone != user.phone:
        if check_phone(phone):
            abort(400, 'تحقق من رقم الهاتف')
        user.update_phone(phone)
        changed = True
    if email != user.email:
        if check_email(email):
            abort(400, 'تحقق من البريد الالكتروني')
        user.update_email(email)
        changed = True
    #maybe change the information but do not need to modify the password
    if  oldPassword != '':
        if  check_password_hash(user.password, oldPassword):
            if  newPassword != '':
                hash_pass = generate_password_hash(newPassword, method='sha256')
                user.update_password(hash_pass)
                changed = True
        else:
            abort(400, 'كلمه السر خاطئة')
    if not changed:
        abort(400, 'لا توجد قيمة متغيرة')

def forget_password_process(account_date):

    #validate the request
    if not('email' in account_date):
        abort(400, 'لا يوجد قيم في الطلب')   
    
    email = account_date['email']

    if email == '':
        abort(400, ' الرجاء اكمال تسجيل البيانات المطلوبة')

    #check the email format
    if check_email(email):
        abort(400, 'تحقق من البريد الالكتروني')
    #check if the email exist into system
    user = User.query.with_entities(User.id, User.email, User.fname,User.lname).filter_by(email=email).first_or_404(description='عنوان البريد الكتروني خطأ')
    #initiate reset password token
    token = initiate_reset_password_token(user.id,user.email)
    #get the token for this user and delete it. For each user has only one valid token to reset password
    valid_token = Valid_Token.query.filter(Valid_Token.user_id == User.id).first()
    if valid_token is not None:
        valid_token.delete()
    #create an object of token and store into database
    token_object = Valid_Token(token=token,user_id=user.id)
    token_object.insert()
    #return token and email
    return token, email , '{} {}'.format(user.fname,user.lname)

def send_email(token,email,name):

    #create the variable 
    from_ = app.config['ACCOUNT']
    password = app.config['ACCOUNT_PASSWORD']
    to_ = email

    reset_pass_url = "http://localhost:3000/reset-pass/{}".format(token)

    message = MIMEMultipart("alternative")
    message["Subject"] = 'إعادة تعيين كلمة المرور'
    message["From"] = from_
    message["To"] = to_

    # write the HTML part
    html = template_email_password(name,reset_pass_url)

    html_part = MIMEText(html, "html")
    message.attach(html_part)
    #initilize the server and send the message(link to reset the password) to destination account 
    try:
        server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
        server.login(from_, password)
        server.sendmail(from_, to_ ,message.as_string())
        server.quit()

    except smtplib.SMTPException:
        abort(400, 'لا يمكن تنفيذ طلبك الان')

def reset_password_process(reset_data):

    #validate the request
    if not('password' in reset_data and 'confirmedPassword' in reset_data and 'token' in reset_data):
        abort(400, 'لا يوجد قيم في الطلب')   
    
    password = reset_data['password']
    confirmPassword = reset_data['confirmedPassword']
    token = reset_data['token']

    if password == '' or confirmPassword == '' or token == '':
        abort(400, ' الرجاء اكمال تسجيل البيانات المطلوبة')

    if password != confirmPassword:
        abort(400, 'كلمة السر غير متطابقة')

    #decode the token
    payload = decode_auth_token(token)

    #check if the token are deleted: 1. change the token 2. token has been used 
    valid_token = Valid_Token.query.filter(Valid_Token.user_id == payload['sub']).first()
    #check if the token are same, not old one
    if valid_token is not None:
        if valid_token.token != token:
            abort(403, 'الرمز غير صحيح')
    #if we dont find any token in database
    else: 
        abort(403,'الرمز غير صالح للاستخدام')

    #get the user
    user = User.query.filter_by(id=payload['sub']).first_or_404('حدث خطأ, يرجى المحاولة لاحقاً')

    hash_pass = generate_password_hash(password, method='sha256')
    user.update_password(hash_pass)
    valid_token.delete()
    user.close_session()

def send_notification_support(report_id):

    #send notification to support for alerts there is a defect
    #create the variable 
    from_ = app.config['ACCOUNT']
    password = app.config['ACCOUNT_PASSWORD']
    to_ = app.config['SERVICE_ACCOUNT']

    defect_report_url = "http://localhost:3000/defect/{}".format(report_id)

    message = MIMEMultipart("alternative")
    message["Subject"] = 'إبلاغ عن ثغرة او مشكلة'
    message["From"] = from_
    message["To"] = to_

    # write the HTML part
    html = template_email_service(report_id,defect_report_url)

    html_part = MIMEText(html, "html")
    message.attach(html_part)
    #initilize the server and send the message(=) to destination account (service)
    try:
        server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
        server.login(from_, password)
        server.sendmail(from_, to_ ,message.as_string())
        server.quit()

    except smtplib.SMTPException:
        abort(400, 'لا يمكن تنفيذ طلبك الان')

def send_inform_user(report_id,name,email):

    #create the variable 
    from_ = app.config['ACCOUNT']
    password = app.config['ACCOUNT_PASSWORD']
    to_ = email

    message = MIMEMultipart("alternative")
    message["Subject"] = 'تم إستلام البلاغ'
    message["From"] = from_
    message["To"] = to_

    # write the HTML part
    html = template_email_inform_user(report_id,name)

    html_part = MIMEText(html, "html")
    message.attach(html_part)
    #initilize the server and send the message(=) to destination account 
    try:
        server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
        server.login(from_, password)
        server.sendmail(from_, to_ ,message.as_string())
        server.quit()

    except smtplib.SMTPException:
        abort(400, 'لا يمكن تنفيذ طلبك الان')

@public_route.route('/register', methods=['POST'])
def register():

    register_data = request.get_json()
    new_user = check_register_value(register_data)

    hasToekn = True
    token = ''

    #if there any issue with retrive the id of user will inform client there is no token initiated
    try:
        if new_user.role == 'System_Administrator':
            new_sys_admin = System_Administrator(id=new_user.id)
            new_sys_admin.insert() 
        elif new_user.role == 'School_Manager':
            new_school_manager = School_Manager(id=new_user.id)
            new_school_manager.insert()
        elif new_user.role == 'Science_Teacher' or new_user.role == 'Laboratory_Manager':
            new_school_member = School_Member(id=new_user.id)
            new_school_member.insert() 
        token = initiate_token(new_user.id,new_user.role,new_user.fname,new_user.lname,False)
        new_user.close_session()

    #if there is any isssue with initiate the token will send back false     
    except:
        hasToekn = False

    return jsonify({
        'success': True,
        'message': 'تمت عملية التسجيل الحساب بنجاح',
        'hasToken': hasToekn,
        'token': token
    })

'''
Request:
    {
 "nid": "1592631590",
 "fname": "Fouad",
 "mname": "A",
 "lname": "Ramadan",
 "password": "123456",
 "secondPassword": "123456",
 "phone": "0557797377",
 "email": "aa@hotmail.com",
 "role": "Laboratory_Manager"
}
Response:
{
    "hasToken": true,
    "message": "عملية التسجيل الحساب تمت بنجاح",
    "success": true,
    "token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJleHAiOjE2MTE3ODQ2NTUsImlhdC
    I6MTYxMTc4NDM1NSwic3ViIjoyMCwiZGF0YSI6eyJmbmFtZSI6IkZvdWFkIiwibG5hbWUiOiJNYW5zaG8iLCJyb2xlIjoiXHUwNjQyXHU
    wNjI3XHUwNjI2XHUwNjJmIFx1MDYyN1x1MDY0NFx1MDY0NVx1MDYyZlx1MDYzMVx1MDYzM1x1MDYyOSJ9
    LCJwZXJtaXNzaW9ucyI6IlNjaG9vbF9NYW5hZ2VyIn0.VXUEjcR_xnp804lI1Ebjf9TvaTMMkcEiwXFDpZVlQZ4"
}
'''

@public_route.route('/login', methods=['POST'])
def login():

    login_data = request.get_json()

    #if login process success will return a token
    token,user = login_process(login_data)

    return jsonify({
        'success': True,
        'message': 'عملية تسجيل الدخول تمت بنجاح',
        'user': user.format(),
        'token': token
    })

'''
Request:
{
 "nid": "1234567895",
 "password": "123456"
}
Response:
{
    "message": "عملية تسجيل الدخول تمت بنجاح",
    "success": true,
    "token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJleHAiOjE2MTE3ODQ2MjMs
    ImlhdCI6MTYxMTc4NDMyMywic3ViIjoxOSwiZGF0YSI6eyJmbmFtZSI6IkZvdWFkIiwibG5hbWUiOiJN
    YW5zaG8iLCJyb2xlIjoiXHUwNjQyXHUwNjI3XHUwNjI2XHUwNjJmIFx1MDYyN1x1MDY0NFx1MDY0NVx1MDYyZlx1
    MDYzMVx1MDYzM1x1MDYyOSJ9LCJwZXJtaXNzaW9ucyI6IlNjaG9vbF9NYW5hZ2VyIn0._CTIqYMNdxg-RV_LPIGqHyDo11_181y-spDG7wKigM4"
}
'''

@public_route.route('/profile', methods=['GET'])
@require_auth(['School_Manager','Laboratory_Manager','Educational_Supervisor','Science_Teacher','System_Administrator','Support'])
def display_profile(payload):

    user = User.query.filter_by(id=payload['sub']).first_or_404(description='يجب التسجيل في الموقع أولاً')
    return jsonify({
        'success': True,
        'user': user.format()
    })

'''
Request: 
{
header token 
}
Response:
{
    "email": "ff@hotmail.com",
    "fname": "Fouad",
    "lname": "Mansho",
    "mname": "A",
    "nid": "1224542790",
    "phone": 555123456,
    "role": "قائد المدرسة",
    "success": true
}
'''

@public_route.route('/profile', methods=['PATCH'])
@require_auth(['School_Manager','Laboratory_Manager','Educational_Supervisor','Science_Teacher','System_Administrator','Support'])
def modify_profile(payload):

    profile_data = request.get_json()
    #check the null before query 
    user = User.query.filter_by(id=payload['sub']).first_or_404(description='يجب التسجيل في الموقع أولاً')

    edit_profile(profile_data,user)
    user.commit_session()      
    hasSchool = checkHasSchool(user)

    data = jsonify({
            'success': True,
            'user': user.format(),
            'token': initiate_token(user.id,user.role,user.fname,user.lname,hasSchool)
            })

    user.close_session()

    return data

'''
Request: 
{
    "email": "ff@hotmail.com",
    "fname": "Fouad",
    "lname": "Mansho",
    "mname": "A",
    "phone": "555663336",
    "oldPassword": "12345",
    "newPassword": ""
}
Response:
{
    "email": "ff@hotmail.com",
    "fname": "Fouad",
    "lname": "Mansho",
    "mname": "A",
    "phone": "555663336",
    "success": true
}
'''

@public_route.route('/invitation-school', methods=['GET'])
@require_auth(['Laboratory_Manager','Science_Teacher'])
def display_all_invitation(payload):

    invitaion_data = request.get_json()

    invitations = Invitation.query.filter_by(member_id=payload['sub']).all()
    if invitations is None:
        abort(404, 'لا توجد اي دعوة حتى الان')
    
    content = [invite.format_recieve() for invite in invitations]

    return jsonify({
            'success': True,
            'invitations': content
             })

'''
Request: 
route: invitation_school
Response:
{
    "invitations": [
        {
            "memberId": 62,
            "message": "Welcome to Falah",
            "schoolId": 9
        }
    ],
    "success": true
}
'''

@public_route.route('/invitation-school', methods=['POST'])
@require_auth(['Laboratory_Manager','Science_Teacher'])
def accept_invitation_(payload):

    invitaion_data = request.get_json()
    #User verification
    id = payload['sub']
    if payload['permissions'] == 'Laboratory_Manager':
        lab_mngr = Laboratory_Manager.query.filter(and_(Laboratory_Manager.id==id, Laboratory_Manager.activate == True)).first()
        if lab_mngr is not None:
            abort(400, 'لايمكن تنفيذ الطلب لانك مسجل في مدرسة بالفعل')
    elif payload['permissions'] == 'Science_Teacher':
        science_teacher = Science_Teacher.query.filter(and_(Science_Teacher.id==id, Science_Teacher.activate == True)).first()
        if science_teacher is not None:
            abort(400, 'لايمكن تنفيذ الطلب لانك مسجل في مدرسة بالفعل')

    token = accept_invitation(invitaion_data,id)

    return jsonify({
            'success': True,
            'message': 'تم قبول الطلب بنجاح',
            'token': token
             })

'''
Request: 
{
    "schoolId": 9
}
Response:
{
    "success": true,
    'message': 'تم قبول الطلب بنجاح',
    "token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJleHAiOjE2MTMxMjQ1OTAsIm
    lhdCI6MTYxMzA4ODU5MCwic3ViIjo2MiwiZGF0YSI6eyJmbmFtZSI6IkZvdWFkIiwibG
    5hbWUiOiJSYW1hZGFuIiwicm9sZSI6Ilx1MDY0NVx1MDYyZFx1MDYzNlx1MDYzMSBcdTA
    2NDVcdTA2MmVcdTA2MmFcdTA2MjhcdTA2MzEiLCJoYXNTY2hvb2wiOnRydWV9LCJwZXJt
    aXNzaW9ucyI6IkxhYm9yYXRvcnlfTWFuYWdlciJ9.geQwZRzVudlRovO_GdGG1xuDgkRjI
    qV-FKVqp3b2Js"
}
'''

@public_route.route('/invitation-school', methods=['DELETE'])
@require_auth(['Laboratory_Manager','Science_Teacher'])
def reject_invitation_(payload):

    invitaion_data = request.get_json()
    #User verification
    id = payload['sub']
    if payload['permissions'] == 'Laboratory_Manager':
        lab_mngr = Laboratory_Manager.query.filter(and_(Laboratory_Manager.id==id, Laboratory_Manager.activate == True)).first()
        if lab_mngr is not None:
            abort(400, 'لايمكن تنفيذ الطلب لانك مسجل في مدرسة بالفعل')
    elif payload['permissions'] == 'Science_Teacher':
        science_teacher = Science_Teacher.query.filter(and_(Science_Teacher.id==id, Science_Teacher.activate == True)).first()
        if science_teacher is not None:
            abort(400, 'لايمكن تنفيذ الطلب لانك مسجل في مدرسة بالفعل')

    reject_invitation(invitaion_data,id)

    return jsonify({
            'success': True,
            'message': 'تم رفض الطلب بنجاح'
             })

'''
Request: 
{
    "schoolId": 9
}
Response:
{
    "success": true,
    'message': 'تم رفض الطلب بنجاح'
}
'''

####### RESET PASSWORD #######

@public_route.route('/forget-pass', methods=['POST'])
def forget_password():

    forget_pass_data = request.get_json()

    #initiate token
    token, email, name = forget_password_process(forget_pass_data)
    success = send_email(token,email,name)

    return jsonify({
            'success': True,
            'message': 'يرجى مراجعة البريد اللكتروني لإكمال عملية تغيير كلمة المرور',
            'token': token
             })

'''
{
    "message": "يرجى مراجعة البريد اللكتروني لإكمال عملية تغيير كلمة المرور",
    "success": true,
    "token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJleHAiOjE2MjA4NTkxMDksImlhdCI6MTYyMDg1ODgwOSwic3ViIjo0MiwiZGF0YSI6eyJlbWFpbCI6
    ImdvZmFzZDRAZ21haWwuY29tIn19.b7aMU1ZLmNVrUn339IJ6P3ohJK7BB6Rj323I-qZiauo"
}
'''

@public_route.route('/reset-pass', methods=['POST'])
def reset_password():

    forget_pass_data = request.get_json()
    #initiate token
    reset_password_process(forget_pass_data)

    return jsonify({
            'success': True,
            'message': 'تم تعديل كلمة المرور بنجاح'
             })

'''
{
    "message": "تم تعديل كلمة المرور بنجاح",
    "success": true
}
'''