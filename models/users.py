from app import db
from flask import Blueprint,jsonify,request,abort
from app.authentication import require_auth
import datetime, pytz, calendar
from sqlalchemy import and_, or_, func,exists, asc, desc,case
from .resources import (Course,Ministry_Item,Semester,Manage_Semester,Manage_Course,Manage_Ministry_Item,Practical_Experiment,
Manage_Practical_Experiment,Practical_Item,City,Manage_City,Area,School,Laboratory,Manage_Laboratory,Teach_Course,Laboratory_Item,
Manage_Laboratory_Item,Remove_Laboratory_Item)   
from .transactions import Invitation,Practical_Experiment_Request,Confirm_Practical_Request,Item_Used
from .evaluate_system import Question,Manage_Question,Answer,Evaluate_Experiment,Evaluate,Evaluate_Type,Visit,Evaluate_Laboratory,Evaluate_Laboratory_Manager
from .support import Defect_Report
from app.component import DATE_FORMAT,getRoleAR,check_date_format,getReasonAR,get_class_number,RATE,WILL_EXPIRE_DAY
from sqlalchemy.exc import DataError,IntegrityError,NoSuchTableError,NoSuchColumnError,UnboundExecutionError
from sqlalchemy.orm.exc import NoResultFound

#role are: Educational_Supervisor, Laboratory_Manager, Science_Teacher, School_Manager, System_Administrator 

class User(db.Model):
       __tablename__ = 'users'

       id = db.Column(db.Integer, primary_key=True)
       fname = db.Column(db.String(40), nullable=False)
       mname = db.Column(db.String(40), nullable=False)
       lname = db.Column(db.String(40), nullable=False)
       password = db.Column(db.String(180), nullable=False)
       phone = db.Column(db.String(16), nullable=False)
       email = db.Column(db.String(100),unique=True, nullable=False)
       role = db.Column(db.String(25), nullable=False)

       educational_supervisor = db.relationship('Educational_Supervisor', backref='user', lazy='joined')
       school_member = db.relationship('School_Member', backref='user', lazy=True)
       school_manager = db.relationship('School_Manager', backref='user', lazy=True)
       system_administrator = db.relationship('System_Administrator', backref='user', lazy=True)
       reporter = db.relationship('Defect_Report',backref='user', lazy=True)  

       def format(self):
        return{
            'id': self.id,
            'fname': self.fname,
            'mname': self.mname,
            'lname': self.lname,
            'phone': self.phone,
            'email': self.email,
            'role': getRoleAR(self.role),
        }

       def format_details(self):
            return {
            'id':self.id,
            'name': self.fname + ' ' + self.mname + ' '+ self.lname,
            'role': self.role,
            'roleAr': getRoleAR(self.role),
            'path': '/user/{}'.format(self.id)
                }

       def full_name(self):
           return self.fname + ' ' + self.mname + ' '+ self.lname

       def getRole(self):
            return {
            'en': self.role,
            'ar': getRoleAR(self.role)
             }

       def __repr__(self):
           return 'User name {} and his role {}'.format(self.fname, self.role)
        
       def insert(self):
            try:   
                db.session.add(self)
                db.session.commit() 
                return self      
            except:
                db.session.rollback()
                abort(400, 'حدث خطأ, يرجى المحاولة لاحقاً') 
  
       def update_fname(self,fname):
            try:
                self.fname = fname
            except:
                db.session.rollback()
                abort(400, 'حدث خطأ, يرجى المحاولة لاحقاً')

       def update_mname(self,mname):
            try:
                self.mname = mname
            except:
                db.session.rollback()
                abort(400, 'حدث خطأ, يرجى المحاولة لاحقاً')

       def update_lname(self,lname):
            try:
                self.lname = lname
            except:
                db.session.rollback()
                abort(400, 'حدث خطأ, يرجى المحاولة لاحقاً')

       def update_phone(self,phone):
            try:
                self.phone = phone
            except:
                db.session.rollback()
                abort(400, 'حدث خطأ, يرجى المحاولة لاحقاً')

       def update_email(self,email):
            try:
                self.email = email
            except:
                db.session.rollback()
                abort(400, 'حدث خطأ, يرجى المحاولة لاحقاً')

       def update_password(self,password):
            try:
                self.password = password
                db.session.commit()
            except:
                db.session.rollback()
                abort(400, 'حدث خطأ, يرجى المحاولة لاحقاً')

       def create_report(self,report_data,user_id):
            #check if any missing attribute 
            if not('title' in report_data and 'text' in report_data):
                abort(400, 'لا يوجد قيم في الطلب')   

            title = report_data['title']
            text = report_data['text']

            #check if any attribute is null 
            if title == '' or text == '':
                abort(400, ' الرجاء اكمال تسجيل البيانات المطلوبة')

            report = Defect_Report(user_id=user_id,text=text,title=title)
            #return only ID not object
            return report.insert()

       def defect_solved(self,report_data,user_id):
            #check if any missing attribute 
            if not('id' in report_data and 'status' in report_data):
                abort(400, 'لا يوجد قيم في الطلب')   

            id = report_data['id']
            status = report_data['status']

            #check if any attribute is null 
            if id is None or not isinstance(status, bool):
                abort(400, ' الرجاء اكمال تسجيل البيانات المطلوبة')

            #get the report and check if its in the db
            report = Defect_Report.query.filter_by(id=id).first_or_404('لا يوجد تقرير عن خلل بهذا الرقم')
            #if there is no any change in the report status
            if report.status == status:
                abort(400, 'لا يوجد اي تغيير في حالة البلاغ')

            report.change_state(status)
            return report

       def close_session(self):
           db.session.close()

       def commit_session(self):
           db.session.commit()


