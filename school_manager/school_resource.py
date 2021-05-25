from flask import Blueprint,jsonify,request,abort
from app.authentication import require_auth,initiate_token
from app.models.resources import School,City,Laboratory,Course
from app.models.users import School_Manager,User,Laboratory_Manager,Science_Teacher
from app.models.transactions import Invitation
from app.component import pagination,PAGE_SHELF
from sqlalchemy import and_, or_
import math

school_resource = Blueprint('school_resource',__name__)

'''
{
 "nid": "1224542790",
 "password": "123456"
}
{
 "nid": "1234567890",
 "password": "123456"
}
{
 "nid": "1592631597",
 "password": "123456"
}
{
 "nid": "1472583695",
 "password": "123456"
}
'''

def check_school(mngr_id):
    school_manager = School_Manager.query.filter_by(id=mngr_id).first_or_404(description='الرجاء التسجيل في النظام اولاً')
    school = school_manager.his_school
    # error out of index for that reason i check the length of list before
    if len(school) == 0:
        abort(404, 'ليس لديك مدرسة مسجلة')
    return school_manager, school[0]

########## SCHOOL ##########        

@school_resource.route('/school', methods=['POST'])
@require_auth(['School_Manager'])
def add_school(payload):

    #check if the manager has school first {Done}

    school_manager = School_Manager.query.filter_by(id=payload['sub']).first_or_404(description='حدث خطأ يرجى المحاولة لاحقاً')
    if len(school_manager.his_school) != 0:
        abort(400, 'لديك مدرسة مسجلة بالفعل')
    user = school_manager.user
    token = initiate_token(user.id,user.role,user.fname,user.lname,True)
    school_data = request.get_json()
    school_manager.add_school_process(school_data)
    
    school = School.query.filter_by(id=school_data['id']).first_or_404(description='حدث خطأ يرجى المحاولة لاحقاً')    

    return jsonify({ 
        'success': True,
        'message': 'تم انشاء المدرسة بنجاح',
        'school': school.format_details(),
        'token': token
    })

'''
Request:
{
    "id": 2000,
    "areaId": 10, 
    "name": "MM"
}
Response:
{
    "id": 8,
    "message": "تم انشاء المدرسة بنجاح",
    "success": true,
    "token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJleHAiOjE2MTI5OTgwN
    TIsImlhdCI6MTYxMjk2MjA1Miwic3ViIjo0NiwiZGF0YSI6eyJmbmFtZSI6IkZvdWFkI
    iwibG5hbWUiOiJSYW1hZGFuIiwicm9sZSI6Ilx1MDY0Mlx1MDYyN1x1MDYyNlx1MDY
    yZiBcdTA2MjdcdTA2NDRcdTA2NDVcdTA2MmZcdTA2MzFcdTA2MzNcdTA2MjkiLCJoY
    XNTY2hvb2wiOnRydWV9LCJwZXJtaXNzaW9ucyI6IlNjaG9vbF9NYW5hZ2VyIn0.wSw
    imOzhaYz-Iw4LNKYsRJqs6-CiixobxCM18AeDoOw"
}'''

@school_resource.route('/school', methods=['PATCH'])
@require_auth(['School_Manager'])
def modify_school(payload):

    school_manager, school = check_school(payload['sub'])

    school_data = request.get_json()
    school_manager.edit_school(school_data,school)

    return jsonify({
        'success': True,
        'school': school.format_details(), 
        'message': 'تم تعديل معلومات المدرسة بنجاح'
        })

'''
Request:
{
     "area":{
                "label": "West",
                "value": 10
            }
            , 
 "name": "مدرسة الصلاح",
 "id": 4
}
Response:
{
    "message": "تم تعديل معلومات المدرسة بنجاح",
    "success": true
}
'''