class System_Administrator(db.Model):
    __tablename__ = 'system_administrator'


    id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    
    course = db.relationship('Course',secondary=Manage_Course, backref='modifier', lazy=True)  
    ministry_item = db.relationship('Ministry_Item',secondary=Manage_Ministry_Item, backref='modifier', lazy=True)
    semester = db.relationship('Semester', secondary=Manage_Semester, backref='modifier', lazy=True)
    practical_experiment = db.relationship('Practical_Experiment', secondary=Manage_Practical_Experiment, backref='modifier', lazy=True)
    city = db.relationship('City', secondary=Manage_City, backref='modifier', lazy=True)
    question = db.relationship('Question', secondary=Manage_Question, backref='modifier', lazy=True)

 
    def insert(self):
        try:   
            db.session.add(self)
            db.session.commit()       
        except:
            db.session.rollback()
            abort(400, 'حدث خطأ, يرجى المحاولة لاحقاً') 
    
    def format(self):
        return{
            'name': self.user.fname + ' ' + self.user.lname,
        }
    
    def check_valid_date(self,start_date,end_date,id):
        now = datetime.datetime.utcnow()
        #convert the string date to the object with appropriate format
        #and check the format of the date
        start_date_obj = check_date_format(start_date)
        end_date_obj = check_date_format(end_date)
        #check the date was given is acceptable and true
        if not (now < start_date_obj and end_date_obj > start_date_obj):
            abort(400, 'الرجاء ادخال تواريخ صحيحة')
        #check if there is any semester in that date    
        semester = Semester.query.filter(or_(Semester.start_date.between(start_date, end_date),(and_(start_date >= Semester.start_date, start_date <= Semester.end_date)))).first()
        if semester is not None and id != semester.id:
            abort(400, 'يوجد ترم دراسي في الوقت المحدد') 

    def add_course_process(self,course_data):

        #check if any missing attribute 
        if not('name' in course_data):
            abort(400, 'لا يوجد قيم في الطلب')   
        
        name = course_data['name']

        #check if any attribute is null 
        if name == '':
            abort(400, ' الرجاء اكمال تسجيل البيانات المطلوبة')
        
        course = Course(name=name)
        return course.insert()

    def edit_course(self,course_data):

        if not('newName' in course_data and 'id' in course_data):
            abort(400, 'لا يوجد قيم في الطلب')
        
        name = course_data['newName']
        id = course_data['id']
        
        if name == '' or id is None:
            abort(400, ' الرجاء اكمال تسجيل البيانات المطلوبة')

        course = Course.query.filter_by(id=id).first_or_404(description='لا توجد مادة بهذا الرقم')
    
        if course.name == name:
            abort(400, 'لا يوجد اي تغيير')

        course.update(name)
        course.append(self)
        return course

    def add_item(self,item_data):

        #check if any missing attribute 
        if not('name' in item_data and 'unit' in item_data and 'safety' in item_data):
            abort(400, 'لا يوجد قيم في الطلب')   
        
        name = item_data['name']
        unit = item_data['unit']
        safety = item_data['safety']


        #check if any attribute is null 
        if name == '' or unit == '' or not isinstance(safety, bool):
            abort(400, ' الرجاء اكمال تسجيل البيانات المطلوبة')
        #the units in the system
        units = ['centimeter','gram','millimeter', 'kilogram', 'milligram', 'ounces', 'piece']
        if unit.lower() not in units:
            abort(400, 'يرجى اختيار واحدة من وحدات القياس المسموحة')

        item = Ministry_Item(name=name,unit=unit.lower(),safety=safety)
        return item.insert()

    def edit_item(self,item_data):

            #check if any missing attribute 
        if not('name' in item_data and 'unit' in item_data and 'id' in item_data and 'safety' in item_data):
            abort(400, 'لا يوجد قيم في الطلب')   
        
        name = item_data['name']
        item_id = item_data['id']
        unit = item_data['unit']
        safety = item_data['safety']

        #check if any attribute is null 
        if name == '' or unit == '' or item_id is None or not isinstance(safety, bool):
            abort(400, ' الرجاء اكمال تسجيل البيانات المطلوبة')
    
        item = Ministry_Item.query.filter_by(id=item_id).first_or_404(description='لا توجد عهدة بهذا الرقم')

        if item.name == name and item.unit.lower() == unit.lower() and item.safety == safety:
            abort(400, 'لا يوجد اي تغيير')
        
        #the units in the system
        units = ['centimeter','gram','millimeter', 'kilogram', 'milligram', 'ounces', 'piece']
        if unit.lower() not in units:
            abort(400, 'يرجى اختيار واحدة من وحدات القياس المسموحة')
        
        item.update(name, unit.lower(),safety)
        item.append(self)

        return item

    def add_semester_process(self,semester_data):

        #check if any missing attribute
        if not('title' in semester_data and 'startDate' in semester_data and 'endDate' in semester_data):
            abort(400, 'لا يوجد قيم في الطلب')            

        title = semester_data['title']
        start_date = semester_data['startDate']
        end_date = semester_data['endDate']

        #check if any attribute is null 
        if title == '' or start_date == '' or end_date == '':
            abort(400, 'الرجاء اكمال تسجيل البيانات المطلوبة')
            
        #check if the date not used 
        self.check_valid_date(start_date,end_date,0)

        semester = Semester(title=title,start_date=start_date,end_date=end_date)
        return semester.insert()

    def edit_semester(self,semester_data):

        #check if any missing attribute 
        if not('id' in semester_data and 'title' in semester_data and 'startDate' in semester_data and 'endDate' in semester_data):
            abort(400, 'لا يوجد قيم في الطلب')   
        
        id = semester_data['id']
        title = semester_data['title']
        start_date = semester_data['startDate']
        end_date = semester_data['endDate']

        #check if any attribute is null 
        if id is None or title == '' or start_date == '' or end_date == '':
            abort(400, ' الرجاء اكمال تسجيل البيانات المطلوبة')
    
        semester = Semester.query.filter_by(id=id).first_or_404(description='لا يوجد ترم دراسي بهذا الرقم')
        #check if any value modified 

        #check the format of the date and return Object
        start_date_obj = check_date_format(start_date)
        end_date_obj = check_date_format(end_date)

        #convert Date to Datetime object (datetime.datetime.min.time() --> 00:00:00)
        start_date_db = datetime.datetime.combine(semester.start_date, datetime.datetime.min.time())
        end_date_db = datetime.datetime.combine(semester.end_date, datetime.datetime.min.time()) 

        if semester.title == title and start_date_db == start_date_obj and end_date_db == end_date_obj:
            abort(400, 'لا يوجد اي تغيير')

        if start_date_db != start_date_obj or end_date_db != end_date_obj:
            #check if the date not used 
            self.check_valid_date(start_date,end_date,id)

        semester.update(title, start_date, end_date)
        semester.append(self)
        return semester

    def add_experiment_process(self,experiment_data):

        #check if any missing attribute 
        if not('title' in experiment_data and 'courseId' in experiment_data and 'items' in experiment_data):
            abort(400, 'لا يوجد قيم في الطلب')   
        
        title = experiment_data['title']
        course_id = experiment_data['courseId']
        items = experiment_data['items']

        #check if any attribute is null 
        if title == '' or course_id is None:
            abort(400, ' الرجاء اكمال تسجيل البيانات المطلوبة')
        #check if there is no any item included with the experiment
        if len(items) < 1:
            abort(400, 'الرجاء اضافة عهدة واحدة لتكملة تسجيل التجربة')
        #check if the item in ministry item list 
        for item in items:
            if 'quantity' in item and 'value' in item:
                #check if the quantity higher than one 
                if item['quantity'] is None or item['quantity'] < 1:
                    abort(400, 'لا بد من اضافة كمية')   
                ministry_item = Ministry_Item.query.filter_by(id=item['value']).first_or_404(description='لايوجد {} في النظام'.format(item['label']))
            else:
                abort(400, 'لا يوجد قيم في الطلب')   
        #check if the course in the system 
        course = Course.query.filter_by(id=course_id).first_or_404(description='لا توجد مادة بهذا الرقم')
        #create the practical experiment
        practical_experiment = Practical_Experiment(title=title,course_id=course_id)
        practical_experiment = practical_experiment.insert()
        
        #add the item list to practical experiment
        for item in items: 
            practical_item = Practical_Item(practical_experiment_id=practical_experiment.id,ministry_item_id=item['value'],quantity=item['quantity'])
            practical_item.insert()

        return practical_experiment

    def edit_experiment(self,experiment_data):

        #check if any missing attribute 
        if not('id' in experiment_data and 'title' in experiment_data and 'courseId' in experiment_data and 'items' in experiment_data):
            abort(400, 'لا يوجد قيم في الطلب')   
        
        id = experiment_data['id']
        title = experiment_data['title']
        course_id = experiment_data['courseId']
        items = experiment_data['items']

        #check if any attribute is null 
        if id is None or title == '' or course_id is None or len(items) < 1:
            abort(400, ' الرجاء اكمال تسجيل البيانات المطلوبة')
        #get the practical experiment from database
        practical_experiment = Practical_Experiment.query.filter_by(id=id).first_or_404(description='لا توجد تجربة عملية بهذا الرقم')
        #temporary list of item
        item_list = []
        count = 0
        for item in items:
            #check if any missing attribute 
            if 'quantity' in item and 'value' in item and 'label' in item:
                #get the specific practical item and then check if the status add, delete or update 
                practical_item = Practical_Item.query.filter(and_(Practical_Item.practical_experiment_id==id, Practical_Item.ministry_item_id==item['value'])).first()
                item_list.append(practical_item)
                if item['status'] == 'add':
                    #if the object no null so there is already item exist in the practical experiment 
                    if practical_item is not None:
                        abort(400, 'مضاف بالفعل {}'.format(item['label']))
                    #is the object is null, so i need check if the item required in the system or not 
                    elif practical_item is None:
                        ministry_item = Ministry_Item.query.filter_by(id=item['value']).first_or_404(description='في النظام {} لايوجد'.format(item['label']))
                elif item['status'] == 'delete' or item['status'] == 'update':
                    #check if the object is null, so there is no any item related to this practical experiemnt need to delete 
                    if practical_item is None:
                        abort(404, description='مربوطة في هذه التجربة {} لا توجد عهدة'.format(item['label']))
                #same mean no change will be happen
                elif item['status'] == 'same':
                    count = count + 1
                #if the user insert any other operand into system
                else:
                    abort(400, 'لا يمكن تنفيذ هذه العملية')
            else:
                abort(400, 'لا يوجد قيم في الطلب') 
        #if there is no change into data 
        if practical_experiment.title == title and practical_experiment.course_id == course_id and len(items) == count:
            abort(400, 'لا يوجد اي تغيير')
        #update corse and title
        practical_experiment.update_course_id(course_id)
        practical_experiment.update_title(title)
        #update item depend on status either add or delete

        for item in items:
            #pop the value from the temproray list
            practical_item = item_list.pop(0)
            #add new item into practical experiment 
            if item['status'] == 'add':
                practical_item = Practical_Item(practical_experiment_id=id,ministry_item_id=item['value'],quantity=item['quantity'])
                practical_item.insert()
            elif item['status'] == 'delete': 
                #just delete the item but before that just confirm if the id is the same
                if practical_item.ministry_item_id == item['value'] and practical_item.practical_experiment_id == id:
                    practical_item.delete()
            elif item['status'] == 'update': 
                #update the quantity but before that just confirm if the id is the same 
                if practical_item.ministry_item_id == item['value'] and practical_item.practical_experiment_id == id:
                    practical_item.update_quantity(item['quantity'])

        #add the user to manage list 
        practical_experiment.append(self)
        return practical_experiment

    def add_city_process(self,city_data):

        #check if any missing attribute 
        if not('name' in city_data and 'areas' in city_data):
            abort(400, 'لا يوجد قيم في الطلب')   
        
        name = city_data['name']
        areas = city_data['areas']

        #check if any attribute is null 
        if name == '':
            abort(400, ' الرجاء اكمال تسجيل البيانات المطلوبة')
        
        if len(areas) < 1:
            abort(400, 'الرجاء اضافة منطقة واحدة لتكملة تسجيل التجربة')
                
        city = City(name=name)
        city = city.insert()

        areas = city_data['areas']
        for area in areas: 
            area_obj = Area(name=area['label'], city_id=city.id)
            area_obj.insert()

        return city

    def edit_city(self,city_data):

        #check if any missing attribute 
        if not('id' in city_data and 'name' in city_data and 'areas' in city_data):
            abort(400, 'لا يوجد قيم في الطلب') 
        
        id = city_data['id']
        name = city_data['name']
        areas = city_data['areas']

        #check if any attribute is null 
        if id is None or name == '' or len(areas) < 1:
            abort(400, ' الرجاء اكمال تسجيل البيانات المطلوبة')

        city = City.query.filter_by(id=id).first_or_404(description='لا توجد مدينة بهذا الرقم')

        count = 0

        city_id = city.id
        for area in areas:
            if area['status'] == 'add':
                area_obj = Area(name=area['label'],city_id=city_id)
                area_obj.insert()
            elif area['status'] == 'delete':
                area_obj = Area.query.filter(Area.id==area['value'], Area.city_id==city_id).first_or_404(description='لا توجد منطقة {} مربوطة مع هذه المدينة '.format(area['label']))
                area_obj.delete()
            elif area['status'] == 'update':
                area_obj = Area.query.filter(Area.id==area['value'], Area.city_id==city_id).first_or_404(description='لا توجد منطقة {} مربوطة مع هذه المدينة '.format(area['label']))
                area_obj.update(area['label'])
            elif area['status'] == 'same':
                count = count + 1
            else:
                abort(400, 'لا يمكن تنفيذ هذه العملية')

        if city.name == name and len(areas) == count:
            abort(400, 'لا يوجد اي تغيير')
        city.update_name(name)

        city.append(self)
        city.commit()

        return city

    def add_question(self,question_data):

        #check if any missing attribute 
        if not('text' in question_data and 'evaluateType' in question_data):
            abort(400, 'لا يوجد قيم في الطلب')   
        
        text = question_data['text']
        evaluate_type = question_data['evaluateType']

        #check if any attribute is null 
        if text == '' or evaluate_type is None:
            abort(400, ' الرجاء اكمال تسجيل البيانات المطلوبة')
                        
        question = Question(text=text,evaluate_type=evaluate_type)
        #return question after insert it into db to get the sequential id 
        return question.insert()

    def edit_question(self,question_data):

        #check if any missing attribute 
        if not('id' in question_data and 'text' in question_data and 'evaluateType' in question_data):
            abort(400, 'لا يوجد قيم في الطلب') 
        
        id = question_data['id']
        text = question_data['text']
        evaluate_type = question_data['evaluateType']

        #check if any attribute is null 
        if id is None or text == '' or evaluate_type is None:
            abort(400, ' الرجاء اكمال تسجيل البيانات المطلوبة')

        question = Question.query.filter_by(id=id).first_or_404(description='لا يوجد سؤال بهذا الرقم')
        #check if the request has no changed 
        if question.evaluate_type == evaluate_type:
            abort(400, 'لا يوجد اي تغيير')

        question.update_evaluate_type(evaluate_type)
        #get the response
        response = question.format()
        question.append(self)

        return response

    def add_education_supervisor(self,info_data):
        
        #check if any missing attribute 
        if not('courseId' in info_data and 'areaId' in info_data):
            abort(400, 'لا يوجد قيم في الطلب') 
        
        courseId = info_data['courseId']
        areaID = info_data['areaId']

        #check if any attribute is null 
        if courseId is None or areaID is None:
            abort(400, ' الرجاء اكمال تسجيل البيانات المطلوبة') 

        area = Area.query.with_entities(Area.id).filter_by(id=areaID).first_or_404('لا توجد منطقة بهذا الرقم')
        course = Area.query.with_entities(Course.id).filter_by(id=courseId).first_or_404('لا توجد مادة بهذا الرقم')

        #invoke the register function because the process will use
        from app.public_route import check_register_value  
        new_user = check_register_value(info_data) 

        new_edu_supervisor = Educational_Supervisor(id=new_user.id,area_id=area.id,course_id=course.id)
        return new_edu_supervisor.insert()

    def modify_education_supervisor(self,info_data):
        
        #check if any missing attribute 
        if not('educationalSupervisorId' in info_data and 'courseId' in info_data and 'areaId' in info_data):
            abort(400, 'لا يوجد قيم في الطلب') 
        
        courseId = info_data['courseId']
        areaID = info_data['areaId']
        id = info_data['educationalSupervisorId']

        #check if any attribute is null 
        if id is None or courseId is None or areaID is None:
            abort(400, ' الرجاء اكمال تسجيل البيانات المطلوبة') 

        edu_supervisor = Educational_Supervisor.query.filter_by(id=id).first_or_404('لا يوجد مشرف تربوي بهذا الرقم')

        if courseId == edu_supervisor.course_id and areaID == edu_supervisor.area_id:
            abort(400,'لا يوجد اي تغيير')

        #update the value if there any change 
        edu_supervisor.update_course(courseId)
        edu_supervisor.update_area(areaID)
        #commit all changed was happend and return education supervisor obejct 
        return edu_supervisor.commit()


class School_Manager(db.Model):
    __tablename__ = 'school_manager'

    id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)

    school = db.relationship('School', uselist=False ,backref='manager', lazy=True)  


    def format(self):
        return {
            'id': self.id,
            'name': self.user.fname + ' ' + self.user.lname
        }

    def insert(self):
        try:   
            db.session.add(self)
            db.session.commit()       
        except:
            db.session.rollback()
            abort(400, 'حدث خطأ, يرجى المحاولة لاحقاً') 

    def add_school_process(self,school_data):
        
        #check if any missing attribute 
        if not('id' in school_data and 'name' in school_data and 'areaId' in school_data):
            abort(400, 'لا يوجد قيم في الطلب')   
        
        id = school_data['id']
        name = school_data['name']
        area = school_data['areaId']

        #check if any attribute is null 
        if name == '' or area is None or id is None:
            abort(400, ' الرجاء اكمال تسجيل البيانات المطلوبة')
        area_obj = Area.query.filter_by(id=area).first_or_404(description='لا توجد منطقة بهذا الرقم')

        #when create a school will initiate in DB  
        school = School(id=id,name=name,school_manager_id=self.id,area_id=area_obj.id)
        school.insert() 
    
    def edit_school(self,school_data,school):
        #check if any missing attribute 
        if not('name' in school_data and 'areaId' in school_data and 'id' in school_data):
            abort(400, 'لا يوجد قيم في الطلب')   
        
        name = school_data['name']
        id = school_data['id']
        area = school_data['areaId']

        #check if any attribute is null 
        if name == '' or id is None or area is None:
            abort(400, ' الرجاء اكمال تسجيل البيانات المطلوبة')
    

        if school.name == name and school.area.id == area:
            abort(400, 'لا يوجد اي تغيير')
        
        area_obj = Area.query.filter_by(id=area).first_or_404(description='لا توجد منطقة بهذا الرقم')
        school.update(name,area_obj.id)
    
    def send_invitation(self,invite_data,school):

        if not('memberId' in invite_data and 'message' in invite_data):
            abort(400, 'لا يوجد قيم في الطلب')   
        
        member_id = invite_data['memberId']
        message = invite_data['message']

        #check if any attribute is null 
        if  member_id is None:
            abort(400, ' الرجاء اكمال تسجيل البيانات المطلوبة')
        
        #check if there any school memeber is the system or not
        member = School_Member.query.filter_by(id=member_id).first_or_404(description='لا يوجد عضو بهذا الرقم')
        #check the school member role either a laboratory record or a science teacher 
        if member.user.role == 'Laboratory_Manager':
            #check if the laboratory manager has acitve in any school
            lab_mngr = Laboratory_Manager.query.filter(and_(Laboratory_Manager.id==member_id, Laboratory_Manager.activate == True)).first()
            if lab_mngr is not None:
                abort(400, description='لا يمكن اضافة محضر المختبر, لانه مسجل في مدرسة بالفعل')
        elif member.user.role == 'Science_Teacher':
            #check if the scince teacher has acitve in any school
            science_teacher = Science_Teacher.query.filter(and_(Science_Teacher.id==member_id, Science_Teacher.activate == True)).first()
            if science_teacher is not None:
                abort(400, description='لا يمكن اضافة معلم العلوم, لانه مسجل في مدرسة بالفعل')

        #send invite to the school memeber 
        try:
            invite = Invitation(school_id=school.id,member_id=member.id,message=message) 
            invite.insert()
        #Issue with foreign key or primary key
        except IntegrityError:
            abort(500, 'يوجد خطأ في معلومات محضر المختبر او المختبر')
        except DataError:
            abort(500, 'يوجد خطأ في صياغة التاريخ')
        #No table with same name 
        except NoSuchTableError:
            abort(500, 'حدث خطأ من السيرفر, يرجى المحاولة لاحقاً')
        #No column with same name
        except NoSuchColumnError:
            abort(500, 'حدث خطأ من السيرفر, يرجى المحاولة لاحقاً')
        #no connection with databse
        except UnboundExecutionError:
            abort(500, 'حدث خطأ من السيرفر, يرجى المحاولة لاحقاً')

        return member_id

    def delete_invitation(self,member_id,school):

        #check if any attribute is missing 
        if member_id is None:
            abort(400, ' الرجاء اكمال تسجيل البيانات المطلوبة')

        school_member = School_Member.query.filter_by(id=member_id).first_or_404(description='لا يوجد حساب بهذا الرقم')
        invitation = Invitation.query.filter(and_(Invitation.member_id==school_member.id, Invitation.school_id == school.id)).first_or_404(description='لا توجد دعوة بهذا الرقم')
        invitation.delete()
        invitation.close() 

    def add_laboratory_process(self,laboratory_data,school):

        if not('labId' in laboratory_data and 'labManagers' in laboratory_data):
            abort(400, 'لا يوجد قيم في الطلب')   
        
        lab_id = laboratory_data['labId']
        lab_managers = laboratory_data['labManagers']

        #check if any attribute is null 
        if  lab_id is None:
            abort(400, ' الرجاء اكمال تسجيل البيانات المطلوبة')

        manager_list = []
        #check if any attribute is null 
        if  not(lab_managers is None or len(lab_managers) == 0):
            # check if the lab manager into the system (school)
            for lab_manager in lab_managers:
                lab_mngr = Laboratory_Manager.query.filter(and_(Laboratory_Manager.id==lab_manager['value'], Laboratory_Manager.school_id ==school.id)).first_or_404(description='{} لا يوجد محضر مختبر بهذا الرقم'.format(lab_manager['value']))
                manager_list.append(lab_mngr)

        #create school
        lab = school.create_lab(lab_id)
        
        #check if any attribute is null 
        if  not(lab_managers is None or len(lab_managers) == 0):
            for lab_mngr in manager_list:
                lab.append_manager(lab_mngr)
        
        return manager_list, lab

    def assgin_manager_toLab(self,laboratory_data,school):

        #manager_list contain object 
        #lab_managers contain request

        if not('labId' in laboratory_data and 'labManagers' in laboratory_data):
            abort(400, 'لا يوجد قيم في الطلب')   
        
        lab_id = laboratory_data['labId']
        lab_managers = laboratory_data['labManagers']

        #check if any attribute is null 
        if  lab_id is None or lab_managers is None or len(lab_managers) == 0:
            abort(400, ' الرجاء اكمال تسجيل البيانات المطلوبة')

        lab = Laboratory.query.filter(and_(Laboratory.number==lab_id, Laboratory.school_id ==school.id)).first_or_404(description='لا يوجد مختبر بهذا الرقم')
        # check if the lab manager into the system (school)
        manager_list = []
        for lab_manager in lab_managers:
            lab_mngr = Laboratory_Manager.query.filter(and_(Laboratory_Manager.id==lab_manager['value'], Laboratory_Manager.school_id ==school.id)).first_or_404(description='{} لا يوجد محضر مختبر بهذا الرقم'.format(lab_manager['value']))
            manager_list.append(lab_mngr)
            
        count = 0
        for x in range(len(manager_list)):
            #check if the lab manager already exist into lab or not (Depend on status)
            manager_work_on = manager_list[x].work_on_labs
            if lab_managers[x]['status'] == 'add':
                if lab in manager_work_on:
                    abort(400, 'محضر المختبر رقم {} قد تم تسجيله في مختبر رقم {}  من قبل'.format(manager_list[x].id,lab.number))
            elif lab_managers[x]['status'] == 'delete':
                if lab not in manager_work_on:
                    abort(400, 'لا يمكن ازالة محضر المختبر رقم {} لانه ليس مسجل في مختبر'.format(manager_list[x].id,lab.number))
            elif lab_managers[x]['status'] == 'same':
                count += 1
            else:
                abort(400, 'لا يمكن تنفيذ العملية')
        
        if count == len(manager_list):
            abort(400, 'لا يوجد اي تغيير')

        updated_list = []

        for x in range(len(manager_list)):
            #update the list of lab manager (Depend on status)
            if lab_managers[x]['status'] == 'add':
                updated_list.append(manager_list[x])
                lab.append_manager(manager_list[x])
            elif lab_managers[x]['status'] == 'delete':
                updated_list.append(manager_list[x])
                lab.remove_manager(manager_list[x])

        return updated_list, lab

    def assgin_course_toSienceTeacer(self,science_teacher_data,school):

        #course_list contain object 
        #courses contain request 

        if not('courses' in science_teacher_data and 'scienceTeacherId' in science_teacher_data):
            abort(400, 'لا يوجد قيم في الطلب')   
               
        science_teacher_id = science_teacher_data['scienceTeacherId']
        courses = science_teacher_data['courses']

        #check if any attribute is null 
        if  science_teacher_id is None or courses is None or len(courses) == 0:
            abort(400, ' الرجاء اكمال تسجيل البيانات المطلوبة')

        science_teacher = Science_Teacher.query.filter(and_(Science_Teacher.id==science_teacher_id, Science_Teacher.school_id ==school.id, Science_Teacher.activate == True)).first_or_404(description='لا يوجد معلم علوم بهذا الرقم')
        # check if the course into the system (school)
        course_list = []
        for course in courses:
            course_obj = Course.query.filter_by(id=course['value']).first_or_404(description='{} لا توجد مادة بهذا الرقم'.format(course['value']))
            course_list.append(course_obj)

        count = 0
        for x in range(len(course_list)):    
            #check if the science teacher already teach the course
            teach_course = science_teacher.teach
            if courses[x]['status'] == 'add':
                if course_list[x] in teach_course:
                    abort(404, 'معلم العلوم رقم {} قد تم تعيينه بتدريس مادة رقم {}  من قبل'.format(science_teacher.id,course_list[x].id))
            elif courses[x]['status'] == 'delete':
                if course_list[x] not in teach_course:
                    abort(404, 'لا بمكن حذف المادة, لان معلم العلوم رقم {} لم يتم تعيينه بتدريس مادة رقم {}  من قبل'.format(science_teacher.id,course_list[x].id))
            elif courses[x]['status'] == 'same':
                count += 1
            else:
                abort(400, 'لا يمكن تنفيذ العملية')

        if count == len(course_list):
            abort(400, 'لا يوجد اي تغيير')

        updated_list = []
        for x in range(len(course_list)):
            #update the list of course in science teacher (Depend on status)
            if courses[x]['status'] == 'add':
                updated_list.append(course_list[x])
                science_teacher.append_course(course_list[x])
            elif courses[x]['status'] == 'delete':
                updated_list.append(course_list[x])
                science_teacher.remove_course(course_list[x])

        return updated_list, science_teacher

    def assgin_lab_toManager(self,lab_mngr_data,school):

        #lab_list contain object 
        #laboratories contain request

        if not('labManagerId' in lab_mngr_data and 'laboratories' in lab_mngr_data):
            abort(400, 'لا يوجد قيم في الطلب')   
        
        laboratories = lab_mngr_data['laboratories']
        lab_manager_id = lab_mngr_data['labManagerId']

        #check if any attribute is null 
        if  lab_manager_id is None or laboratories is None or len(laboratories) == 0:
            abort(400, ' الرجاء اكمال تسجيل البيانات المطلوبة')

        lab_manager = Laboratory_Manager.query.filter(and_(Laboratory_Manager.id==lab_manager_id, Laboratory_Manager.school_id ==school.id, Laboratory_Manager.activate == True)).first_or_404(description='لا يوجد محضر مختر بهذا الرقم')
        # check if the lab manager into the system (school)
        lab_list = []
        for laboratory in laboratories:
            lab = Laboratory.query.filter(and_(Laboratory.number==laboratory['value'], Laboratory.school_id ==school.id)).first_or_404(description='لا يوجد مختبر بهذا الرقم')
            lab_list.append(lab)

        count = 0
        for x in range(len(lab_list)):    
            #check if the science teacher already teach the course
            lab_mngrs = lab_list[x].manager
            if laboratories[x]['status'] == 'add':
                if lab_manager in lab_mngrs:
                    abort(404, 'محضر المختبر رقم {} قد تم تسجيله في مختبر رقم {}  من قبل'.format(lab_manager.id,lab_list[x].number))
            elif laboratories[x]['status'] == 'delete':
                if lab_manager not in lab_mngrs:
                    abort(404, 'محضر المختبر رقم {} لم يتم تعيينه على مختبر رقم {}  من قبل'.format(lab_manager.id,lab_list[x].number))
            elif laboratories[x]['status'] == 'same':
                count += 1
            else:
                abort(400, 'لا يمكن تنفيذ العملية')

        if count == len(lab_list):
            abort(400, 'لا يوجد اي تغيير')

        updated_list = []
        for x in range(len(lab_list)):
            #update the list of course in science teacher (Depend on status)
            if laboratories[x]['status'] == 'add':
                updated_list.append(lab_list[x])
                lab_manager.append_lab(lab_list[x])
            elif laboratories[x]['status'] == 'delete':
                updated_list.append(lab_list[x])
                lab_manager.remove_lab(lab_list[x])

        return updated_list, lab_manager

    def laboratory_manager_dashboard(self,school,request):

        from_ = ''
        to_ = ''
        start_date = request.args.get('startDate')
        end_date = request.args.get('endDate')

        #get the time right now 
        tz = pytz.timezone('Asia/Riyadh')
        time = datetime.datetime.now(tz)
        #convert to needed format
        now = time.strftime(DATE_FORMAT)

        semester = Semester.query.filter(and_(Semester.start_date <= now, Semester.end_date >= now)).first_or_404('يمكنك الاستعلام في حين وجود فصل دراسي فعال')

        #### SEMESTER DATA ####
        #convert Date to Datetime object (datetime.datetime.min.time() --> 00:00:00)
        start_date_db = datetime.datetime.combine(semester.start_date, datetime.datetime.min.time())
        end_date_db = datetime.datetime.combine(semester.end_date, datetime.datetime.min.time()) 

        #if the user does not choose a specific date, so by default will use the date of semester
        from_ = start_date_db.strftime(DATE_FORMAT)
        to_ = end_date_db.strftime(DATE_FORMAT) 

        if start_date is not None and start_date != '':
            #check the format of the date and return Object
            start_date_obj = check_date_format(start_date)
            #must check if the date was choose by user in the semester or not 
            if start_date_obj >= start_date_db and start_date_obj <= end_date_db:
                from_ = start_date
            else: 
                abort(401, 'لا يمكنك الاستعلام عن تواريخ خارج الترم الدراسي الحالي')

        if end_date is not None and end_date != '':
            #check the format of the date and return Object
            end_date_obj = check_date_format(end_date)
            #must check if the date was choose by user in the semester or not 
            if end_date_obj >= start_date_db and end_date_obj <= end_date_db:          
                to_ = end_date
            else: 
                abort(401, 'لا يمكنك الاستعلام عن تواريخ خارج الترم الدراسي الحالي')
        #if the user insert end date smaller than the start date
        if from_ >= to_:
            abort(400, 'الرجاء اختيار تواريخ صحيحة')
        
        #to store all transaction of item in laboratory
        month_detail = []

        #start of month (month will Increment)
        start_month = check_date_format(from_)
        until = check_date_format(to_)

        #### GET LAB MANAGERS ####
        laboratroy_managers = school.lab_managers

        #### MAIN INFORMATION ####
        numberOfLabManager = laboratroy_managers.count()

        #### ITEM ACTIVITY MONTHLY ####
        
        done = False
        while True:
            start_ = start_month.strftime(DATE_FORMAT)
            end = ''
            # get the last day of month
            end_month = datetime.datetime(start_month.year, start_month.month, calendar.monthrange(start_month.year, start_month.month)[-1])
            #if the end month lower than until (to_)
            if end_month < until:
                end_ = end_month.strftime(DATE_FORMAT)
                #get the first day of next month (Increment Month)
                start_month = (end_month.replace(day=1) + datetime.timedelta(days=32)).replace(day=1)

            #if the end month greater than until (to_)
            else:
                end_ = until.strftime(DATE_FORMAT)
                done = True
            
            #get the number of item was added by this laboratroy manager
            added_quantity = laboratroy_managers.options(db.selectinload(Laboratory_Manager.added_items)).with_entities(func.count().label('count')).filter(Laboratory_Item.added_date.between(start_, end_)).first()[0]
            #get the number of item was deleted by this laboratroy manager
            deleted_quantity = laboratroy_managers.options(db.selectinload(Laboratory_Manager.deleted_items)).with_entities(func.count().label('count')).filter(Remove_Laboratory_Item.remove_date.between(start_, end_)).first()[0]
            #get the name of the month
            month_name = check_date_format(start_).strftime("%B")

            month_detail.append([
                month_name,
                added_quantity,
                deleted_quantity
            ])
            #if period has done will break the while loop
            if done:
                break

        #### MAIN INFORMATION ####
        #rate of laboratory manager
        rates = []
        for lab_mngr in laboratroy_managers:
            rates.append({'name': lab_mngr.school_member.full_name_member(), 'rate': float(lab_mngr.rate)})
        #number of lab, which responsible for them
        number_of_labs = Laboratory.query.with_entities(func.count().label('count')).filter(Laboratory.school_id==school.id).first()[0]

        #### PRACTICAL EXPERIMENT APPROVE ####
        #APPROVED            
        number_approved = laboratroy_managers.options(db.selectinload(Laboratory_Manager.all_request_confirmed)).with_entities(func.count().label('count')).filter(and_(
        Confirm_Practical_Request.lab_manager_school_id == school.id ,Confirm_Practical_Request.state == True)).first()[0]
        #NOT APPROVED
        number_not_approved = laboratroy_managers.options(db.selectinload(Laboratory_Manager.all_request_confirmed)).with_entities(func.count().label('count')).filter(and_(
        Confirm_Practical_Request.lab_manager_school_id == school.id ,Confirm_Practical_Request.state == False)).first()[0]
        #TOTAL EXPERIMENT
        total_experiment = number_approved + number_not_approved

        #### EXPERIMENT TYPE EXECUTED ####
        #dictionary to store experiment with number of executed 
        practical_experiments = []
        #get all experiment in the system 
        ministry_experiments = Practical_Experiment.query.with_entities(Practical_Experiment.id,Practical_Experiment.title).all()
        for experiment in ministry_experiments:
            number = laboratroy_managers.options(db.selectinload(Laboratory_Manager.all_request_confirmed)).with_entities(func.count().label('count')).filter(and_(
            Confirm_Practical_Request.lab_manager_school_id == school.id,
            Confirm_Practical_Request.request_id == Practical_Experiment_Request.id,
            Practical_Experiment_Request.execute_date.between(from_, to_),
            Practical_Experiment_Request.practical_experiment_id == experiment.id,
            Practical_Experiment_Request.id == Confirm_Practical_Request.request_id,
            Confirm_Practical_Request.executed == True)).first()[0]
            practical_experiments.append({
                'experimentExecuted': experiment.title,
                'qunatity': number
            })  

        #### EXPERIMENT EXECUTED WITH DATE ####
        #dictionary to store experiment with number of executed 
        practical_experiments_execute_date = []
        #get number of executed for each experiement in specific date  
        experiments = laboratroy_managers.options(db.selectinload(Laboratory_Manager.all_request_confirmed)).with_entities(
        Practical_Experiment_Request.execute_date,func.count(Practical_Experiment_Request.execute_date).label('count')).filter(
        and_(Confirm_Practical_Request.lab_manager_school_id == school.id,
        Confirm_Practical_Request.request_id == Practical_Experiment_Request.id,
        Practical_Experiment_Request.execute_date.between(from_, to_),
        Practical_Experiment_Request.id == Confirm_Practical_Request.request_id,
        Confirm_Practical_Request.executed == True)).group_by(
        Practical_Experiment_Request.execute_date).all()
        #change format to 2D array
        for experiment in experiments:
            practical_experiments_execute_date.append([experiment.execute_date,experiment.count])

        #### LABORATROY MANAGERS ACTIVITY WITH EXPERIMENT REQUEST ####
        #dictionary to store experiment with number of accepted and rejected 
        lab_manager_summary = []
        #get number of experiment eather accept or reject for each experiement for each laboratory manager         
        lab_managers_activity = laboratroy_managers.options(db.selectinload(Laboratory_Manager.all_request_confirmed)).with_entities(
        Confirm_Practical_Request.lab_manager_id,func.sum(case([(Confirm_Practical_Request.state == True, 1)], else_=0)).label('accept'),
        func.sum(case([(Confirm_Practical_Request.state == False, 1)], else_=0)).label('reject')).filter(
        and_(Confirm_Practical_Request.lab_manager_school_id == school.id,Confirm_Practical_Request.confirm_date.between(from_, to_))).group_by(
        Confirm_Practical_Request.lab_manager_id).all()
        
        #change format to 2D array
        for lab_manager_activity in lab_managers_activity:
            for lab_mngr in laboratroy_managers:
                if lab_manager_activity.lab_manager_id == lab_mngr.id:
                    lab_manager_summary.append([lab_mngr.school_member.full_name_member(),lab_manager_activity.accept,lab_manager_activity.reject])

        return {
           'startSemester': semester.start_date,
           'endSemester': semester.end_date,
           'labManagersCount': numberOfLabManager,
           'rates': rates,
           'numberLabs': number_of_labs,
           'totalExperiments': total_experiment,
           'approvedExperiments': number_approved,
           'notApprovedExperiments': number_not_approved,
           'itemActivity': month_detail,
           'numberExecuteExperiment': practical_experiments,
           'numberExecutedDate': practical_experiments_execute_date,
           'labManagersExperimentsSummary': lab_manager_summary
            }
        
    def laboratory_dashboard(self,school,request):

        from_ = ''
        to_ = ''
        start_date = request.args.get('startDate')
        end_date = request.args.get('endDate')

        #get the time right now 
        tz = pytz.timezone('Asia/Riyadh')
        time = datetime.datetime.now(tz)
        #convert to needed format
        now = time.strftime(DATE_FORMAT)

        semester = Semester.query.filter(and_(Semester.start_date <= now, Semester.end_date >= now)).first_or_404('يمكنك الاستعلام في حين وجود فصل دراسي فعال')

        #### SEMESTER DATA ####
        #convert Date to Datetime object (datetime.datetime.min.time() --> 00:00:00)
        start_date_db = datetime.datetime.combine(semester.start_date, datetime.datetime.min.time())
        end_date_db = datetime.datetime.combine(semester.end_date, datetime.datetime.min.time()) 

        #if the user does not choose a specific date, so by default will use the date of semester
        from_ = start_date_db.strftime(DATE_FORMAT)
        to_ = end_date_db.strftime(DATE_FORMAT) 

        if start_date is not None and start_date != '':
            #check the format of the date and return Object
            start_date_obj = check_date_format(start_date)
            #must check if the date was choose by user in the semester or not 
            if start_date_obj >= start_date_db and start_date_obj <= end_date_db:
                from_ = start_date
            else: 
                abort(401, 'لا يمكنك الاستعلام عن تواريخ خارج الترم الدراسي الحالي')

        if end_date is not None and end_date != '':
            #check the format of the date and return Object
            end_date_obj = check_date_format(end_date)
            #must check if the date was choose by user in the semester or not 
            if end_date_obj >= start_date_db and end_date_obj <= end_date_db:          
                to_ = end_date
            else: 
                abort(401, 'لا يمكنك الاستعلام عن تواريخ خارج الترم الدراسي الحالي')
        #if the user insert end date smaller than the start date
        if from_ >= to_:
            abort(400, 'الرجاء اختيار تواريخ صحيحة')
        
        #### GET LABS ####
        laboratories = school.laboratories
        #### LABORATORY ITEM ####
        expire_soon = (time + datetime.timedelta(days=WILL_EXPIRE_DAY)).strftime(DATE_FORMAT)
        #VALID 
        number_valid = Laboratory_Item.query.with_entities(func.count().label('count')).filter(and_(Laboratory_Item.school_id == school.id,
        Laboratory_Item.added_date.between(from_, to_),(
        or_(Laboratory_Item.expire_date > expire_soon,
        Laboratory_Item.expire_date == None)), Laboratory_Item.deleted == False)).first()[0]
        #WILL-EXPIRE
        number_will_expire = Laboratory_Item.query.with_entities(func.count().label('count')).filter(and_(Laboratory_Item.school_id == school.id, Laboratory_Item.added_date.between(from_, to_),
        Laboratory_Item.expire_date > now,
        Laboratory_Item.expire_date <= expire_soon, Laboratory_Item.deleted == False)).first()[0]
        #EXPIRED
        number_expired = Laboratory_Item.query.with_entities(func.count().label('count')).filter(and_(Laboratory_Item.school_id == school.id, Laboratory_Item.added_date.between(from_, to_),
        Laboratory_Item.expire_date <= now, Laboratory_Item.deleted == False)).first()[0]

        #### PRACTICAL EXPERIMENT REQUEST ####    
        #EXECUTED  
        number_executed = Practical_Experiment_Request.query.with_entities(func.count().label('count')).filter(and_(Practical_Experiment_Request.school_id == school.id,
        Practical_Experiment_Request.execute_date.between(from_, to_),
        Practical_Experiment_Request.id == Confirm_Practical_Request.request_id,
        Confirm_Practical_Request.executed == True)).first()[0]
        #NOT EXECUTED
        number_not_executed = Practical_Experiment_Request.query.with_entities(func.count().label('count')).filter(and_(Practical_Experiment_Request.school_id == school.id,
        Practical_Experiment_Request.execute_date.between(from_, to_),
        Practical_Experiment_Request.id == Confirm_Practical_Request.request_id,
        Confirm_Practical_Request.executed == False)).first()[0]
        #WAITING
        number_waiting = Practical_Experiment_Request.query.with_entities(func.count().label('count')).filter(and_(Practical_Experiment_Request.school_id == school.id,
        Practical_Experiment_Request.execute_date.between(from_, to_),
        Practical_Experiment_Request.id == Confirm_Practical_Request.request_id,
        Confirm_Practical_Request.executed == None)).first()[0]

        #### EXPERIMENT TYPE EXECUTED ####
        #dictionary to store experiment with number of executed 
        practical_experiments = []
        #get all experiment in the system 
        ministry_experiments = Practical_Experiment.query.with_entities(Practical_Experiment.id,Practical_Experiment.title).all()
        for experiment in ministry_experiments:
            number = Practical_Experiment_Request.query.with_entities(func.count().label('count')).filter(and_(Practical_Experiment_Request.school_id == school.id,
            Practical_Experiment_Request.execute_date.between(from_, to_),
            Practical_Experiment_Request.practical_experiment_id == experiment.id,
            Practical_Experiment_Request.id == Confirm_Practical_Request.request_id,
            Confirm_Practical_Request.executed == True)).first()[0]
            practical_experiments.append({
                'experimentExecuted': experiment.title,
                'qunatity': number
            })

        #### SAFETY EQUIPMENT ####
        #dictionary to store saftey item with number in the lab 
        safety_items = []
        #get all experiment in the system 
        ministry_safety_equipment = Ministry_Item.query.with_entities(Ministry_Item.id,Ministry_Item.name).filter_by(safety=True).all()
        for item in ministry_safety_equipment:
            number = Laboratory_Item.query.with_entities(func.count().label('count')).filter(and_(Practical_Experiment_Request.school_id == school.id,
            Laboratory_Item.added_date.between(from_, to_),
            Laboratory_Item.ministry_item_id == item.id)).first()[0]
            safety_items.append({
                'safetyItem': item.name,
                'quantity': number
            })

        #### EXPERIMENT EXECUTED WITH DATE ####
        #dictionary to store experiment with number of executed 
        practical_experiments_execute_date = []
        #get number of executed for each experiement in specific date 
        #  
        #experiments = laboratories.options(db.selectinload(Laboratory.requests)).with_entities(
        #Practical_Experiment_Request.execute_date,func.count(Practical_Experiment_Request.execute_date).label('count')).filter(
        #and_(Practical_Experiment_Request.school_id == school.id,Practical_Experiment_Request.execute_date.between(from_, to_),
        #Practical_Experiment_Request.id == Confirm_Practical_Request.request_id,
        #Confirm_Practical_Request.executed == True)).group_by(
        #Practical_Experiment_Request.execute_date).all()

        experiments = Practical_Experiment_Request.query.with_entities(
        Practical_Experiment_Request.execute_date,func.count(Practical_Experiment_Request.id).label('count')).filter(and_(
        Practical_Experiment_Request.school_id == school.id,Practical_Experiment_Request.id == Confirm_Practical_Request.request_id,
        Practical_Experiment_Request.execute_date.between(from_, to_),Confirm_Practical_Request.executed == True)).group_by(
        Practical_Experiment_Request.execute_date).all()
        
        #change format to 2D array
        for experiment in experiments:
            practical_experiments_execute_date.append([experiment.execute_date,experiment.count])
       
        return {
           'startSemester': semester.start_date,
           'endSemester': semester.end_date,
           'validItem': number_valid,
           'willExpireItem': number_will_expire,
           'expiredItem': number_expired,
           'executedExperiment': number_executed,
           'notExecutedExperiment': number_not_executed,
           'waitingExperiment': number_waiting,
           'numberExecuteExperiment': practical_experiments,
           'numberSafetyItem': safety_items,
           'numberExecutedDate': practical_experiments_execute_date
            }