@school_resource.route('/school', methods=['DELETE'])
@require_auth(['School_Manager'])
def delete_school(payload):

    school_manager = School_Manager.query.filter_by(id=payload['sub']).first_or_404(description='حدث خطأ يرجى المحاولة لاحقاً')
    school = school_manager.his_school
    # error out of index for that reason i check the length of list before
    if len(school) == 0:
        abort(404, 'ليس لديك مدرسة مسجلة')

    user = school_manager.user
    token = initiate_token(user.id,user.role,user.fname,user.lname,False)
    school[0].delete()

    return jsonify({
        'message': 'تم حذف المدرسة بنجاح',
        'success': True,
        'token': token
    })

'''
Request:
route: school
Response:
{
    "message": "تم حذف المدرسة بنجاح",
    "success": true,
    "token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJleHAiOjE2MTI5OTgxMTU
    hdCI6MTYxMjk2MjExNSwic3ViIjo0NiwiZGF0YSI6eyJmbmFtZSI6IkZvdWFkIiwibG5h
    bWUiOiJSYW1hZGFuIiwicm9sZSI6Ilx1MDY0Mlx1MDYyN1x1MDYyNlx1MDYyZiBcdTA2M
    jdcdTA2NDRcdTA2NDVcdTA2MmZcdTA2MzFcdTA2MzNcdTA2MjkiLCJoYXNTY2hvb2wiO
    mZhbHNlfSwicGVybWlzc2lvbnMiOiJTY2hvb2xfTWFuYWdlciJ9.caLl_SF3Qp-2vXF5
    BAV_O7m0RBPWxpfPkBxpIyUGDkQ"
}
'''

@school_resource.route('/school', methods=['GET'])
@require_auth(['School_Manager'])
def get_school(payload):
    
    school_manager, school = check_school(payload['sub'])

    city_selection = City.query.order_by(City.id).all()
    city_content = [c.format_create() for c in city_selection]
    invitations_selection = school.invited
    invitations_content = [i.format() for i in invitations_selection] 

    laboratories_selection = school.own_labs
    laboratories_content = [l.format() for l in laboratories_selection]  
    lab_mngrs_selection = school.lab_manager_member
    lab_mngrs_content = [l.format_create() for l in lab_mngrs_selection]  
    st_selection = school.science_teacher_member
    st_content = [s.format_create() for s in st_selection] 

    return jsonify({
        'school': school.format_details(),
        'invitations': invitations_content,
        'laboratories': laboratories_content,
        'scienceTeachers': st_content,
        'laboratoryManagers': lab_mngrs_content,
        'success': True,
        'cities': city_content
        })

'''
Request: 
route: school
Response:
{
    "LaboratoryManagers": [
        {
            "label": "Fouad A Ramadan",
            "value": 62
        }
    ],
    "cities": [
        {
            "areas": [
                {
                    "label": "West",
                    "value": 10
                },
                {
                    "label": "east-west",
                    "value": 11
                }
            ],
            "label": "Jeddah",
            "value": 6
        }
    ],
    "invitations": [
        {
            "memberId": 62,
            "message": "Welcome to Falaha",
            "name": "Fouad A Ramadan",
            "schoolId": 1000
        }
    ],
    "laboratories": [
        {
            "value": 1
        }
    ],
    "school": {
        "id": 1000,
        "location": {
            "area": {
                "label": "West",
                "value": 10
            },
            "city": {
                "label": "Jeddah",
                "value": 6
            }
        },
        "name": "مدرسة الفلاح",
        "schoolManager": {
            "id": 46,
            "name": "Fouad Ramadan"
        }
    },
    "scienceTeachers": [
        {
            "label": "Fouad A Ramadan",
            "value": 63
        }
    ],
    "success": true
}
'''

@school_resource.route('/school/<int:school_id>', methods=['GET'])
@require_auth(['System_Administrator'])
def display_specific_school(payload,school_id):
    #modifed lab and member and invi        
    school = School.query.filter_by(id=school_id).first_or_404(description='لا توجد مدرسة بهذا الرقم')

    return jsonify({
        'school': school.format_details(),
        'success': True
        })