class School_Member(db.Model):
    __tablename__ = 'school_member'

    id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)

    lab_manager_relation = db.relationship('Laboratory_Manager',backref='school_member', lazy=True)  
    science_teacher_relation = db.relationship('Science_Teacher',backref='school_member', lazy=True)  
    invited_relation = db.relationship('Invitation',backref='school_member', lazy=True)  

    def full_name_member(self):
        user = self.user
        return user.full_name()

    def getRole(self):
        user = self.user
        return user.getRole()

    def insert(self):
        try:   
            db.session.add(self)
            db.session.commit()       
        except:
            db.session.rollback()
            abort(400, 'حدث خطأ, يرجى المحاولة لاحقاً') 
    
    def close(self):
        db.session.close()


class Laboratory_Manager(db.Model):
    __tablename__ = 'laboratory_manager'

    id = db.Column(db.Integer, db.ForeignKey('school_member.id'))
    school_id = db.Column(db.Integer, db.ForeignKey('school.id'))
    activate = db.Column(db.Boolean,nullable=False)
    rate = db.Column(db.Numeric(precision=3,scale=2), default= 0.00)


    school_relation = db.relationship('School', backref='lab_manager_member', lazy='selectin')
    manage_lab = db.relationship('Laboratory', secondary=Manage_Laboratory, backref='manager', lazy=True)
    confirm_request_relation = db.relationship('Confirm_Practical_Request', backref='lab_manager', lazy=True)
    manage_item_relation = db.relationship('Laboratory_Item', secondary=Manage_Laboratory_Item,backref='lab_manager_modified', lazy=True)

    added_items = db.relationship('Laboratory_Item', backref='lab_manager_added', lazy='dynamic')
    deleted_items = db.relationship('Remove_Laboratory_Item', backref='lab_manager_modified', lazy='dynamic')

    __table_args__ = (
     db.PrimaryKeyConstraint(
        id, school_id,
         ),
     )
    
    all_request_confirmed = db.relationship('Confirm_Practical_Request', backref='laboratroy_manager_issued', lazy='dynamic')


    def format_requirement(self):
        user = self.school_member.user
        return user.format_details()
    
    def format_create(self):
        labs = self.work_on_labs
        content = [l.format_create() for l in labs]
        return{
            'name': self.school_member.full_name_member(),
            'id': self.id,
            'path': '/laboratory-manager/{}'.format(self.id),
            'laboratories':content,
            'rate': float(self.rate),
            'role': self.school_member.getRole() 
         }

    def format_label_value(self):
        return{
            'label': self.school_member.full_name_member(),
            'value': self.id
        }

    def format_evaluate(self):
        labs = self.work_on_labs
        content = [l.format_create() for l in labs]
        return{
            'name': self.school_member.full_name_member(),
            'id': self.id,
            'path': '/visit/current/laboratory-manager/{}'.format(self.id),
            'laboratories':content,
            'rate': float(self.rate),
            'role': self.school_member.getRole() 
         }

    def insert(self):
        try:   
            db.session.add(self)
            db.session.commit()       
        except:
            db.session.rollback()
            abort(400, 'لا توجد مدرسة بهذا الرقم') 

    def update_rate(self,rate):
        try:
            self.rate = rate
            db.session.flush()
        except:
            db.session.rollback()  
            abort(400, 'حدث خطأ, يرجى المحاولة لاحقاً')

    def update_activate(self,state):
        try:   
            self.activate = state
            db.session.commit()       
        except:
            db.session.rollback()
            abort(400, 'حدث خطأ, يرجى المحاولة لاحقاً') 
    
    def append_lab(self,lab):
        try:
            self.work_on_labs.append(lab)
            db.session.commit()
        except:
            db.session.rollback()  
            abort(400, 'حدث خطأ, يرجى المحاولة لاحقاً')

    def remove_lab(self,lab):
        try:
            self.work_on_labs.remove(lab)
            db.session.commit()
        except:
            db.session.rollback()  
            abort(400, 'حدث خطأ, يرجى المحاولة لاحقاً')

    def close(self):
        db.session.close()
    
    def commit(self):
        db.session.commit()
    
    def add_item(self,item_data,laboratory):

        #check if any missing attribute 
        if not('itemId' in item_data and 'expireDate' in item_data and 'hasExpireDate' in item_data and 'quantity' in item_data):
            abort(400, 'لا يوجد قيم في الطلب')   
        
        id = item_data['itemId']
        expire_date = item_data['expireDate']
        hasExpireDate = item_data['hasExpireDate']
        quantity = item_data['quantity']

        #check if any attribute is null 
        if id is None or quantity is None or hasExpireDate is None:
            abort(400, ' الرجاء اكمال تسجيل البيانات المطلوبة')

        #check if the item in the ministry item
        ministry_item = None
        try:
            ministry_item = Ministry_Item.query.filter_by(id=id).one()
        except NoResultFound: 
            abort(404, 'لا توجد عهدة بهذا الرقم')

        now = datetime.datetime.utcnow()
        #check the has expire date or not 
        #check the format of the date
        if hasExpireDate == True:
            #check the expire date higher than today 
            #convert the string date to the object with appropriate format
            try:
                expire_date_obj = check_date_format(expire_date)
            except ValueError:
                abort(400, 'الرجاء كتابة التاريخ بالصيغة الصحيحة')

            #check the date was given is acceptable and true
            if now > expire_date_obj:
                abort(400, 'لرجاء ادخال تاريخ انتهاء العهدة اكبر من اليوم')
        else:
            expire_date = None
        #check the quantity higher than zero 
        if quantity < 1:
            abort(400, 'لرجاء ادخال كمية')
        laboratory_item = None

        try:
            laboratory_item = Laboratory_Item(quantity=quantity,added_date=now,expire_date=expire_date,lab_manager_id=self.id,lab_manager_school=self.school_id,
            ministry_item_id=ministry_item.id)
            laboratory_item.insert()
            laboratory_item = laboratory.append_item(laboratory_item)
            laboratory_item.append_manager(self)
        #Issue with foreign key or primary key
        except IntegrityError:
            abort(500, 'يوجد خطأ في معلومات محضر المختبر او المختبر')
        except DataError:
            abort(500, 'يوجد خطأ في صياغة التاريخ')
        #No table with same name 
        except NoSuchTableError:
            abort(500, 'حدث خطأ من السيرفر, يرجى المحاولة لاحقاً')
        #No column with same name
        except NoSuchColumnError:
            abort(500, 'حدث خطأ من السيرفر, يرجى المحاولة لاحقاً')
        #no connection with databse
        except UnboundExecutionError:
            abort(500, 'حدث خطأ من السيرفر, يرجى المحاولة لاحقاً')
            
        return laboratory_item

    def edit_item(self,item_data,laboratory):

        #check if any missing attribute 
        if not('itemId' in item_data and 'expireDate' in item_data and 'quantity' in item_data and 'hasExpireDate' in item_data):
            abort(400, 'لا يوجد قيم في الطلب')   
        
        id = item_data['itemId']
        expire_date = item_data['expireDate']
        hasExpireDate = item_data['hasExpireDate']
        quantity = item_data['quantity']

        #check if any attribute is null 
        if id is None or quantity is None or hasExpireDate is None:
            abort(400, ' الرجاء اكمال تسجيل البيانات المطلوبة')

        #check if the item in his lab 
        laboratory_item = Laboratory_Item.query.filter(Laboratory_Item.id==id).first_or_404(description='لا توجد عهدة بهذا الرقم')
        lab_items = laboratory.lab_items
        if laboratory_item not in lab_items:
            abort(401, description='لا يمكنك الوصول الى العهدة المطلوبة')

        if laboratory_item.deleted == True:
            reason = laboratory_item.laboratory_item_removed[0].reason
            reasonAr = getReasonAR(reason)
            abort(404, 'العهدة محذوفة, السبب: {}'.format(reasonAr))

        access = False

        if hasExpireDate:
            #check date format and convert to object
            expire_date_obj = check_date_format(expire_date)
            #convert Date to Datetime object (datetime.datetime.min.time() --> 00:00:00)
            expire_date_obj_db = datetime.datetime.combine(laboratory_item.expire_date, datetime.datetime.min.time())    
            #check if there is any changed happend 
            if expire_date_obj == expire_date_obj_db:
                access = True
            #check from the expire date if lower than today
            now = datetime.datetime.utcnow()
            if now > expire_date_obj:
                    abort(400, description='لرجاء ادخال تاريخ انتهاء العهدة اكبر من اليوم')
        
        if quantity == 0 and access:
            abort(400, 'لا يوجد اي تغيير')

        #check the quantity is acceptable 
        if laboratory_item.quantity + quantity < 0:
                abort(400, description='لا توجد كمية كافية')

        #update values        
        laboratory_item.update(quantity,expire_date)
        laboratory_item.append_manager(self)

        return laboratory_item

    def remove_item(self,item_data,laboratory_item):

        #check if any missing attribute 
        if not('note' in item_data and 'reason' in item_data):
            abort(400, 'لا يوجد قيم في الطلب')   
        
        note = item_data['note']
        reason = item_data['reason']

        #check if any attribute is null 
        if reason == '':
            abort(400, ' الرجاء اكمال تسجيل البيانات المطلوبة')

        reasonList = ['broke','tainted','expired','lost','used']
        if reason not in reasonList:
            abort(400, 'الرجاء الاختيار واحدة من الاسباب المذكورة')

        #1 check if this item for his lab only 401 
        # (Get list of lab)
        # (Get list of item from lab object)
        # (Check the laboratory item in item list)
        # (Nested for loop) 
        access = False
        labs = self.work_on_labs
        for lab in labs:
            lab_items = lab.lab_items
            if laboratory_item in lab_items:
                access = True
        if access:
            #2 check if the item is already removed 400
            if laboratory_item.deleted:
                reason = laboratory_item.laboratory_item_removed[0].reason
                reasonAr = getReasonAR(reason)
                abort(404, description='العهدة محذوفة بالفعل, السبب: {}'.format(reasonAr))
            #deleted process
            now = datetime.datetime.utcnow()
            removed_item = Remove_Laboratory_Item(note=note,reason=reason,remove_date=now,lab_item=laboratory_item.id,lab_manager_id=self.id,lab_manager_school=self.school_id)
            removed_item.insert()
            laboratory_item.update_state()
            return removed_item
        else:
            abort(401, description='لا يمكنك الوصول الى العهدة المطلوبة')

    def confirm_request(self,practical_experiment_data,school,laboratories):
        #check if any missing attribute 
        if not('requestId' in practical_experiment_data and 'state' in practical_experiment_data and 'note' in practical_experiment_data):
            abort(400, 'لا يوجد قيم في الطلب')   
        
        id = practical_experiment_data['requestId']
        state = practical_experiment_data['state']
        note = practical_experiment_data['note']

        #check if any attribute is null 
        if id is None or not isinstance(state, bool):
            abort(400, ' الرجاء اكمال تسجيل البيانات المطلوبة')  
            
        labs_id = []
        for lab in laboratories:
            labs_id.append(lab.number) 
        #check if the request for his labs and exists 
        request = Practical_Experiment_Request.query.filter(and_(Practical_Experiment_Request.id == id,Practical_Experiment_Request.school_id == school.id,
        Practical_Experiment_Request.lab_id.in_(labs_id))).first_or_404(description='لا يوجد طلب تجربة عملية بهذا الرقم')

        #check if the request has been confirmed before 
        #here we handle out of index of array
        

        if request.confirmed == False:
            now = datetime.datetime.utcnow()
            message = ''
            items_used = []

            if state:
                #check there any available item    
                new_quantity = None
                practical_items = request.practical_experiment.practical_item
                for item in practical_items:
                    #multiple each item's quantity with the user input quantity to get the final quantity 
                    new_quantity = item.quantity * request.quantity
                    #get the laboratory item to check if science teacher can do the experiment or not so we summing all the items together
                    summing = Laboratory_Item.query.with_entities(func.sum(Laboratory_Item.quantity).label('sum')).filter(and_(Laboratory_Item.school_id== school.id,
                    Laboratory_Item.lab_id== request.lab_id,Laboratory_Item.ministry_item_id == item.ministry_item_id, Laboratory_Item.deleted == False,or_(
                    Laboratory_Item.expire_date == None, request.execute_date < Laboratory_Item.expire_date))).first()[0]
                    if summing is None or (summing is not None and summing < new_quantity):
                        abort(400, 'لا توجد كمية مناسبة لقبول الطلب')

                for item in practical_items:
                    #may lab item has many row in the database
                    lab_item_s = Laboratory_Item.query.filter(and_(Laboratory_Item.school_id== school.id, Laboratory_Item.lab_id== request.lab_id,
                    Laboratory_Item.ministry_item_id == item.ministry_item_id, Laboratory_Item.deleted == False, or_(
                    Laboratory_Item.expire_date == None, request.execute_date < Laboratory_Item.expire_date)))
                    lab_item_s = lab_item_s.order_by(Laboratory_Item.expire_date.asc()).all()
                    #get the remaining quantity 
                    remain = item.quantity * request.quantity
                    #for each item in the lab has many rows or quantity in spread so i check them
                    for lab_item in lab_item_s:
                        #use method that minus the quantity form lab item
                        remain, item_details = lab_item.use(remain,now)
                        #store that item will be used 
                        items_used.append(item_details)
                        #if i recieve zero mean i got all the quantity i need
                        if remain == 0:
                            break
                message = 'تم قبول الطلب بنجاح'          
            elif state == False:
                if note == '':
                    abort(400, 'يرجى كتابة سبب الرفض')  
                message = 'تم رفض الطلب بنجاح'          
            else:
                abort(400, 'الرجاء اضافة رد على هذا الطلب')

            request.update_confirmed()    
            confirmation = Confirm_Practical_Request(state=state,confirm_date=now,note=note,request_id=id,lab_manager_id=self.id,lab_manager_school_id = school.id)
            confirmation = confirmation.insert()

            for item in items_used:
                item_used = Item_Used(lab_manager_id=self.id,lab_manager_school_id=self.school_id,quantity=item['quantity'],lab_item_id=item['id'])
                confirmation.append_item_used(item_used)

            confirmation.commit()
            return confirmation, message
        else:
            return request.his_confirm[0],'تم الرد على الطلب من قبل'

    def edit_confirm_request(self,practical_experiment_data,school,laboratories):
        #check if any missing attribute 
        if not('requestId' in practical_experiment_data and 'state' in practical_experiment_data and 'note' in practical_experiment_data):
            abort(400, 'لا يوجد قيم في الطلب')   
        
        id = practical_experiment_data['requestId']
        state = practical_experiment_data['state']
        note = practical_experiment_data['note']

        #check if any attribute is null 
        if id is None or not isinstance(state, bool):
            abort(400, ' الرجاء اكمال تسجيل البيانات المطلوبة')  
            
        labs_id = []
        for lab in laboratories:
            labs_id.append(lab.number) 
        #check if the request for his labs and exists 
        request = Practical_Experiment_Request.query.filter(and_(Practical_Experiment_Request.id == id,Practical_Experiment_Request.school_id == school.id,
        Practical_Experiment_Request.lab_id.in_(labs_id), Practical_Experiment_Request.confirmed == True)).first_or_404(description='لا يوجد رد على طلب تجربة عملية بهذا الرقم')

        #check if the request has been confirmed before 
        #here we handle out of index of array
        confirmation = None
        try:
            confirmation = request.his_confirm[0]
        except IndexError:
            #out of index
            abort(404, 'لا يوجد رد على طلب تجربة عملية بهذا الرقم')

        if confirmation.state == state:
            abort(400, 'لا يوجد اي تغيير')
        
        if state:
            now = datetime.datetime.utcnow()
            message = ''
            items_used = []
            #check there any available item    
            new_quantity = None
            practical_items = request.practical_experiment.practical_item
            for item in practical_items:
                #multiple each item's quantity with the user input quantity to get the final quantity 
                new_quantity = item.quantity * request.quantity
                #get the laboratory item to check if science teacher can do the experiment or not
                summing = Laboratory_Item.query.with_entities(func.sum(Laboratory_Item.quantity).label('sum')).filter(and_(Laboratory_Item.school_id== school.id,
                Laboratory_Item.lab_id== request.lab_id,Laboratory_Item.ministry_item_id== item.ministry_item_id, Laboratory_Item.deleted == False,or_(
                Laboratory_Item.expire_date == None, request.execute_date < Laboratory_Item.expire_date))).first()[0]
                if summing is None or (summing is not None and summing < new_quantity):
                    abort(400, 'لا توجد كمية مناسبة لقبول الطلب')

            for item in practical_items:
                #may lab item has many row in the database
                lab_item_s = Laboratory_Item.query.filter(and_(Laboratory_Item.school_id== school.id,Laboratory_Item.ministry_item_id == item.ministry_item_id,
                Laboratory_Item.lab_id== request.lab_id, Laboratory_Item.deleted == False, or_(
                Laboratory_Item.expire_date == None, request.execute_date < Laboratory_Item.expire_date)))
                lab_item_s = lab_item_s.order_by(Laboratory_Item.expire_date.asc()).all()
                #get the remaining quantity 
                remain = item.quantity * request.quantity
                #for each item in the lab has many rows or quantity in spread so i check them
                for lab_item in lab_item_s:
                    #use method that minus the quantity form lab item
                    remain, item_details = lab_item.use(remain,now)
                    #store that item will be used 
                    items_used.append(item_details)
                    #if i recieve zero mean i got all the quantity i need
                    if remain == 0:
                        break

            for item in items_used:
                item_used = Item_Used(lab_manager_id=self.id,lab_manager_school_id=self.school_id,quantity=item['quantity'],lab_item_id=item['id'])
                confirmation.append_item_used(item_used)
            confirmation.commit()

            message = 'تم قبول الطلب بنجاح'          
        elif state == False:
            if note == '':
                abort(400, 'يرجى كتابة سبب الرفض')  
            
            items_used = confirmation.items_used
            #remove all items related to it with return the quantity to lab item and change the state     
            for item in items_used:
                lab_item = item.lab_item
                lab_item.retrieve(item.quantity)
                item.delete()

            message = 'تم رفض الطلب بنجاح'          
        else:
            abort(400, 'الرجاء اضافة رد على هذا الطلب')

        confirmation.update_state()
        return confirmation, message

    def delete_confirm_request(self,request_id,laboratories,school):

        labs_id = []
        for lab in laboratories:
            labs_id.append(lab.number) 
        #check if the request for his labs and exists
        request = Practical_Experiment_Request.query.filter(and_(Practical_Experiment_Request.id == request_id,Practical_Experiment_Request.school_id == school.id,
        Practical_Experiment_Request.lab_id.in_(labs_id), Practical_Experiment_Request.confirmed == True)).first_or_404(description='لا يوجد رد على طلب تجربة عملية بهذا الرقم')

        confirmation = None
        try:
            #check if there is a confirm
            confirmation = request.his_confirm[0]
        except IndexError:
            #out of index
            abort(404, 'لا يوجد رد على طلب تجربة عملية بهذا الرقم') 
        #remove all items related to it with return the quantity to lab item and change the state     
        items_used = confirmation.items_used
        for item in items_used:
            lab_item = item.lab_item
            lab_item.retrieve(item.quantity)
            item.delete()
        #update confirm state in request        
        request.update_confirmed()
        #delete the confirmation
        confirmation.delete()
        return request

    def confirm_execution_request(self,practical_experiment_data,request):

        #check if any missing attribute 
        if not('executed' in practical_experiment_data):
            abort(400, 'لا يوجد قيم في الطلب')   
        
        executed = practical_experiment_data['executed']

        #check if any attribute is null 
        if  not isinstance(executed, bool):
            abort(400, ' الرجاء اكمال تسجيل البيانات المطلوبة') 
        
        #check if the request has confirmed and if has been executed or not
        confirmation = None
        try:
            confirmation = request.his_confirm[0]
            if confirmation.executed is not None:
                abort(400, 'تم الرد مسبقا على تنفيذ التجربة')
        except AttributeError:
            abort(400,'يرجى تأكيد الطلب قبل ارفاق الجواب')
        except IndexError:
            abort(400,'يرجى تأكيد الطلب قبل ارفاق الجواب')

        #get time zone of KSA
        tz = pytz.timezone('Asia/Riyadh')
        time = datetime.datetime.now(tz)
        #convert to needed format
        now = time.strftime(DATE_FORMAT)
        #get the class number which science teacher can evaluate
        class_number_now = get_class_number(time)

        #convert Date to Datetime object (datetime.datetime.min.time() --> 00:00:00)
        time_now = check_date_format(now)
        execute_date_db = datetime.datetime.combine(request.execute_date, datetime.datetime.min.time())
        #check if the time of experiment become in past then update the status of executed eaither true or false
        if execute_date_db < time_now or (execute_date_db == time_now and request.class_number < class_number_now):

            #if the experiment has been not executed so the item has chossen for this will be return
            if executed == False: 
                #remove all items related to it with return the quantity to lab item and change the state     
                items_used = confirmation.items_used
                for item in items_used:
                    lab_item = item.lab_item
                    lab_item.retrieve(item.quantity)
                    item.delete()

            #update the executed state    
            confirmation.update_executed(executed)

    def dashboard(self,request):

        from_ = ''
        to_ = ''
        start_date = request.args.get('startDate')
        end_date = request.args.get('endDate')

        #get the time right now 
        tz = pytz.timezone('Asia/Riyadh')
        time = datetime.datetime.now(tz)
        #convert to needed format
        now = time.strftime(DATE_FORMAT)

        semester = Semester.query.filter(and_(Semester.start_date <= now, Semester.end_date >= now)).first_or_404('يمكنك الاستعلام في حين وجود فصل دراسي فعال')

        #### SEMESTER DATA ####
        #convert Date to Datetime object (datetime.datetime.min.time() --> 00:00:00)
        start_date_db = datetime.datetime.combine(semester.start_date, datetime.datetime.min.time())
        end_date_db = datetime.datetime.combine(semester.end_date, datetime.datetime.min.time()) 

        #if the user does not choose a specific date, so by default will use the date of semester
        from_ = start_date_db.strftime(DATE_FORMAT)
        to_ = end_date_db.strftime(DATE_FORMAT) 

        if start_date is not None and start_date != '':
            #check the format of the date and return Object
            start_date_obj = check_date_format(start_date)
            #must check if the date was choose by user in the semester or not 
            if start_date_obj >= start_date_db and start_date_obj <= end_date_db:
                from_ = start_date
            else: 
                abort(401, 'لا يمكنك الاستعلام عن تواريخ خارج الترم الدراسي الحالي')

        if end_date is not None and end_date != '':
            #check the format of the date and return Object
            end_date_obj = check_date_format(end_date)
            #must check if the date was choose by user in the semester or not 
            if end_date_obj >= start_date_db and end_date_obj <= end_date_db:          
                to_ = end_date
            else: 
                abort(401, 'لا يمكنك الاستعلام عن تواريخ خارج الترم الدراسي الحالي')
        #if the user insert end date smaller than the start date
        if from_ >= to_:
            abort(400, 'الرجاء اختيار تواريخ صحيحة')
        
        #to store all transaction of item in laboratory
        month_detail = []

        #start of month (month will Increment)
        start_month = check_date_format(from_)
        until = check_date_format(to_)

        #### ITEM ACTIVITY MONTHLY ####
    
        done = False
        while True:
            start_ = start_month.strftime(DATE_FORMAT)
            end = ''
            # get the last day of month
            end_month = datetime.datetime(start_month.year, start_month.month, calendar.monthrange(start_month.year, start_month.month)[-1])
            #if the end month lower than until (to_)
            if end_month < until:
                end_ = end_month.strftime(DATE_FORMAT)
                #get the first day of next month (Increment Month)
                start_month = (end_month.replace(day=1) + datetime.timedelta(days=32)).replace(day=1)

            #if the end month greater than until (to_)
            else:
                end_ = until.strftime(DATE_FORMAT)
                done = True

            #get the number of item was added by this laboratroy manager
            added_quantity = self.added_items.with_entities(func.count().label('count')).filter(Laboratory_Item.added_date.between(start_, end_)).first()[0]
            #get the number of item was deleted by this laboratroy manager
            deleted_quantity = self.deleted_items.with_entities(func.count().label('count')).filter(Remove_Laboratory_Item.remove_date.between(start_, end_)).first()[0]

            #get the name of the month
            month_name = check_date_format(start_).strftime("%B")

            month_detail.append([
                month_name,
                added_quantity,
                deleted_quantity
            ])
            #if period has done will break the while loop
            if done:
                break

        #### MAIN INFORMATION ####
        #rate of laboratory manager
        rate = float(self.rate)
        #number of lab, which responsible for them
        number_of_labs = len(self.work_on_labs)

        #### PRACTICAL EXPERIMENT APPROVE ####
        #APPROVED
        number_approved = self.all_request_confirmed.with_entities(func.count().label('count')).filter(and_(
        Confirm_Practical_Request.state == True)).first()[0]
        #NOT APPROVED
        number_not_approved = self.all_request_confirmed.with_entities(func.count().label('count')).filter(and_(
        Confirm_Practical_Request.state == False)).first()[0]
        #TOTAL EXPERIMENT
        total_experiment = number_approved + number_not_approved

        #### EXPERIMENT TYPE EXECUTED ####
        #dictionary to store experiment with number of executed 
        practical_experiments = []
        #get all experiment in the system 
        ministry_experiments = Practical_Experiment.query.with_entities(Practical_Experiment.id,Practical_Experiment.title).all()
        for experiment in ministry_experiments:
            number = self.all_request_confirmed.with_entities(func.count().label('count')).filter(and_(Confirm_Practical_Request.request_id == Practical_Experiment_Request.id,
            Practical_Experiment_Request.execute_date.between(from_, to_),
            Practical_Experiment_Request.practical_experiment_id == experiment.id,
            Practical_Experiment_Request.id == Confirm_Practical_Request.request_id,
            Confirm_Practical_Request.executed == True)).first()[0]
            practical_experiments.append({
                'experimentExecuted': experiment.title,
                'qunatity': number
            })  

        #### EXPERIMENT EXECUTED WITH DATE ####
        #dictionary to store experiment with number of executed 
        practical_experiments_execute_date = []
        #get number of executed for each experiement in specific date  
        experiments = self.all_request_confirmed.with_entities(
        Practical_Experiment_Request.execute_date,func.count(Practical_Experiment_Request.execute_date).label('count')).filter(
        and_(Confirm_Practical_Request.request_id == Practical_Experiment_Request.id,
        Practical_Experiment_Request.execute_date.between(from_, to_),
        Practical_Experiment_Request.id == Confirm_Practical_Request.request_id,
        Confirm_Practical_Request.executed == True)).group_by(
        Practical_Experiment_Request.execute_date).all()
        #change format to 2D array
        for experiment in experiments:
            practical_experiments_execute_date.append([experiment.execute_date,experiment.count])


        return {
           'startSemester': semester.start_date,
           'endSemester': semester.end_date,
           'rate': rate,
           'numberLabs': number_of_labs,
           'totalExperiments': total_experiment,
           'approvedExperiments': number_approved,
           'notApprovedExperiments': number_not_approved,
           'itemActivity': month_detail,
           'numberExecuteExperiment': practical_experiments,
           'numberExecutedDate': practical_experiments_execute_date
            }


class Science_Teacher(db.Model):
    __tablename__ = 'science_teacher'

    id = db.Column(db.Integer, db.ForeignKey('school_member.id'))
    school_id = db.Column(db.Integer, db.ForeignKey('school.id'))
    activate = db.Column(db.Boolean,nullable=False)
    
    __table_args__ = (
     db.PrimaryKeyConstraint(
        id, school_id,
         ),
     )

    teacher_course_relation = db.relationship('Course', secondary=Teach_Course,backref='teacher', lazy=True)
    school_relation = db.relationship('School', backref='science_teacher_member', lazy=True)
    school_member_relation = db.relationship('School_Member', backref='scince_teacher', lazy=True)
    experiment_relation = db.relationship('Practical_Experiment_Request', backref='created_by', lazy=True)



    def format_requirement(self):
        user = self.school_member.user
        return user.format_details()

    def format_create(self):
        courses = self.teach
        content = [c.format_create() for c in courses]
        return{
            'name': self.school_member.full_name_member(),
            'id': self.id,
            'path': '/science-teacher/{}'.format(self.id),
            'courses':content,
            'role': self.school_member.getRole() 
        }

    def insert(self):
        try:   
            db.session.add(self)
            db.session.commit()       
        except:
            db.session.rollback()
            abort(400, 'لا توجد مدرسة بهذا الرقم') 
    
    def update_activate(self,state):
        try:   
            self.activate = state
            db.session.commit()       
        except:
            db.session.rollback()
            abort(400, 'حدث خطأ, يرجى المحاولة لاحقاً') 

    def append_course(self,course):
        try:
            self.teach.append(course)
            db.session.commit()
        except:
            db.session.rollback()  
            abort(400, 'حدث خطأ, يرجى المحاولة لاحقاً')  

    def remove_course(self,course):
        try:
            self.teach.remove(course)
            db.session.commit()
        except:
            db.session.rollback()  
            abort(400, 'حدث خطأ, يرجى المحاولة لاحقاً')                   
    
    def close(self):
        db.session.close()

    def commit(self):
        db.session.commit()
   
    def initiate_new_experiment(self,practical_experiment_data,school):

        #check if any missing attribute 
        if not('experimentId' in practical_experiment_data and 'quantity' in practical_experiment_data and 'executeDate' in practical_experiment_data and 
        'classNo' in practical_experiment_data and 'labId' in practical_experiment_data):
            abort(400, 'لا يوجد قيم في الطلب')   

        experimentId = practical_experiment_data['experimentId']
        quantity = practical_experiment_data['quantity']
        executeDate = practical_experiment_data['executeDate']
        classNo = practical_experiment_data['classNo']
        labId = practical_experiment_data['labId']

        #check if any attribute is null 
        if experimentId is None or quantity is None or classNo is None or labId is None or executeDate == '':
            abort(400, ' الرجاء اكمال تسجيل البيانات المطلوبة')

        #check if the lab in his school or not 
        laboratory = None
        try:
            laboratory = Laboratory.query.with_entities(Laboratory.number,Laboratory.school_id).filter(and_(Laboratory.number==labId,Laboratory.school_id==school.id)).one()
        except NoResultFound: 
            abort(404, 'لا يوجد مختبر بهذا الرقم')

        #class number must be between 1 and 7
        if classNo < 1 or classNo > 7:
            abort(400, 'الرجاء اختيار وقت الحصة من الحصة الأولى الى الحصة السابعة')

        #check the format of date and return object of datetime
        date_obj = None
        try:
            date_obj = check_date_format(executeDate)
        except ValueError:
            abort(400, 'الرجاء كتابة التاريخ بالصيغة الصحيحة')

        #check if the time was chosen available
        requests = Practical_Experiment_Request.query.filter(and_(Practical_Experiment_Request.lab_id == laboratory.number, Practical_Experiment_Request.school_id == school.id,
        Practical_Experiment_Request.execute_date == executeDate,Practical_Experiment_Request.class_number==classNo)).all() 
        #by compare with other request in same time and class number, with check the state of confirming 
        for request in requests:
            if (request is not None and len(request.his_confirm) == 0 ) or (request is not None and len(request.his_confirm) > 0 and request.his_confirm[0].state == True):
                abort(400, 'الرجاء اختيار موعد اخر')

        practical_experiment = None  
        #check if the experiment in the system
        try:
            practical_experiment = Practical_Experiment.query.filter_by(id = experimentId).one()
        except NoResultFound: 
            abort(404, 'لا تجربة بهذا الرقم')

        #check if the science teacher has teach the course of this experiment
        try:
            course = practical_experiment.course
            own_courses = self.teach
            if course not in own_courses:
                abort(401, 'لا يمكن انشاء تجربة عملية لمواد غير مسموح بتدريسها')
        except AttributeError:
            abort(401, 'ليس لديك اي مواد لانشاء تجربة عليها')

        #check there any available item    
        new_quantity = None
        note = 'تم انشاء الطلب بنجاح, توجد كمية متوفرة'
        practical_items = practical_experiment.practical_item
        for item in practical_items:
            #multiple each item's quantity with the user input quantity to get the final quantity 
            new_quantity = item.quantity * quantity

            #get the laboratory item to check if science teacher can do the experiment or not
            summing = Laboratory_Item.query.with_entities(func.sum(Laboratory_Item.quantity).label('sum')).filter(and_(Laboratory_Item.school_id== school.id,
            Laboratory_Item.lab_id== laboratory.number,Laboratory_Item.ministry_item_id== item.ministry_item_id, Laboratory_Item.deleted == False,or_(
            Laboratory_Item.expire_date == None, request.execute_date < Laboratory_Item.expire_date))).first()[0]
            if summing is None or (summing is not None and summing < new_quantity):
                note = 'تم انشاء الطلب بنجاح, ولكن لا توجد كمية مناسبة لعمل التجربة العملية في الوقت الحالي الرجاء انتظار التأكيد من محضرؤ المختبر'

        #initiate new request 
        now = datetime.datetime.utcnow()
        new_request = None
        try:
            new_request = Practical_Experiment_Request(class_number=classNo,create_date=now,execute_date=executeDate,quantity=quantity,
            science_teacher_id=self.id,science_teacher_school_id=school.id,lab_id=laboratory.number,school_id=laboratory.school_id,practical_experiment_id=practical_experiment.id)
            new_request = new_request.insert()
        #Issue with foreign key or primary key 
        except IntegrityError:
            abort(500, 'يوجد خطأ في معلومات محضر المختبر او المختبر')
        #No table with same name 
        except NoSuchTableError:
            abort(500, 'حدث خطأ من السيرفر, يرجى المحاولة لاحقاً')
        #No column with same name
        except NoSuchColumnError:
            abort(500, 'حدث خطأ من السيرفر, يرجى المحاولة لاحقاً')
        #no connection with databse
        except UnboundExecutionError:
            abort(500, 'حدث خطأ من السيرفر, يرجى المحاولة لاحقاً')
        
        return new_request, note
               
    def edit_experiment(self,practical_experiment_data,school):

        #check if any missing attribute 
        if not('requestId' in practical_experiment_data and 'quantity' in practical_experiment_data and 'executeDate' in practical_experiment_data
         and 'classNo' in practical_experiment_data and 'labId' in practical_experiment_data):
            abort(400, 'لا يوجد قيم في الطلب')   
        
        requestId = practical_experiment_data['requestId']
        quantity = practical_experiment_data['quantity']
        executeDate = practical_experiment_data['executeDate']
        classNo = practical_experiment_data['classNo']
        labId = practical_experiment_data['labId']

        #check if any attribute is null 
        if requestId is None or quantity is None or classNo is None or labId is None or executeDate == '':
            abort(400, ' الرجاء اكمال تسجيل البيانات المطلوبة')

        #check the experiment request for him
        request = Practical_Experiment_Request.query.filter(and_(Practical_Experiment_Request.id == requestId, Practical_Experiment_Request.science_teacher_id == self.id , 
        Practical_Experiment_Request.science_teacher_school_id == self.school_id)).first_or_404(description='لا يوجد طلب تجربة عملية بهذا الرقم')
        #check the request has not confirm yet
        confirm = Confirm_Practical_Request.query.filter_by(request_id=request.id).first()
        if confirm is not None:
            abort(400, 'الطلب قد تم الرد عليه مسبقا, لا يمكن التعديل في الوقت الحالي')

        #check if there is any change 
        has_change = False
        #if ( and executeDate == request.execute_date and classNo == request.class_number and ):

        #convert Date to Datetime object (datetime.datetime.min.time() --> 00:00:00)
        date_db = datetime.datetime.combine(request.execute_date, datetime.datetime.min.time())
        #check the format of date
        execute_date_obj = check_date_format(executeDate)
        
        change_lab = False
        #check if the time of practical experiment has changed or laboratory has changed
        if classNo != request.class_number or execute_date_obj != date_db or labId != request.lab_id:
            has_change = True

            #check if the lab in his school or not 
            laboratory = Laboratory.query.filter(and_(Laboratory.number==labId,Laboratory.school_id==school.id)).first_or_404(description='لا يوجد مختبر بهذا الرقم')
            
            #class number must be between 1 and 7
            if classNo < 1 or classNo > 7:
                abort(400, 'الرجاء اختيار وقت الحصة من الحصة الأولى الى الحصة السابعة')

            #check if the time was chosen available
            requests = Practical_Experiment_Request.query.filter(and_(Practical_Experiment_Request.execute_date == executeDate,Practical_Experiment_Request.class_number==classNo,
            Practical_Experiment_Request.lab_id == laboratory.number, Practical_Experiment_Request.school_id == school.id)).all() 
            #by compare with other request in same time and class number, with check the state of confirming 
            for pre_request in requests:
                if (pre_request is not None and len(pre_request.his_confirm) == 0 ) or (pre_request is not None and len(pre_request.his_confirm) > 0 and pre_request.his_confirm[0].state == True):
                    abort(400, 'الرجاء اختيار موعد اخر')

            if labId != request.lab_id:
                change_lab = True
                request.update_laboratory(laboratory.number)
            if classNo != request.class_number or execute_date_obj != date_db:
                request.update_time(classNo,executeDate)

        note = 'تم تعديل الطلب بنجاح'
        if quantity != request.quantity or change_lab: 
            has_change = True
            #check there any available item    
            new_quantity = None
            note = 'تم تعديل الطلب بنجاح, توجد كمية متوفرة'
            practical_items = request.practical_experiment.practical_item
            for item in practical_items:
                #multiple each item's quantity with the user input quantity to get the final quantity 
                new_quantity = item.quantity * quantity
                #get the laboratory item to check if science teacher can do the experiment or not
                summing = Laboratory_Item.query.with_entities(func.sum(Laboratory_Item.quantity).label('sum')).filter(and_(Laboratory_Item.school_id== school.id,
                Laboratory_Item.lab_id== request.lab_id,Laboratory_Item.ministry_item_id== item.ministry_item_id, Laboratory_Item.deleted == False)).first()[0]
                if summing is None or (summing is not None and summing < new_quantity):
                    note = 'تم تعديل الطلب بنجاح, ولكن لا توجد كمية مناسبة لعمل التجربة العملية في الوقت الحالي الرجاء انتظار التأكيد من محضرؤ المختبر'
        
            if quantity != request.quantity:
                request.update_quantity(quantity)

        if not has_change:
            abort(400, 'لا يوجد اي تغيير')
        #initiate new request 
        request.commit()
        return request, note
        
    def evaluate_experiment(self,evaluate_data,experiment_id):
        #check if any missing attribute 
        if not('answers' in evaluate_data):
            abort(400, 'لا يوجد قيم في الطلب')   
        
        answers = evaluate_data['answers']
    
        #check if any attribute is null 
        if answers is None:
            abort(400, ' الرجاء اكمال تسجيل البيانات المطلوبة')
        #check from the id of confirm
        confirm = Confirm_Practical_Request.query.filter_by(request_id=experiment_id).first_or_404('لا توجد تجربة عملية للتقييم')
        #check if the experiement has been evaluated before
        if confirm.evaluated == True:
            abort(400, 'تم تقييم هذه التجربة من قبل')
        #check if the experiement has been executed or not
        if confirm.executed is None or confirm.executed == False:
            abort(401, 'يرجى تنفيذ التجربة حتى تتمكن من تقييم التجربة')
        #check from the evaluate type
        evaluate_type = Evaluate_Type.query.with_entities(Evaluate_Type.id).filter_by(title='evaluate_experiment').first_or_404('يرجى اختيار نوع التقييم المتاح في النظام')
        #get the time right now 
        tz = pytz.timezone('Asia/Riyadh')
        now = datetime.datetime.now(tz)
        #create new evaluate
        evaluate = Evaluate(date=now,evaluate_type=evaluate_type.id)
        evaluate = evaluate.insert()
        
        count_question = 0
        score = 0
        #submit the answers
        for answer in answers:
            #check from of data is exist
            if 'answerId' in answer and 'questionId' in answer:
                answer_id = answer['answerId']
                question_id = answer['questionId']
                if answer_id is not None and question_id is not None:
                    #check from the answer between one and two 
                    if answer_id < 0 or answer_id > 1:
                        abort(400, 'الرجاء اختيار واحدة من الاجوبة المتوفرة')
                    #check if the question is available 
                    question = Question.query.with_entities(Question.id).filter(Question.id==question_id,Question.evaluate_type == evaluate_type.id).first_or_404('لا يوجد سؤال بهذا الرقم')
                    ans = Answer(answer_value=answer_id,question_id=question.id,evaluate_id=evaluate.id)
                    ans.insert()
                    count_question += 1
                    score += answer_id
                else:
                    abort(400, ' الرجاء اكمال تسجيل البيانات المطلوبة')       
            else:
                abort(400, 'لا يوجد قيم في الطلب') 


        #get the total rate of the lab manager by educational supervisor to count the new rate 
        rates_edu = Evaluate_Laboratory_Manager.query.with_entities(func.sum(Evaluate_Laboratory_Manager.rate).label('sum'),func.count().label('count')).filter(and_(
        Evaluate_Laboratory_Manager.laboratory_manager_id == confirm.lab_manager_id,
        Evaluate_Laboratory_Manager.laboratory_manager_school_id == confirm.lab_manager_school_id)).first()

        #get the total rate of the lab manager by scince teacher to count the new rate 
        rates_science = Evaluate_Experiment.query.with_entities(func.sum(Evaluate_Experiment.rate).label('sum'),func.count().label('count')).filter(and_(
        Evaluate_Experiment.confirm_id == Confirm_Practical_Request.request_id, Confirm_Practical_Request.lab_manager_id == confirm.lab_manager_id,
        Confirm_Practical_Request.lab_manager_school_id == confirm.lab_manager_school_id)).first()

        #calcultae the result   
        result = (score / count_question) * RATE

        rate_number = 0.0
        rate_summing = 0.0
        #check if has a rate before or not 
        if rates_science.count > 0 and rates_science.sum is not None:
            rate_number += float(rates_science.count) 
            rate_summing += float(rates_science.sum) 

        if rates_edu.count > 0 and rates_edu.sum is not None:
            rate_number += float(rates_edu.count) 
            rate_summing += float(rates_edu.sum) 

        #calculate new rate 
        new_rate = (rate_summing + result ) / (rate_number + 1)
        #store the rate out of RATE (5.00) for the experiment and laboratory manager
        confirm.update_manager_rate(new_rate)
        evaluate_experiment = Evaluate_Experiment(id=evaluate.id,confirm_id=confirm.request_id,rate=result)
        evaluate_experiment.insert()
        #change the state of evaluated to true
        confirm.update_evaluated()
        #send back the confirm     
        return confirm  

                