'''
Request:
route: school/4
Response:
{
    "school": {
        "id": 4,
        "location": {
            "area": "West",
            "city": "Jeddah"
        },
        "name": "مدرسة الحارث",
        "schoolManager": {
            "id": 46,
            "name": "Fouad Ramadan"
        }
    },
    "success": true
}
'''

@school_resource.route('/schools', methods=['GET'])
@require_auth(['System_Administrator'])
def display_all_schools(payload):

    selection = School.query.order_by(School.id).all()
    current_content, current_page = pagination(request,selection)

    if len(current_content) == 0:
        abort(404, 'لا يوجد مدارس للعرض')

    return jsonify({
        'success': True,
        'schools': current_content,
        'totalPages': math.ceil(len(selection)/PAGE_SHELF),
        'currentPage': current_page
        })

'''
Request:
para : page=1
Response:
{
    "currentPage": 1,
    "schools": [
        {
            "label": "مدرسة الحارث",
            "path": "/school/4",
            "value": 4
        }
    ],
    "success": true,
    "totalPages": 1
}
'''

@school_resource.route('/city/create-requirements', methods=['GET'])
@require_auth(['School_Manager'])
def city_requirements(payload):

    city_selection = City.query.order_by(City.id).all()
    city_content = [c.format_create() for c in city_selection]

    return jsonify({
        'cities': city_content,
        'success': True
        })

'''
Request:
route: /school/create_requirements
Response:
{
    "cities": [
        {
            "areas": [
                {
                    "label": "West",
                    "value": 10
                },
                {
                    "label": "east-west",
                    "value": 11
                }
            ],
            "label": "Jeddah",
            "value": 6
        }
    ],
    "success": true
}
'''

########## INVITATION ########## 

@school_resource.route('/invite-member', methods=['POST'])
@require_auth(['School_Manager'])
def invite_school_member(payload):

    school_manager, school = check_school(payload['sub'])
    invite_data = request.get_json()
    member_id = school_manager.send_invitation(invite_data,school)
    
    invitation = Invitation.query.filter(and_(Invitation.school_id==school.id, Invitation.member_id == member_id)).first_or_404(description='حدث خطأ, يرجى المحاولة لاحقاً')

    return jsonify({
        'message': 'تم انشاء دعوة جديدة بنجاح',
        'invitaion':invitation.format(),
        'success': True
            })
'''
Request:
{
    "memberId": 62,
    "message": "Welcome to Falaha"
}
Response:
{
    "invitaion": {
        "memberId": 63,
        "message": "Welcome to Falaha",
        "name": "Fouad A Ramadan",
        "schoolId": 1000
    },
    "message": "تم انشاء دعوة جديدة",
    "success": true
}
'''

@school_resource.route('/invite-member', methods=['GET'])
@require_auth(['School_Manager'])
def display_all_invitations(payload):

    school_manager, school = check_school(payload['sub'])

    invitations = school.invited
    invitations_content = [invite.format() for invite in invitations]

    if len(invitations_content) == 0:
        abort(404, 'لا توجد دعوات مرسلة')
    
    return jsonify({
        'invitations': invitations_content,
        'success': True
        })

'''
Request:
route: invite-member
Response:
{
    "invitations": [
        {
            "memberId": 62,
            "message": "Welcome to Falaha",
            "schoolId": 1000
        }
    ],
    "success": true
}
'''

@school_resource.route('/invite-member/<int:member_id>', methods=['DELETE'])
@require_auth(['School_Manager'])
def delete_invitations(payload,member_id):

    school_manager, school = check_school(payload['sub'])

    school_manager.delete_invitation(member_id,school)

    return jsonify({
        'invitations': 'تم حذف الدعوة بنجاح',
        'memberId': member_id,
        'success': True
        })
'''
Request:
{
    "memberId": 63
}
Response:
{
    "invitations": "تم حذف الدعوة بنجاح",
    "success": true
}
'''

########## LABORATORY ########## 

@school_resource.route('/laboratory', methods=['POST'])
@require_auth(['School_Manager'])
def add_laboratory(payload):

    school_manager, school = check_school(payload['sub'])

    laboratory_data = request.get_json()
    updated_list_manager, lab = school_manager.add_laboratory_process(laboratory_data,school)
    lab_mngrs_content = [l.format_create() for l in updated_list_manager]
    
    return jsonify({
        'message': 'تم انشاء مختبر جديد',
        'success': True,
        'lab': lab.format(),
        'labManagers': lab_mngrs_content
        })

'''
Request:
{
    "labId": 1
}
Response:
{
    "labId": 1,
    "message": "تم انشاء مختبر جديد",
    "success": true
}
'''

@school_resource.route('/laboratory/<int:lab_id>', methods=['GET'])
@require_auth(['School_Manager'])
def display_specific_laboratory(payload,lab_id):

    school_manager, school = check_school(payload['sub'])

    lab = Laboratory.query.filter(and_(Laboratory.number==lab_id, Laboratory.school_id == school.id)).first_or_404(description='لا يوجد مختبر بهذا الرقم')
    
    lab_mngrs = Laboratory_Manager.query.filter(and_(Laboratory_Manager.activate==True, Laboratory_Manager.school_id == school.id)).all()
    lab_mngrs_content = [l.format_create() for l in lab_mngrs]
    
    return jsonify({
        'laboratory': lab.format(),
        'labManagers': lab_mngrs_content,
        'success': True
        })

'''
Request:
route: /laboratory/1
Response:
{
    "LabManagers": [
        {
            "id": 62,
            "laboratories": [
                {
                    "label": 1,
                    "value": 1
                }
            ],
            "name": "Fouad A Ramadan"
        }
    ],
    "laboratories": {
        "id": 1,
        "labManagers": [
            {
                "id": 62,
                "laboratories": [
                    {
                        "label": 1,
                        "value": 1
                    }
                ],
                "name": "Fouad A Ramadan"
            }
        ]
    },
    "success": true
}
'''


@school_resource.route('/laboratory', methods=['GET'])
@require_auth(['School_Manager'])
def display_all_laboratories(payload):

    school_manager, school = check_school(payload['sub'])

    laboratories = school.own_labs
    laboratories_content = [l.format() for l in laboratories]
    
    return jsonify({
        'laboratories': laboratories_content,
        'success': True
        })
        
'''
Request:
route: invite-member
Response:
{
    "currentPage": 1,
    "laboratories": [
        {
            "id": 1,
            "labManagers": [
                {
                    "id": 62,
                    "laboratories": [
                        {
                            "label": 1,
                            "value": 1
                        }
                    ],
                    "name": "Fouad A Ramadan"
                }
            ]
        },
        {
            "id": 2,
            "labManagers": []
        },
        {
            "id": 3,
            "labManagers": []
        },
        {
            "id": 4,
            "labManagers": []
        },
        {
            "id": 5,
            "labManagers": []
        },
        {
            "id": 6,
            "labManagers": []
        }
    ],
    "success": true,
    "totalPages": 1
}
'''

@school_resource.route('/school/create-requirements', methods=['GET'])
@require_auth(['School_Manager'])
def display_school_requirements(payload):

    school_manager, school = check_school(payload['sub'])

    laboratories = school.own_labs
    laboratories_content = [l.format_details() for l in laboratories]
    science_teacher = school.science_teacher_member
    st_content = [l.format_requirement() for l in science_teacher]
    lab_manager = school.lab_manager_member
    lm_content = [l.format_requirement() for l in lab_manager]
    
    return jsonify({
        'laboratories': laboratories_content,
        'scienceTeacher': st_content,
        'labManager':lm_content,
        'success': True
        })
        