class Educational_Supervisor(db.Model):
    __tablename__ = 'educational_supervisor'
    
    id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    area_id = db.Column(db.Integer, db.ForeignKey('area.id'))
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'))

    area = db.relationship('Area', backref='educational_supervisors', lazy='joined')
    visits = db.relationship('Visit', backref='educational_supervisor', lazy='selectin')


    def format(self):
        user = self.user
        return {
            'name': user.full_name(),
            'role': user.getRole(),
            'id': self.id,
            'phone': user.phone,
            'email': user.email,
            'courseId': self.course_id,
            'areaId': self.area_id,
            'cityId': self.area.city_id,
            'path': '/educational-supervisor/{}'.format(self.id)
        }

    def full_name(self):
        return self.user.full_name()

    def insert(self):
            try:   
                db.session.add(self)
                db.session.commit()
                return self       
            except:
                db.session.rollback()
                abort(400, 'حدث خطأ, يرجى المحاولة لاحقاً')
    
    def update_course(self,course_id):
        try:   
            self.course_id = course_id
            db.session.flush()       
        except:
            db.session.rollback()
            abort(400, 'لا توجد مادة بهذا الرقم') 
    
    def update_area(self,area_id):
        try:   
            self.area_id = area_id
            db.session.flush()       
        except:
            db.session.rollback()
            abort(400, 'لا توجد منطقة بهذا الرقم') 

    def filtering(request,educational_supervisors):

        #here we get the value from the request and we have the default value if there is not exist in the request 
        id = request.args.get('id')
        areaId = request.args.get('areaId')
        courseId = request.args.get('courseId')

        
        selection = educational_supervisors
        try:
            #check from the requiremnets then apply it on the selection (query)
            #filter the educational supervisors by id
            if id is not None and id != '':
                selection = selection.filter(Educational_Supervisor.id == id) 
            #filter the educational supervisors by course
            if courseId is not None and courseId != '' and courseId != 'all':
                selection = selection.filter(Educational_Supervisor.course_id == courseId) 
            #filter the educational supervisors by area
            if areaId is not None and areaId != '' and areaId != 'all':
                selection = selection.filter(Educational_Supervisor.area_id == areaId) 

            #return the filtering query 
            return selection.all() 
        #this type of excpetion, for to use the wrong type in query 
        except DataError:
            db.session.rollback()
            return []
    
    def commit(self):
        try:
            db.session.commit()
            return self
        except: 
            db.session.rollback()
            abort(400, 'حدث خطأ, يرجى المحاولة لاحقاً')

    def close(self):
        db.session.close()

    def append_visit(self,visit):
        try:
            self.visits.append(visit)
            db.session.commit()
        except:
            db.session.rollback()  
            abort(400, 'حدث خطأ, يرجى المحاولة لاحقاً')

    def initiate_visit(self,visit_data):
        #check if any missing attribute 
        if not('note' in visit_data and 'schoolId' in visit_data):
            abort(400, 'لا يوجد قيم في الطلب')   
        
        note = visit_data['note']
        schoolId = visit_data['schoolId']

        #check if any attribute is null 
        if schoolId is None:
            abort(400, ' الرجاء اكمال تسجيل البيانات المطلوبة')

        #chekc if he/she has a current visit has not closed yet
        visit = Visit.query.with_entities(Visit.id).filter(Visit.educational_supervisor_id == self.id, Visit.closed == False).first()
        if visit is not None:
            abort(401, 'يوجد زيارة حالية, يرجى اغلاقها')

        #check the school in the system and educational supervisor in same area of the school
        school = School.query.with_entities(School.id).filter(and_(School.id == schoolId,School.area_id == self.area_id)).first_or_404('لا توجد مدرسة في منطقتك الإدارية بهذا الرقم')

        #initialize  visit and return it 
        #get time zone of KSA
        tz = pytz.timezone('Asia/Riyadh')
        time = datetime.datetime.now(tz)

        visit = None
        try:
            visit = Visit(visit_date=time,note=note,school_id=school.id)
            visit = visit.insert()
            self.append_visit(visit)
        #Issue with foreign key or primary key
        except IntegrityError:
            abort(500, 'يوجد خطأ في معلومات محضر المختبر او المختبر')
        except DataError:
            abort(500, 'يوجد خطأ في صياغة التاريخ')
        #No table with same name 
        except NoSuchTableError:
            abort(500, 'حدث خطأ من السيرفر, يرجى المحاولة لاحقاً')
        #No column with same name
        except NoSuchColumnError:
            abort(500, 'حدث خطأ من السيرفر, يرجى المحاولة لاحقاً')
        #no connection with databse
        except UnboundExecutionError:
            abort(500, 'حدث خطأ من السيرفر, يرجى المحاولة لاحقاً')
        return visit

    def update_visit(self,visit_data):
        #check if any missing attribute 
        if not('note' in visit_data and 'schoolId' in visit_data and 'visitId' in visit_data):
            abort(400, 'لا يوجد قيم في الطلب')   
        
        id = visit_data['visitId']
        note = visit_data['note']
        schoolId = visit_data['schoolId']

        #check if any attribute is null 
        if schoolId is None or id is None:
            abort(400, ' الرجاء اكمال تسجيل البيانات المطلوبة')

        visit = Visit.query.filter(and_(Visit.id==id, Visit.educational_supervisor_id == self.id)).first_or_404(description='لا توجد زيارة بهذا الرقم')

        #check if any value modified
        if visit.school_id == schoolId:
            abort(400, 'لا يوجد اي تغيير')

        #check the school in the system and educational supervisor in same area of the school
        school = School.query.with_entities(School.id).filter(and_(School.id == schoolId,School.area_id == self.area_id)).first_or_404('لا توجد مدرسة بهذا الرقم')

        #check if the school has visit in the same date
        #school_has_visit = Visit.query.with_entities(Visit.id).filter(and_(Visit.school_id == school.id, Visit.visit_date == date)).first()
        #has_visit = Visit.query.with_entities(Visit.id).filter(and_(Visit.educational_supervisor_id == self.id, Visit.visit_date == date)).first()

        #if has_visit is not None or school_has_visit is not None:
        #    abort(400, 'توجد زيارة مسجلة في الموعد المحدد')

        return visit.update_visit(school.id)      

    def close_visit(self):

        #get the current visit
        visit = Visit.query.filter(and_(Visit.educational_supervisor_id == self.id,Visit.closed == False)).first_or_404(description='لا توجد زيارة حاليا لإغلاقها')
        return visit.close_visit()
     
    def evaluate_laboratory(self,evaluate_data,visit,laboratory_id):
        #check if any missing attribute 
        if not('answers' in evaluate_data):
            abort(400, 'لا يوجد قيم في الطلب')   
        
        answers = evaluate_data['answers']

        #check if any attribute is null 
        if answers is None:
            abort(400, ' الرجاء اكمال تسجيل البيانات المطلوبة')

        #check if the lab is exist or not
        lab = Laboratory.query.with_entities(Laboratory.number).filter(and_(Laboratory.school_id == visit.school_id,
        Laboratory.number == laboratory_id)).first_or_404('لا يوجد مختبر بهذا الرقم')

        evaluate = Evaluate_Laboratory.query.with_entities(Evaluate_Laboratory.id).filter(and_(Evaluate_Laboratory.visit_id==visit.id, Evaluate_Laboratory.school_id==visit.school_id,
        Evaluate_Laboratory.laboratory_id==laboratory_id)).first()
        #check if the educational supervisor evaluate the same lab in same visit 
        if evaluate is not None:
            abort(401, 'تم تقييم المختبر بالفعل')

        #check from the evaluate type
        evaluate_type = Evaluate_Type.query.with_entities(Evaluate_Type.id).filter_by(title='evaluate_laboratory').first_or_404('يرجى اختيار نوع التقييم المتاح في النظام')
        #get the time right now 
        tz = pytz.timezone('Asia/Riyadh')
        now = datetime.datetime.now(tz)
        #create new evaluate
        evaluate = Evaluate(date=now,evaluate_type=evaluate_type.id)
        evaluate = evaluate.insert()
        
        count_question = 0
        score = 0
        #submit the answers
        for answer in answers:
            #check from of data is exist
            if 'answerId' in answer and 'questionId' in answer:
                answer_id = answer['answerId']
                question_id = answer['questionId']
                if answer_id is not None and question_id is not None:
                    #check from the answer between one and two 
                    if answer_id < 0 or answer_id > 1:
                        abort(400, 'الرجاء اختيار واحدة من الاجوبة المتوفرة')
                    #check if the question is available 
                    question = Question.query.with_entities(Question.id).filter(Question.id==question_id,
                    Question.evaluate_type == evaluate_type.id).first_or_404('لا يوجد سؤال بهذا الرقم')
                    ans = Answer(answer_value=answer_id,question_id=question.id,evaluate_id=evaluate.id)
                    ans.insert()
                    count_question += 1
                    score += answer_id
                else:
                    abort(400, ' الرجاء اكمال تسجيل البيانات المطلوبة')       
            else:
                abort(400, 'لا يوجد قيم في الطلب') 

        #get the total rate of the lab to count the new rate 
        rates = Evaluate_Laboratory.query.with_entities(func.sum(Evaluate_Laboratory.rate).label('sum'),func.count().label('count')).filter(and_(
        Evaluate_Laboratory.school_id == visit.school_id,
        Evaluate_Laboratory.laboratory_id == laboratory_id)).first()
        #calcultae the result   
        result = (score / count_question) * RATE

        rate_number = 0.0
        rate_summing = 0.0
        #check if has a rate before or not 
        if rates.count > 0 and rates.sum is not None:
            rate_number = float(rates.count) 
            rate_summing = float(rates.sum) 

        #calculate new rate 
        new_rate = (rate_summing + result ) / (rate_number + 1)
        try:
            evaluate_laboratory = Evaluate_Laboratory(id=evaluate.id,laboratory_id=laboratory_id,school_id=visit.school_id,visit_id=visit.id,rate=result)
            evaluate_laboratory.insert()
        #Issue with foreign key or primary key
        except IntegrityError:
            abort(500, 'يوجد خطأ في معلومات محضر المختبر او المختبر')
        except DataError:
            abort(500, 'يوجد خطأ في صياغة التاريخ')
        #No table with same name 
        except NoSuchTableError:
            abort(500, 'حدث خطأ من السيرفر, يرجى المحاولة لاحقاً')
        #No column with same name
        except NoSuchColumnError:
            abort(500, 'حدث خطأ من السيرفر, يرجى المحاولة لاحقاً')
        #no connection with databse
        except UnboundExecutionError:
            abort(500, 'حدث خطأ من السيرفر, يرجى المحاولة لاحقاً')

        #store the average rate out of RATE (5.00) for laboratory 
        laboraotory = evaluate_laboratory.update_lab_rate(new_rate)
        #send back the laboraotory     
        return laboraotory  

    def evaluate_laboratory_manager(self,evaluate_data,visit,lab_manager_id):
        #check if any missing attribute 
        if not('answers' in evaluate_data):
            abort(400, 'لا يوجد قيم في الطلب')   
        
        answers = evaluate_data['answers']

        #check if any attribute is null 
        if answers is None:
            abort(400, ' الرجاء اكمال تسجيل البيانات المطلوبة')

        #check if the lab manager is exist or not
        user = Laboratory_Manager.query.with_entities(Laboratory_Manager.id).filter(and_(Laboratory_Manager.id==lab_manager_id, Laboratory_Manager.school_id == visit.school_id,
        Laboratory_Manager.activate == True)).first_or_404(description='لا يوجد محضر مختبر بهذا الرقم')

        evaluate = Evaluate_Laboratory_Manager.query.with_entities(Evaluate_Laboratory_Manager.id).filter(and_(Evaluate_Laboratory_Manager.visit_id==visit.id,
        Evaluate_Laboratory_Manager.laboratory_manager_id==lab_manager_id,
        Evaluate_Laboratory_Manager.laboratory_manager_school_id==visit.school_id)).first()
        #check if the educational supervisor evaluate the same lab manager in same visit 
        if evaluate is not None:
            abort(401, 'تم تقييم المختبر بالفعل')

        #check from the evaluate type
        evaluate_type = Evaluate_Type.query.with_entities(Evaluate_Type.id).filter_by(title='evaluate_laboratory_manager').first_or_404('يرجى اختيار نوع التقييم المتاح في النظام')
        #get the time right now 
        tz = pytz.timezone('Asia/Riyadh')
        now = datetime.datetime.now(tz)
        #create new evaluate
        evaluate = Evaluate(date=now,evaluate_type=evaluate_type.id)
        evaluate = evaluate.insert()
        
        count_question = 0
        score = 0
        #submit the answers
        for answer in answers:
            #check from of data is exist
            if 'answerId' in answer and 'questionId' in answer:
                answer_id = answer['answerId']
                question_id = answer['questionId']
                if answer_id is not None and question_id is not None:
                    #check from the answer between one and two 
                    if answer_id < 0 or answer_id > 1:
                        abort(400, 'الرجاء اختيار واحدة من الاجوبة المتوفرة')
                    #check if the question is available 
                    question = Question.query.with_entities(Question.id).filter(Question.id==question_id,Question.evaluate_type == evaluate_type.id).first_or_404('لا يوجد سؤال بهذا الرقم')
                    ans = Answer(answer_value=answer_id,question_id=question.id,evaluate_id=evaluate.id)
                    ans.insert()
                    count_question += 1
                    score += answer_id
                else:
                    abort(400, ' الرجاء اكمال تسجيل البيانات المطلوبة')       
            else:
                abort(400, 'لا يوجد قيم في الطلب') 

        #get the total rate of the lab manager by educational supervisor to count the new rate 
        rates_edu = Evaluate_Laboratory_Manager.query.with_entities(func.sum(Evaluate_Laboratory_Manager.rate).label('sum'),func.count().label('count')).filter(and_(
        Evaluate_Laboratory_Manager.laboratory_manager_id == lab_manager_id,
        Evaluate_Laboratory_Manager.laboratory_manager_school_id == visit.school_id)).first()

        #get the total rate of the lab manager by scince teacher to count the new rate 
        rates_science = Evaluate_Experiment.query.with_entities(func.sum(Evaluate_Experiment.rate).label('sum'),func.count().label('count')).filter(and_(
        Evaluate_Experiment.confirm_id == Confirm_Practical_Request.request_id, Confirm_Practical_Request.lab_manager_id == lab_manager_id,
        Confirm_Practical_Request.lab_manager_school_id == visit.school_id)).first()

        #calcultae the result   
        result = (score / count_question) * RATE

        rate_number = 0.0
        rate_summing = 0.0
        #check if has a rate before or not 
        if rates_science.count > 0 and rates_science.sum is not None:
            rate_number += float(rates_science.count) 
            rate_summing += float(rates_science.sum) 

        if rates_edu.count > 0 and rates_edu.sum is not None:
            rate_number += float(rates_edu.count) 
            rate_summing += float(rates_edu.sum) 

        #calculate new rate 
        new_rate = (rate_summing + result ) / (rate_number + 1)
        
        evaluate_laboratory_manager = Evaluate_Laboratory_Manager(id=evaluate.id,laboratory_manager_id=lab_manager_id,laboratory_manager_school_id=visit.school_id,
        visit_id=visit.id,rate=result)
        evaluate_laboratory_manager.insert()

        #store the average rate out of RATE (5.00) for laboratory 
        laboraotory_manager = evaluate_laboratory_manager.update_lab_mngr_rate(new_rate)
        #send back the laboraotory     
        return laboraotory_manager 


'''
        #select all request has not been confirmed yet. Using not exists into Confirm table 
        sub = ~ Confirm_Practical_Request.query.filter(Confirm_Practical_Request.request_id == Practical_Experiment_Request.id).exists()
        test = Practical_Experiment_Request.query.filter(and_(sub,Practical_Experiment_Request.school_id == school.id)).all()
'''

'''
            lab_item = Laboratory_Item.query.filter(and_(Laboratory_Item.school_id== school.id, Laboratory_Item.lab_id== laboratory.number,
            Laboratory_Item.ministry_item_id== item.ministry_item_id )).all()
'''