'''
Request:
route: /school/create-requirements
Response:
{
    "labManager": [
        {
            "id": 62,
            "name": "Fouad A Ramadan",
            "path": "/user/62",
            "role": "Laboratory_Manager",
            "roleAr": "محضر مختبر"
        }
    ],
    "laboratories": [
        {
            "id": 1
        }
    ],
    "scienceTeacher": [
        {
            "id": 63,
            "name": "Fouad A Ramadan",
            "path": "/user/63",
            "role": "Science_Teacher",
            "roleAr": "معلم علوم"
        }
    ],
    "success": true
}
'''

########## ASSIGN_ROLE ########## 

@school_resource.route('/assign-manager', methods=['PATCH'])
@require_auth(['School_Manager'])
def assign_lab_manager(payload):

    school_manager, school = check_school(payload['sub'])

    laboratory_data = request.get_json()
    updated_list_manager, lab = school_manager.assgin_manager_toLab(laboratory_data,school)
    lab_mngrs_content = [l.format_create() for l in updated_list_manager]

   
    return jsonify({
        'message': 'تم تعديل محضري المختبر في المختبر بنجاح',
        'labManagers': lab_mngrs_content,
        'lab': lab.format(),
        'success': True
        })
        
'''
Request:
{
    "labId": 1,
    "labManagers": [
        {
            "value":62,
            "status": "add"
        }
    ]
}
Response:
ADD CASE
{
    "lab": {
        "id": 1,
        "labManagers": [
            {
                "id": 62,
                "laboratories": [
                    {
                        "label": 1,
                        "value": 1
                    }
                ],
                "name": "Fouad A Ramadan",
                "path": "/laboratory-manager/62"
            }
        ],
        "path": "/laboratory/1"
    },
    "labManagers": [
        {
            "id": 62,
            "laboratories": [
                {
                    "label": 1,
                    "value": 1
                }
            ],
            "name": "Fouad A Ramadan",
            "path": "/laboratory-manager/62"
        }
    ],
    "laboratories": "تم تعديل محضري المختبر في المختبر بنجاح",
    "success": true
}
DELETE CASE
{
    "lab": {
        "id": 1,
        "labManagers": [],
        "path": "/laboratory/1"
    },
    "labManagers": [
        {
            "id": 62,
            "laboratories": [],
            "name": "Fouad A Ramadan",
            "path": "/laboratory-manager/62"
        }
    ],
    "laboratories": "تم تعديل محضري المختبر في المختبر بنجاح",
    "success": true
}
'''

@school_resource.route('/assign-course', methods=['PATCH'])
@require_auth(['School_Manager'])
def assign_course(payload):

    school_manager, school = check_school(payload['sub'])

    science_teacher_data = request.get_json()
    updated_list_course , science_teacher = school_manager.assgin_course_toSienceTeacer(science_teacher_data,school)
    course_content = [l.format_create() for l in updated_list_course]

    return jsonify({
        'message': 'تم تعديل المواد في قائمة التدريس بنجاح',
        'scienceTeacher': science_teacher.format_create(),
        'courses': course_content,
        'success': True
        })
        
'''
Request:
{
    "scienceTeacherId": 63,
    "courses": [
        {
            "value": 17,
            "status": "delete"
        }
        ,
        {
            "value": 18,
            "status": "add"
        }
    ]
}
Response:
ADD AND DELETE
{
    "courses": [
        {
            "label": "CPIT-402",
            "value": 17
        },
        {
            "label": "CPIT-100",
            "value": 19
        }
    ],
    "laboratories": "تم اضافة المواد في قائمة التدريس بنجاح",
    "scienceTeacher": {
        "courses": [
            {
                "label": "CPIT-200",
                "value": 18
            },
            {
                "label": "CPIT-100",
                "value": 19
            }
        ],
        "id": 63,
        "name": "Fouad A Ramadan",
        "path": "/science-teacher/63"
    },
    "success": true
}
'''

@school_resource.route('/assign-laboratory', methods=['PATCH'])
@require_auth(['School_Manager'])
def assign_lab(payload):

    school_manager, school = check_school(payload['sub'])

    lab_mngr_data = request.get_json()

    updated_list_labs , lab_mngr = school_manager.assgin_lab_toManager(lab_mngr_data,school)
    labs_content = [l.format() for l in updated_list_labs]

    return jsonify({
        'message': 'تم تعديل مختبرات محضر المختبر  بنجاح',
        'laboratoryManager': lab_mngr.format_create(),
        'laboratories': labs_content,
        'success': True
        })
        
'''
Request:
{
    "labManagerId": 62,
    "laboratories": [
        {
            "value":2,
            "status": "add"
        },
                {
            "value":1,
            "status": "same"
        }
    ]
}
Response:
{
    "LaboratoryManager": {
        "id": 62,
        "laboratories": [
            {
                "label": 1,
                "value": 1
            },
            {
                "label": 2,
                "value": 2
            }
        ],
        "name": "Fouad A Ramadan",
        "path": "/laboratory-manager/62"
    },
    "laboratories": [
        {
            "id": 2,
            "labManagers": [
                {
                    "id": 62,
                    "laboratories": [
                        {
                            "label": 1,
                            "value": 1
                        },
                        {
                            "label": 2,
                            "value": 2
                        }
                    ],
                    "name": "Fouad A Ramadan",
                    "path": "/laboratory-manager/62"
                }
            ],
            "path": "/laboratory/2"
        }
    ],
    "message": "تم تعديل مختبرات محضر المختبر  بنجاح",
    "success": true
}
'''

########## MEMBER ########## 

@school_resource.route('/science-teacher/<int:st_id>', methods=['GET'])
@require_auth(['School_Manager'])
def display_specific_ST(payload,st_id):

    school_manager, school = check_school(payload['sub'])

    science_teacher = Science_Teacher.query.filter(and_(Science_Teacher.id==st_id, Science_Teacher.school_id == school.id, Science_Teacher.activate == True)).first_or_404(description='لا يوجد معلم علوم بهذا الرقم')
    
    courses = Course.query.all()
    course_content = [c.format_create() for c in courses]
    
    return jsonify({
        'scienceTeacher': science_teacher.format_create(),
        'courses': course_content,
        'success': True
        })

'''
Request:
route: /laboratory/1
Response:
{
    "courses": [
        {
            "label": "CPIT-401",
            "value": 15
        },
        {
            "label": "CPIT-402",
            "value": 17
        },
        {
            "label": "CPIT-200",
            "value": 18
        },
        {
            "label": "CPIT-100",
            "value": 19
        },
        {
            "label": "CPIT-305",
            "value": 20
        },
        {
            "label": "CPIT-101",
            "value": 22
        },
        {
            "label": "CPIT-121",
            "value": 23
        },
        {
            "label": "CPIT-222",
            "value": 25
        }
    ],
    "scienceTeacher": {
        "courses": [
            {
                "label": "CPIT-401",
                "value": 15
            },
            {
                "label": "CPIT-402",
                "value": 17
            }
        ],
        "id": 63,
        "name": "Fouad A Ramadan"
    },
    "success": true
}
'''

@school_resource.route('/laboratory-manager/<int:lab_mngr_id>', methods=['GET'])
@require_auth(['School_Manager'])
def display_specific_lab_mngr(payload,lab_mngr_id):

    school_manager, school = check_school(payload['sub'])

    laboratory_manager = Laboratory_Manager.query.filter(and_(Laboratory_Manager.id==lab_mngr_id, Laboratory_Manager.school_id == school.id, Laboratory_Manager.activate == True)).first_or_404(description='لا يوجد محضر مختبر بهذا الرقم')
    labs = school.own_labs
    lab_content = [l.format() for l in labs]
    
    return jsonify({
        'laboratoryManager': laboratory_manager.format_create(),
        'laboratories': lab_content,
        'success': True
        })

'''
Request:
route: /laboratory/1
Response:
{
    "laboratories": [
        {
            "label": 1,
            "value": 1
        },
        {
            "label": 2,
            "value": 2
        },
        {
            "label": 3,
            "value": 3
        },
        {
            "label": 4,
            "value": 4
        },
        {
            "label": 5,
            "value": 5
        },
        {
            "label": 6,
            "value": 6
        }
    ],
    "laboratoryManager": {
        "id": 62,
        "laboratories": [
            {
                "label": 1,
                "value": 1
            }
        ],
        "name": "Fouad A Ramadan"
    },
    "success": true
}
'''

@school_resource.route('/laboratory-manager', methods=['GET'])
@require_auth(['School_Manager'])
def display_all_lab_mngr(payload):

    school_manager, school = check_school(payload['sub'])
    lab_mngr = school.lab_manager_member
    lab_mngr_content = [l.format_create() for l in lab_mngr]
    
    return jsonify({
        'laboratoryManagers': lab_mngr_content,
        'success': True
        })

########## DASHBOARD ########## 

@school_resource.route('/laboratory-manager/dashboard', methods=['GET'])
@require_auth(['School_Manager'])
def lab_mngr_dashboard(payload):

    school_manager, school = check_school(payload['sub'])

    response = school_manager.laboratory_manager_dashboard(school,request)
    
    return jsonify({
        'dashboard': response,
        'success': True
        })

'''
{
    "dashboard": {
        "approvedExperiments": 1,
        "endSemester": "Sat, 05 Jun 2021 00:00:00 GMT",
        "itemActivity": [
            [
                "January",
                0,
                0
            ],
            [
                "February",
                9,
                4
            ],
            [
                "March",
                2,
                0
            ],
            [
                "April",
                2,
                0
            ],
            [
                "May",
                0,
                0
            ],
            [
                "June",
                0,
                0
            ]
        ],
        "notApprovedExperiments": 0,
        "numberExecuteExperiment": [
            {
                "experimentExecuted": "EXP YY",
                "qunatity": 1
            },
            {
                "experimentExecuted": "X",
                "qunatity": 0
            },
            {
                "experimentExecuted": "Xa",
                "qunatity": 0
            }
        ],
        "numberExecutedDate": [
            [
                "Mon, 15 Mar 2021 00:00:00 GMT",
                1
            ]
        ],
        "numberLabs": 1,
        "rates": [
            {
                "name": "Fouad A Ramadan",
                "rate": 3.75
            }
        ],
        "startSemester": "Fri, 01 Jan 2021 00:00:00 GMT",
        "totalExperiments": 1
    },
    "success": true
}
'''

@school_resource.route('/laboratory/dashboard', methods=['GET'])
@require_auth(['School_Manager'])
def lab_dashboard(payload):

    school_manager, school = check_school(payload['sub'])

    response = school_manager.laboratory_dashboard(school,request)
    
    return jsonify({
        'dashboard': response,
        'success': True
        })

'''
{
    "dashboard": {
        "endSemester": "Sat, 05 Jun 2021 00:00:00 GMT",
        "executedExperiment": 16,
        "expiredItem": 16,
        "notExecutedExperiment": 0,
        "numberExecuteExperiment": [
            {
                "experimentExecuted": "EXP YY",
                "qunatity": 16
            },
            {
                "experimentExecuted": "X",
                "qunatity": 0
            },
            {
                "experimentExecuted": "Xa",
                "qunatity": 0
            }
        ],
        "numberExecutedDate": [
            [
                "Mon, 15 Mar 2021 00:00:00 GMT",
                16
            ]
        ],
        "numberSafetyItem": [
            {
                "quantity": 0,
                "safetyItem": "Fire extinguisher"
            }
        ],
        "startSemester": "Fri, 01 Jan 2021 00:00:00 GMT",
        "validItem": 112,
        "waitingExperiment": 0,
        "willExpireItem": 0
    },
    "success": true
}
'''