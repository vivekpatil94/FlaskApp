from app import db
from flask import abort
from sqlalchemy import asc, desc, and_, or_, func
from app.component import getReasonAR,check_date_format,DATE_FORMAT,WILL_EXPIRE_DAY
from app.models.transactions import Practical_Experiment_Request,Confirm_Practical_Request
from sqlalchemy.exc import DataError,IntegrityError
from sqlalchemy.orm.exc import StaleDataError
import datetime,pytz

Manage_Laboratory = db.Table('manage_laboratory',
    db.Column('lab_manager_id', db.Integer),
    db.Column('lab_manager_school', db.Integer),
    db.Column('school_id', db.Integer),
    db.Column('lab_id', db.Integer),
    db.ForeignKeyConstraint( ('school_id', 'lab_id'), ('laboratory.school_id', 'laboratory.number'),  ),
    db.ForeignKeyConstraint( ('lab_manager_id','lab_manager_school'), ('laboratory_manager.id','laboratory_manager.school_id'),  ),    
)

Teach_Course = db.Table('teach_course',
    db.Column('course_id', db.Integer, db.ForeignKey('course.id'), nullable=False),
    db.Column('school_id', db.Integer),
    db.Column('science_teacher_id', db.Integer),
    db.ForeignKeyConstraint( ('school_id', 'science_teacher_id'), ('science_teacher.school_id', 'science_teacher.id')  )
)

Manage_Laboratory_Item = db.Table('manage_laboratory_item',
    db.Column('lab_manager_id', db.Integer),
    db.Column('lab_manager_school', db.Integer),
    db.Column('lab_item_id', db.Integer, db.ForeignKey('laboratory_item.id'), nullable=False),
    db.ForeignKeyConstraint( ('lab_manager_id','lab_manager_school'), ('laboratory_manager.id','laboratory_manager.school_id'),  ),    
)

class Course(db.Model):

    __tablename__ = 'course'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False,unique=True)

    practical_experiment_rel = db.relationship('Practical_Experiment', backref='course', lazy=True)
    teach_course_relation = db.relationship('Science_Teacher', secondary=Teach_Course,backref='teach', lazy=True)

    #user_id = db.Column(db.Integer, db.ForeignKey('system_administrator.id'), nullable=False)

    #from .users import Science_Teacher

    #teacher = db.relationship('Science_Teacher', backref='science_teacher', lazy=True)
       
    #'creator': self.creator.user.fname +" "+ self.creator.user.lname

    def format(self):
        return{
         'id': self.id,
         'name': self.name,
         'path': '/course/{}'.format(self.id)
         }

    def format_detail(self):
        practical_experiment = self.practical_experiment
        content = [exp.format_detail() for exp in practical_experiment]
        return {
         'id': self.id,
         'name': self.name,
         'path': '/course/{}'.format(self.id),
         'practicalExperiments': content
            }

    def format_detail_st(self):
        practical_experiment = self.practical_experiment
        content = [exp.format_detail_st() for exp in practical_experiment]
        return {
         'value': self.id,
         'label': self.name,
         'practicalExperiments': content
            }
    
    def format_create(self):
        return{
         'value': self.id,
         'label': self.name
         }

    def filtering(request,courses):

        #here we get the value from the request and we have the default value if there is not exist in the request 
        id = request.args.get('id')
        courseName = request.args.get('courseName')
        
        selection = courses
        try:
            #check from the requiremnets then apply it on the selection (query)
            #filter the course by id
            if id is not None and id != '':
                selection = selection.filter(Course.id == id) 
            #filter the course by name
            if courseName is not None and courseName != '':
                courseName = '%{}%'.format(courseName)
                selection = selection.filter(Course.name.ilike(courseName))

            #return the filtering query 
            return selection.all() 
        #this type of excpetion, for to use the wrong type in query 
        except DataError:
            db.session.rollback()
            return []

    def insert(self):
        try:   
            db.session.add(self)
            db.session.commit()  
            return self     
        except:
            db.session.rollback()
            abort(400, 'المادة مضافة بالفعل')

    def delete(self):
        try:   
            db.session.delete(self)
            db.session.commit()       
        except StaleDataError:
            abort(400, 'لا يمكن حذف المادة الدراسية, يوجد تجارب عملية لهذه المادة او معليمين يدرسون المادة')
        except:
            db.session.rollback()
            abort(400, 'حدث خطأ, يرجى المحاولة لاحقاً')
        finally:
            db.session.close()

    def update(self,newName):
        try:
            self.name = newName
            db.session.commit()
        except:
            db.session.rollback()   
            abort(400, 'المادة مضافة بالفعل')           

    def append(self,user):
        try:
            self.modifier.append(user)
            db.session.commit()
        except:
            db.session.rollback()  
            abort(400, 'حدث خطأ, يرجى المحاولة لاحقاً')                    
    
    def display_all_experiment(self):
        selection = self.practical_experiment
        content = [s.format() for s in selection]
        return content

    def close(self):
        db.session.close()

class Ministry_Item(db.Model):
    __tablename__ = 'ministry_item'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False,unique=True)
    unit = db.Column(db.String(20), nullable=False)    
    safety = db.Column(db.Boolean, nullable=False)

    practical_item_relation = db.relationship('Practical_Item', backref = 'ministry_item', lazy=True)
    lab_item_relation = db.relationship('Laboratory_Item', backref = 'ministry_item', lazy='joined')

    def format(self):
        #'creator': self.creator.user.fname +" "+ self.creator.user.lname
        return{
         'id': self.id,
         'name': self.name,
         'unit': self.unit,
         'safety': self.safety,
         'path': '/item/{}'.format(self.id)
         }
    
    def format_create(self):
        return{
         'value': self.id,
         'label': self.compound_name()
         }

    def compound_name(self):
        return '({} :وحدة القياس) {}'.format(self.unit,self.name)

    def filtering(request,items):

        #here we get the value from the request and we have the default value if there is not exist in the request 
        id = request.args.get('id')
        itemName = request.args.get('itemName')
        unitId = request.args.get('unitId')

        selection = items
        try:
            #check from the requiremnets then apply it on the selection (query)
            #filter the ministry item by id
            if id is not None and id != '':
                selection = selection.filter(Ministry_Item.id == id) 
            #filter the ministry item by name
            if itemName is not None and itemName != '':
                itemName = '%{}%'.format(itemName)
                selection = selection.filter(Ministry_Item.name.ilike(itemName))
            #filter the ministry item by unit
            if unitId is not None and unitId != '' and unitId.lower() != 'all':
                selection = selection.filter(Ministry_Item.unit == unitId.lower()) 

            #return the filtering query 
            return selection.all() 
        #this type of excpetion, for to use the wrong type in query 
        except DataError:
            db.session.rollback()
            return []

    def insert(self):
        try:   
            db.session.add(self)
            db.session.commit()    
            return self   
        except:
            db.session.rollback()
            abort(400, 'العهدة مضافة بالفعل')

    def delete(self):
        try:   
            db.session.delete(self)
            db.session.commit()       
        except StaleDataError:
            abort(400, 'لا يمكن حذف العهدة, هناك مختبرات تحتوي على هذه العهدة')
        except:
            db.session.rollback()
            abort(400, 'حدث خطأ, يرجى المحاولة لاحقاً')

    def update(self,name,unit,safety):
        try:
            self.name = name
            self.unit = unit
            self.safety = safety
            db.session.commit()
        except:
            db.session.rollback()   
            abort(400, 'العهدة مضافة بالفعل')          

    def append(self,user):
        try:
            self.modifier.append(user)
            db.session.commit()
        except:
            db.session.rollback()  
            abort(400, 'حدث خطأ, يرجى المحاولة لاحقاً')                    

    def close(self):
        db.session.close()

class Semester(db.Model):
    __tablename__ = 'semester'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
       
    def format(self):

        #selection = self.modifier
        #content = [s.format() for s in selection]

        return{
         'id': self.id,
         'title': self.title,
         'startDate': self.start_date,
         'endDate': self.end_date,
         'path': '/semester/{}'.format(self.id)
         }

    def insert(self):
        try:   
            db.session.add(self)
            db.session.commit()   
            return self    
        except:
            db.session.rollback()
            abort(400, 'الترم الدراسي مضافة بالفعل')

    def filtering(request,semester):

        #here we get the value from the request and we have the default value if there is not exist in the request 
        id = request.args.get('id')
        title = request.args.get('title')
        fromStartDate = request.args.get('fromStartDate')
        toStartDate = request.args.get('toStartDate')
        fromEndDate = request.args.get('fromEndDate')
        toEndDate = request.args.get('toEndDate')

        selection = semester
        try:
            #check from the requiremnets then apply it on the selection (query)
            #filter by id 
            if id is not None and id != '':
                selection = selection.filter(Semester.id == id)
            #filter by semester name 
            if title is not None and title != '':
                title = '%{}%'.format(title)
                selection = selection.filter(Semester.title.ilike(title))
            #filter the semester by start date 
            if fromStartDate is not None and fromStartDate != '':
                check_date_format(fromStartDate)
                selection = selection.filter(Semester.start_date >= fromStartDate)
            if toStartDate is not None and toStartDate != '': 
                check_date_format(toStartDate)
                selection = selection.filter(Semester.start_date <= toStartDate)
            #filter the semester by end date
            if fromEndDate is not None and fromEndDate != '':
                check_date_format(fromEndDate)
                selection = selection.filter(Semester.end_date >= fromEndDate)
            if toEndDate is not None and toEndDate != '':
                check_date_format(toEndDate)
                selection = selection.filter(Semester.end_date <= toEndDate)

            #return the filtering query 
            return selection.all()
        #this type of excpetion, for to use the wrong type in query 
        except DataError:
            db.session.rollback()
            return []
 
    def delete(self):
        try:   
            db.session.delete(self)
            db.session.commit()       
        except StaleDataError:
            abort(400, 'لا يمكن حذف الترم الدراسي, الترم الدراسي مربوط مع فعاليات الخاصة بختبرات المدارس')
        except:
            db.session.rollback()
            abort(400, 'حدث خطأ, يرجى المحاولة لاحقاً')

    def update(self,title,start_date,end_date):
        try:
            self.title = title
            self.start_date = start_date
            self.end_date = end_date
            db.session.commit()
        except:
            db.session.rollback()   
            abort(400, 'حدث خطأ, يرجى المحاولة لاحقاً')             

    def append(self,user):
        try:
            self.modifier.append(user)
            db.session.commit()
        except:
            db.session.rollback()  
            abort(400, 'حدث خطأ, يرجى المحاولة لاحقاً')                    

    def close(self):
        db.session.close()

class Practical_Experiment(db.Model):
    __tablename__ = 'practical_experiment'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False,unique=True)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False) 

    course_relation = db.relationship('Course', backref = 'practical_experiment', lazy=True)
    practical_experiment_request_relation = db.relationship('Practical_Experiment_Request',backref = 'practical_experiment',passive_deletes='all',lazy=True)
    
    practical_item_relation = db.relationship('Practical_Item', backref = 'practical_experiment',cascade="all,delete" ,lazy=True)


    def format(self):
        return{
         'id': self.id,
         'title': self.title,
         'courseName': self.course.name,
         'path': '/experiment/{}'.format(self.id)
         }

    def format_course(self):
        return{
         'value': self.id,
         'label': self.title
         }

    def format_detail(self):
        items = self.practical_item
        content = [item.format_create() for item in items]
        return {
         'id': self.id,
         'title': self.title,
         'course': self.course.format_create(),
         'items': content
        }
    
    def format_detail_st(self):
        items = self.practical_item
        content = [item.format_create() for item in items]
        return {
         'value': self.id,
         'label': self.title,
         'items': content
        }

    def filtering(request,experiment):

        #here we get the value from the request and we have the default value if there is not exist in the request 
        id = request.args.get('id')
        experimentName = request.args.get('experimentName')
        courseId = request.args.get('courseId')

        selection = experiment
        try:
            #check from the requiremnets then apply it on the selection (query)
            #filter the experiment by id
            if id is not None and id != '':
                selection = selection.filter(Practical_Experiment.id == id) 
            #filter the experiment by name
            if experimentName is not None and experimentName != '':
                experimentName = '%{}%'.format(experimentName)
                selection = selection.filter(Practical_Experiment.title.ilike(experimentName))
            #filter the experiment by course
            if courseId is not None and courseId != '' and courseId != 'all':
                selection = selection.filter(Practical_Experiment.course_id == courseId) 

            #return the filtering query 
            return selection.all() 
        #this type of excpetion, for to use the wrong type in query 
        except DataError:
            db.session.rollback()
            return []

    def insert(self):
        try:   
            db.session.add(self)
            db.session.commit()
            return self       
        except:
            db.session.rollback()
            abort(400, 'التجربة العملية مضافة بالفعل')

    def delete(self):
        try:   
            db.session.delete(self)
            db.session.commit()      
        except IntegrityError:
            abort(400, 'لا يمكن حذف التجربة, التجربة العملية قيد الاستخدام من قبل المدارس')
        except AssertionError:
            abort(400, 'لا يمكن حذف التجربة, التجربة العملية قيد الاستخدام من قبل المدارس')
        except:
            db.session.rollback()
            abort(400, 'حدث خطأ, يرجى المحاولة لاحقاً')
        finally:
            db.session.close()

    def update_title(self,title):
        try:
            self.title = title
            db.session.flush()
        except:
            db.session.rollback()   
            abort(400, 'التجربة العملية مضافة بالفعل') 

    def update_course_id(self,course_id):
        try:
            self.course_id = course_id
            db.session.flush()
        except:
            db.session.rollback()   
            abort(400, 'لا توجد مادة بهذا الرقم')           

    def append(self,user):
        try:
            self.modifier.append(user)
            db.session.commit()
        except:
            db.session.rollback()  
            abort(400, 'حدث خطأ, يرجى المحاولة لاحقاً')                    

    def close(self):
        db.session.close() 

class Practical_Item(db.Model):
    __tablename__ = 'practical_item'

    practical_experiment_id = db.Column(db.Integer, db.ForeignKey('practical_experiment.id'), nullable=False,primary_key=True)
    ministry_item_id = db.Column(db.Integer, db.ForeignKey('ministry_item.id'), nullable=False,primary_key=True)
    quantity = db.Column(db.Integer, nullable=False)

    practical_experiment_relation = db.relationship('Practical_Experiment', backref = 'practical_item', lazy=True)
    ministry_item_relation = db.relationship('Ministry_Item', backref = 'practical_item', lazy=True)

       
    def format(self):
        return{
         'experimentId': self.practical_experiment_id,
         'itemId': self.ministry_item_id}

    def format_create(self):
        return{
         'value': self.ministry_item_id,
         'label': self.ministry_item.compound_name(),
         'quantity': self.quantity}

    def insert(self):
        try:   
            db.session.add(self)
            db.session.flush()       
        except:
            db.session.rollback()
            abort(400, 'العهدة العلمية مضافة بالفعل')
    
    def update_quantity(self,quantity):
        try:
            self.quantity = quantity
            db.session.flush()
        except:
            db.session.rollback()   
            abort(400, 'حدث خطأ, يرجى المحاولة لاحقاً')

    def delete(self):
        try:   
            db.session.delete(self)
            db.session.flush()       
        except StaleDataError:
            abort(400, 'لا يمكن حذف العهدة, يوجد تجارب تستخدم هذه العهد')
        except:
            db.session.rollback()
            abort(400, 'حدث خطأ, يرجى المحاولة لاحقاً')   

    def close(self):
        db.session.close()     

class City(db.Model):
    __tablename__ = 'city'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False,unique=True)
   
    area_relation = db.relationship('Area', backref='city', cascade="all,delete" ,lazy=True)

    def format(self):
        return{
         'id': self.id,
         'name': self.name,
         'path': '/city/{}'.format(self.id)
         }

    def format_detail(self):
        areas = self.areas
        content = [area.format_create() for area in areas]

        return{
         'id': self.id,
         'name': self.name,
         'areas': content
         }

    def format_create(self):
        areas = self.areas
        content = [area.format_create() for area in areas]

        return{
         'value': self.id,
         'label': self.name,
         'areas': content
         }

    def format_c(self):
        return{
         'value': self.id,
         'label': self.name
         }

    def filtering(request,cities):

        #here we get the value from the request and we have the default value if there is not exist in the request 
        id = request.args.get('id')
        cityName = request.args.get('cityName')
        
        selection = cities
        try:
            #check from the requiremnets then apply it on the selection (query)
            #filter the city by id
            if id is not None and id != '':
                selection = selection.filter(City.id == id) 
            #filter the city by name
            if cityName is not None and cityName != '':
                cityName = '%{}%'.format(cityName)
                selection = selection.filter(City.name.ilike(cityName))

            #return the filtering query 
            return selection.all() 
        #this type of excpetion, for to use the wrong type in query 
        except DataError:
            db.session.rollback()
            return []

    def insert(self):
        try:   
            db.session.add(self)
            db.session.commit()      
            return self 
        except:
            db.session.rollback()
            abort(400, 'المدينة مضافة بالفعل')

    def delete(self):
        try:              
            db.session.delete(self)
            db.session.commit()       
        except IntegrityError:
            abort(400, 'لا يمكن هذه المدينة, يوجد مدارس او مشرفين تربويين مرتبطين مع هذه المدينة')
        except:
            db.session.rollback()
            abort(400, 'حدث خطأ, يرجى المحاولة لاحقاً')
        finally:
            db.session.close()

    def update_name(self,name):
        try:
            self.name = name
            db.session.flush()
        except:
            db.session.rollback()   
            abort(400, ' المدينة مضافة بالفعل') 

    def append(self,user):
        try:
            self.modifier.append(user)
            db.session.commit()
        except:
            db.session.rollback()  
            abort(400, 'حدث خطأ, يرجى المحاولة لاحقاً')                             

    def close(self):
        db.session.close() 

    def commit(self):
        db.session.commit() 

class Area(db.Model):
    __tablename__ = 'area'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)

    city_id = db.Column(db.Integer, db.ForeignKey('city.id'), nullable=False)

    city_relation = db.relationship('City', backref='areas', lazy=True)
    school_relation = db.relationship('School', backref='area', lazy=True)


    def format(self):
        return{
         'id': self.id,
         'name': self.name
         }
    
    def format_create(self):
        return{
         'value': self.id,
         'label': self.name
         }

    def format_city(self):
        return{
         'city': self.city.format_c(),
         'area': self.format_create()
         }

    def insert(self):
        try:   
            db.session.add(self)
            db.session.flush()       
        except:
            db.session.rollback()
            abort(400, 'المنطقة مضافة بالفعل')
    
    def update(self,name):
        try:   
            self.name = name
            db.session.flush()       
        except:
            db.session.rollback()
            abort(400, 'لا توجد مدينة')

    def delete(self):
        try:   
            db.session.delete(self)
            db.session.flush()   
        except IntegrityError:
            abort(400, 'لا يمكن حذف المنطقة, يوجد مدارس او مشرفين تربويين مرتبطين مع هذه المنطقة')
        except:
            db.session.rollback()
            abort(400, 'حدث خطأ, يرجى المحاولة لاحقاً')                         

    def close(self):
        db.session.close() 

class School(db.Model):
    __tablename__ = 'school'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    school_manager_id = db.Column(db.Integer, db.ForeignKey('school_manager.id'), nullable=False, unique=True)
    area_id = db.Column(db.Integer, db.ForeignKey('area.id'), nullable=False)

    school_manager_relation = db.relationship('School_Manager', backref='his_school', lazy=True)
    lab_manager_relation = db.relationship('Laboratory_Manager', backref='his_school', lazy=True)
    science_teacher_relation = db.relationship('Science_Teacher', backref='his_school', lazy=True)
    laboratories = db.relationship('Laboratory', backref='inSchool', lazy='dynamic')
    lab_managers = db.relationship('Laboratory_Manager', backref='inSchool', lazy='dynamic')
    school_relation = db.relationship('Area', backref='schools', lazy=True)
    invite_relation = db.relationship('Invitation', backref='school', lazy=True)

    def format_details(self):
        return{
         'id': self.id,
         'name': self.name,
         'schoolManager': self.manager.format(),
         'location': self.area.format_city()
         }

    def format(self):
        return{
         'id': self.id,
         'name': self.name,
         'path': '/school/{}'.format(self.id)
         }

    def format_create(self):
        return{
         'value': self.id,
         'label': self.name
         }

    def insert(self):
        try:   
            db.session.add(self)
            db.session.commit()       
        except:
            db.session.rollback()
            abort(400, 'المدرسة قد نشأت  من قبل')
        finally:
            db.session.close()
    
    def update(self,name,area):
        try:
            self.name = name
            self.area_id = area
            db.session.commit()
        except:
            db.session.rollback()   
            abort(400, ' المدرسة مضافة بالفعل') 

    def delete(self):
        try:   
            db.session.delete(self)
            db.session.commit()       
        except:
            db.session.rollback()
            abort(400, 'المدرسة محذوفة بالفعل')
        finally:
            db.session.close() 

    def create_lab(self,lab_id):
        lab = Laboratory(number=lab_id,school_id=self.id)
        lab.insert()
        return lab                          

    def close(self):
        db.session.close() 

class Laboratory(db.Model):
    __tablename__ = 'laboratory'

    number = db.Column(db.Integer, primary_key=True)
    school_id = db.Column(db.Integer, db.ForeignKey('school.id'), primary_key=True)
    rate = db.Column(db.Numeric(precision=3,scale=2), default= 0.00)

    school_relation = db.relationship('School', backref='own_labs', lazy='selectin')
    manager_manage_lab_relation = db.relationship('Laboratory_Manager', secondary=Manage_Laboratory,backref='work_on_labs', lazy=True)
    #lab_item_relation = db.relationship('Laboratory_Item', backref='laboratory', lazy=True)
    lab_item_dynamic = db.relationship('Laboratory_Item', backref='laboratory', lazy='dynamic')
    requests = db.relationship('Practical_Experiment_Request', backref='laboratory', lazy='dynamic')



    def format_id(self):
        return{
         'id': self.number,
         'path': '/laboratory/{}'.format(self.number)
         }

    def format(self):
        selection = self.manager
        content = [s.format_label_value() for s in selection]
        return{
         'id': self.number,
         'rate': float(self.rate),
         'path': '/laboratory/{}'.format(self.number),
         'labManagers': content
         }

    def format_create(self):
        return{
         'value': self.number,
         'label': self.number
         }
        
    def format_lab_manager(self):
        lab_mngrs = self.manager
        lab_mngrs_content = [lab_mngr.format_label_value() for lab_mngr in lab_mngrs] 
        return{
         'id': self.number,
         'laboratoryManagers': lab_mngrs_content,
         'path': '/school-laboratory/{}'.format(self.number)
         }

    def format_evaluate(self):
        selection = self.manager
        content = [s.format_label_value() for s in selection]
        return{
         'id': self.number,
         'rate': float(self.rate),
         'path': '/visit/current/laboratory/{}'.format(self.number),
         'labManagers': content
         }

    def insert(self):
        try:   
            db.session.add(self)
            db.session.commit()       
        except:
            db.session.rollback()
            abort(400, ' لديك مختبر مسجل بالفعل')
    
    def update(self,name,area):
        try:
            self.name = name
            self.area_id = area
            db.session.commit()
        except:
            db.session.rollback()   
            abort(400, ' المختبر مضافة بالفعل') 
        finally:
            db.session.close()
    
    def update_rate(self,new_rate):
        try:
            self.rate = new_rate
            db.session.flush()
        except:
            db.session.rollback()   
            abort(400, ' المختبر مضافة بالفعل') 

    def append_manager(self,user):
        try:
            self.manager.append(user)
            db.session.commit()
            return self
        except:
            db.session.rollback()  
            abort(400, 'حدث خطأ, يرجى المحاولة لاحقاً') 

    def remove_manager(self,user):
        try:
            self.manager.remove(user)
            db.session.commit()
        except:
            db.session.rollback()  
            abort(400, 'حدث خطأ, يرجى المحاولة لاحقاً') 

    def append_item(self,item):
        try:
            self.lab_items.append(item)
            db.session.commit()
            return item
        except:
            db.session.rollback()  
            abort(400, 'حدث خطأ, يرجى المحاولة لاحقاً') 

    def remove_item(self,user):
        try:
            self.lab_items.remove(item)
            db.session.commit()
        except:
            db.session.rollback()  
            abort(400, 'حدث خطأ, يرجى المحاولة لاحقاً')                      

    def delete(self):
        try:   
            db.session.delete(self)
            db.session.commit()       
        except:
            db.session.rollback()
            abort(400, 'المختبر محذوفة بالفعل')
        finally:
            db.session.close()    

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
        
        
        #### LABORATORY ITEM ####
        expire_soon = (time + datetime.timedelta(days=WILL_EXPIRE_DAY)).strftime(DATE_FORMAT)
        #VALID
        number_valid = self.lab_item_dynamic.with_entities(func.count().label('count')).filter(and_(Laboratory_Item.added_date.between(from_, to_),(
        or_(Laboratory_Item.expire_date > expire_soon,
        Laboratory_Item.expire_date == None)), Laboratory_Item.deleted == False)).first()[0]
        #WILL-EXPIRE
        number_will_expire = self.lab_item_dynamic.with_entities(func.count().label('count')).filter(and_(Laboratory_Item.added_date.between(from_, to_),
        Laboratory_Item.expire_date > now,
        Laboratory_Item.expire_date <= expire_soon, Laboratory_Item.deleted == False)).first()[0]
        #EXPIRED
        number_expired = self.lab_item_dynamic.with_entities(func.count().label('count')).filter(and_(Laboratory_Item.added_date.between(from_, to_),
        Laboratory_Item.expire_date <= now, Laboratory_Item.deleted == False)).first()[0]

        #### PRACTICAL EXPERIMENT REQUEST ####    
        #EXECUTED
        number_executed = self.requests.with_entities(func.count().label('count')).filter(and_(Practical_Experiment_Request.execute_date.between(from_, to_),
        Practical_Experiment_Request.id == Confirm_Practical_Request.request_id,
        Confirm_Practical_Request.executed == True)).first()[0]
        #NOT EXECUTED
        number_not_executed = self.requests.with_entities(func.count().label('count')).filter(and_(Practical_Experiment_Request.execute_date.between(from_, to_),
        Practical_Experiment_Request.id == Confirm_Practical_Request.request_id,
        Confirm_Practical_Request.executed == False)).first()[0]
        #WAITING
        number_waiting = self.requests.with_entities(func.count().label('count')).filter(and_(Practical_Experiment_Request.execute_date.between(from_, to_),
        Practical_Experiment_Request.id == Confirm_Practical_Request.request_id,
        Confirm_Practical_Request.executed == None)).first()[0]

        #### EXPERIMENT TYPE EXECUTED ####
        #dictionary to store experiment with number of executed 
        practical_experiments = []
        #get all experiment in the system 
        ministry_experiments = Practical_Experiment.query.with_entities(Practical_Experiment.id,Practical_Experiment.title).all()
        for experiment in ministry_experiments:
            number = self.requests.with_entities(func.count().label('count')).filter(and_(Practical_Experiment_Request.execute_date.between(from_, to_),
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
            number = self.lab_item_dynamic.with_entities(func.count().label('count')).filter(and_(Laboratory_Item.added_date.between(from_, to_),
            Laboratory_Item.ministry_item_id == item.id)).first()[0]
            safety_items.append({
                'safetyItem': item.name,
                'quantity': number
            })

        #### EXPERIMENT EXECUTED WITH DATE ####
        #dictionary to store experiment with number of executed 
        practical_experiments_execute_date = []
        #get number of executed for each experiement in specific date  
        experiments = self.requests.with_entities(
        Practical_Experiment_Request.execute_date,func.count(Practical_Experiment_Request.execute_date).label('count')).filter(
        and_(Practical_Experiment_Request.execute_date.between(from_, to_),
        Practical_Experiment_Request.id == Confirm_Practical_Request.request_id,
        Confirm_Practical_Request.executed == True)).group_by(
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

    def commit(self):
        db.session.commit() 
   
    def close(self):
        db.session.close()     

class Laboratory_Item(db.Model):
    __tablename__ = 'laboratory_item'

    id = db.Column(db.Integer, primary_key=True)
    quantity = db.Column(db.Integer, nullable=False)
    added_date = db.Column(db.Date, nullable=False)
    expire_date = db.Column(db.Date)
    lab_id = db.Column(db.Integer)
    school_id = db.Column(db.Integer)
    lab_manager_id = db.Column(db.Integer,nullable=False)
    lab_manager_school = db.Column(db.Integer,nullable=False)
    ministry_item_id = db.Column(db.Integer, db.ForeignKey('ministry_item.id'), nullable=False)
    deleted = db.Column(db.Boolean,nullable=False,default=False)

    __table_args__ = (
     db.ForeignKeyConstraint( ('school_id', 'lab_id'), ('laboratory.school_id', 'laboratory.number'),  ),
     db.ForeignKeyConstraint( ('lab_manager_id','lab_manager_school'), ('laboratory_manager.id','laboratory_manager.school_id'),  ),
     )
    
    laboratory_relation = db.relationship('Laboratory', backref='lab_items', lazy=True)
    laboratory_deleted_item_relation = db.relationship('Remove_Laboratory_Item', backref='real_obj', lazy=True)
    manage_item_used_relation = db.relationship('Item_Used', backref='lab_item', lazy=True)


    def format(self):
        ministry_item = self.ministry_item
        return{
         'id': self.id,
         'name': ministry_item.compound_name(),
         'safety': ministry_item.safety,
         'quantity': self.quantity,
         'addedDate': self.added_date,
         'expireDate': self.expire_date,
         'labId': self.lab_id,
         'path': '/school-laboratory/{}/item/{}'.format(self.lab_id,self.id)
         }

    def format_create(self):
        return {
            'value': self.id,
            'label': self.ministry_item.compound_name()
        }

    def filtering(request,selection):

        #here we get the value from the request and we have the default value if there is not exist in the request 
        id = request.args.get('id')
        itemId = request.args.get('itemId')
        expDateAsc = request.args.get('expDateAsc')
        expDateDesc = request.args.get('expDateDesc')
        fromAddedDate = request.args.get('fromAddedDate')
        toAddedDate = request.args.get('toAddedDate')
        fromExpireDate = request.args.get('fromExpireDate')
        toExpireDate = request.args.get('toExpireDate')
        hasExpireDate = request.args.get('hasExpireDate')
        expired = request.args.get('expired')
        willExpire = request.args.get('willExpire')
        valid = request.args.get('valid')

        expire_selection = selection
        
        try:
            #check from the requiremnets then apply it on the selection (query)
            #filter the item by id
            if id is not None and id != '':
                selection = selection.filter(Laboratory_Item.id == id) 
            #filter the item by ministry item id 
            if itemId is not None and itemId != '' and itemId.lower() != 'all':
                selection = selection.filter(Laboratory_Item.ministry_item_id == itemId)
            #filter the item by has expire date only or has no expire date only
            if hasExpireDate is not None and hasExpireDate != '':
                if hasExpireDate.lower() == 'true':
                    selection = selection.filter(Laboratory_Item.expire_date != None)
                if hasExpireDate.lower() == 'false':
                    selection = selection.filter(Laboratory_Item.expire_date == None)
            #filter the item by created date range
            if fromAddedDate is not None and fromAddedDate != '':
                check_date_format(fromAddedDate)
                selection = selection.filter(Laboratory_Item.added_date >= fromAddedDate)
            #filter the item by created date range
            if toAddedDate is not None and toAddedDate != '':
                check_date_format(toAddedDate)
                selection = selection.filter(Laboratory_Item.added_date <= toAddedDate)
            #filter the item by expire date range 
            if fromExpireDate is not None and fromExpireDate != '':
                check_date_format(fromExpireDate)
                selection = selection.filter(Laboratory_Item.expire_date >= fromExpireDate)
            #filter the item by expire date range 
            if toExpireDate is not None and toExpireDate != '':
                check_date_format(toExpireDate)
                selection = selection.filter(Laboratory_Item.expire_date <= toExpireDate)
            #filter the item by ascending
            if expDateAsc is not None and expDateAsc == 'true':
                selection = selection.order_by(Laboratory_Item.expire_date.asc())
            #filter the item by descending
            if expDateDesc is not None and expDateDesc == 'true':
                selection = selection.order_by(Laboratory_Item.expire_date.desc())

            #to deal with data as list 
            copy_selection = []
            key = False

            #get time zone of KSA right now 
            tz = pytz.timezone('Asia/Riyadh')
            time = datetime.datetime.now(tz)
            #convert to needed format
            now = time.strftime(DATE_FORMAT)
            expire_soon = (time + datetime.timedelta(days=WILL_EXPIRE_DAY)).strftime(DATE_FORMAT)

            #filter the item was expired
            if expired is not None and expired == 'true':
                key = True
                temp_selection = selection.filter(Laboratory_Item.expire_date <= now).all()
                copy_selection.extend(temp_selection)
            #filter the item will expire within these days (7 DAYs)
            if willExpire is not None and willExpire == 'true':
                key = True
                temp_selection = selection.filter(and_(Laboratory_Item.expire_date > now, Laboratory_Item.expire_date <= expire_soon)).all()
                copy_selection.extend(temp_selection)
            #filter the item is valid
            if valid is not None and valid == 'true':
                key = True
                temp_selection = selection.filter(or_(Laboratory_Item.expire_date > expire_soon, Laboratory_Item.expire_date == None)).all()
                copy_selection.extend(temp_selection)

            expMsg = ''
            expire_selection = expire_selection.with_entities(Laboratory_Item.id).filter(or_(and_(Laboratory_Item.expire_date > now, Laboratory_Item.expire_date <= expire_soon), 
            Laboratory_Item.expire_date <= now)).first()

            if expire_selection is not None:
                expMsg = 'يوجد عهد سوف تنتهي قريباً او منتهية الصلاحية'

            #return the filtering query 
            if copy_selection is not None and key:
                return copy_selection, expMsg
            return selection.all(), expMsg

        #this type of excpetion, for to use the wrong type in query 
        except DataError:
            db.session.rollback()   
            return [], expMsg

    def use(self, quantity, now):# may 30 - 30
        #minus the quantity of this item and the quantity needed
        remain = self.quantity - quantity
        #if result more than 0, return zero
        if remain > 0:
            self.quantity = remain
            db.session.flush()
            return 0, {'id': self.id, 'quantity': quantity}
        #if result less or equal 0, return the value in case 30 - 30 = 0 the remaining 0 will return 0 i merge them in one condition cause i need to remove them from the available item
        elif remain <= 0:
            quantity_used = self.quantity 
            self.quantity = 0
            db.session.flush()
            removed_item = Remove_Laboratory_Item(note='تم استخدامه في التجارب العملية',reason='used',
            remove_date=now,lab_item=self.id,lab_manager_id=self.lab_manager_id,lab_manager_school=self.lab_manager_school)
            removed_item.insert()
            self.update_state()
            return remain * (-1), {'id': self.id, 'quantity': quantity_used}

    def insert(self):
        try:   
            db.session.add(self)
            db.session.commit()       
        except:
            db.session.rollback()
            abort(400, 'العهدة مضافة بالفعل')

    def delete(self):
        try:   
            db.session.delete(self)
            db.session.commit()       
        except:
            db.session.rollback()
            abort(400, 'العهدة محذوفة بالفعل')

    def update(self,quantity,expire_date):
        try:
            self.quantity += quantity
            self.expire_date = expire_date
            db.session.commit()
        except:
            db.session.rollback()   
            abort(400, 'حدث خطأ, يرجى المحاولة لاحقاً') 
    
    def update_quantity(self,quantity):
        try:
            self.quantity = quantity
            db.session.flush()
        except:
            db.session.rollback()   
            abort(400, 'حدث خطأ, يرجى المحاولة لاحقاً') 

    def update_state(self):
        try:
            self.deleted = not (self.deleted)
            db.session.commit()
        except:
            db.session.rollback()   
            abort(400, 'حدث خطأ, يرجى المحاولة لاحقاً') 

    def append_manager(self,user):
        try:
            self.lab_manager_modified.append(user)
            db.session.commit()
            return self
        except:
            db.session.rollback()  
            abort(400, 'حدث خطأ, يرجى المحاولة لاحقاً')            

    def retrieve(self,old_quantity):
        try:
            if self.deleted: 
                self.laboratory_item_removed[0].delete()
                self.deleted = False  
                
            self.quantity += old_quantity
        except IndexError:
            db.session.rollback()   
            abort(400, 'لا يوجد عهد محذوفة') 
        except:
            db.session.rollback()   
            abort(400, 'حدث خطأ, يرجى المحاولة لاحقاً') 
        
class Remove_Laboratory_Item(db.Model):
    __tablename__ = 'remove_laboratory_item'

    note = db.Column(db.String(250), nullable=False)
    reason = db.Column(db.String(25), nullable=False)
    remove_date = db.Column(db.Date, nullable=False)
    lab_item = db.Column(db.Integer, db.ForeignKey('laboratory_item.id'), nullable=False,primary_key=True)
    lab_manager_id = db.Column(db.Integer,nullable=False,primary_key=True)
    lab_manager_school = db.Column(db.Integer,nullable=False,primary_key=True)

    __table_args__ = (
     db.ForeignKeyConstraint( ('lab_manager_id','lab_manager_school'), ('laboratory_manager.id','laboratory_manager.school_id'),  ),
     )
    
    laboratory_item_relation = db.relationship('Laboratory_Item', backref='laboratory_item_removed', lazy=True)


    def format(self):
        #selection = self.modifier
        #content = [s.format() for s in selection]
        return{
         'id': self.lab_item,
         'name': self.real_obj.ministry_item.compound_name(),
         'note': self.note,
         'reason': getReasonAR(self.reason),
         'removeDate': self.remove_date
         }

    def filtering(request,lab_items):

        #here we get the value from the request and we have the default value if there is not exist in the request 
        id = request.args.get('id')
        itemId = request.args.get('itemId')
        fromDeleteDate = request.args.get('fromDeleteDate')
        toDeleteDate = request.args.get('toDeleteDate')
        lost = request.args.get('lost')
        broke = request.args.get('broke')
        expired = request.args.get('expired')
        tainted = request.args.get('tainted')
        used = request.args.get('used')

        selection = lab_items
        try:
            #check from the requiremnets then apply it on the selection (query)
            #filter the item by id
            if id is not None and id != '':
                selection = selection.filter(Remove_Laboratory_Item.lab_item == id) 
            #filter the item by ministry item id 
            if itemId is not None and itemId != '' and itemId.lower() != 'all':
                selection = selection.filter(and_(Remove_Laboratory_Item.lab_item == Laboratory_Item.id, Laboratory_Item.ministry_item_id == itemId))
            #filter the item by delete date range
            if fromDeleteDate is not None and fromDeleteDate != '':
                check_date_format(fromDeleteDate)
                selection = selection.filter(Remove_Laboratory_Item.remove_date >= fromDeleteDate) 
            #filter the item by delete date range
            if toDeleteDate is not None and toDeleteDate != '':
                check_date_format(toDeleteDate)
                selection = selection.filter(Remove_Laboratory_Item.remove_date <= toDeleteDate) 

            #to deal with data as list 
            copy_selection = []
            key = False

            #filter the item by reason 'Lost'
            if lost is not None and lost == 'true':
                key = True
                temp_selection = selection.filter(Remove_Laboratory_Item.reason == 'lost').all()
                copy_selection.extend(temp_selection)
            #filter the item by reason 'Lost'
            if broke is not None and broke == 'true':
                key = True
                temp_selection = selection.filter(Remove_Laboratory_Item.reason == 'broke').all()
                copy_selection.extend(temp_selection)
            #filter the item by reason 'Lost'
            if expired is not None and expired == 'true':
                key = True
                temp_selection = selection.filter(Remove_Laboratory_Item.reason == 'expired').all()
                copy_selection.extend(temp_selection)
            #filter the item by reason 'Lost'
            if tainted is not None and tainted == 'true':
                key = True
                temp_selection = selection.filter(Remove_Laboratory_Item.reason == 'tainted').all()
                copy_selection.extend(temp_selection)
            #filter the item by reason 'Lost'
            if used is not None and used == 'true':
                key = True
                temp_selection = selection.filter(Remove_Laboratory_Item.reason == 'used').all()
                copy_selection.extend(temp_selection)

            #return the filtering query 
            if copy_selection is not None and key:
                return copy_selection
            return selection.all()
            
        #this type of excpetion, for to use the wrong type in query 
        except DataError:
            db.session.rollback()
            return []

    def insert(self):
        try:   
            db.session.add(self)
            db.session.commit()       
        except:
            db.session.rollback()
            abort(400, 'العهدة محذوفة بالفعل')

    def delete(self):
        try:   
            db.session.delete(self)
            db.session.flush()       
        except:
            db.session.rollback()
            abort(400, 'العهدة محذوفة بالفعل')


Manage_Semester = db.Table('manage_semester',
    db.Column('user_id', db.Integer, db.ForeignKey('system_administrator.id'), nullable=False),
    db.Column('semester_id', db.Integer, db.ForeignKey('semester.id'), nullable=False)
)

Manage_Ministry_Item = db.Table('manage_ministry_item',
    db.Column('user_id', db.Integer, db.ForeignKey('system_administrator.id'), nullable=False),
    db.Column('ministry_item_id', db.Integer, db.ForeignKey('ministry_item.id'), nullable=False)
)

Manage_Course = db.Table('manage_course',
    db.Column('user_id', db.Integer, db.ForeignKey('system_administrator.id'), nullable=False),
    db.Column('course_id', db.Integer, db.ForeignKey('course.id'), nullable=False)
)

Manage_Practical_Experiment = db.Table('manage_practical_experiment',
    db.Column('user_id', db.Integer, db.ForeignKey('system_administrator.id'), nullable=False),
    db.Column('practical_experiment_id', db.Integer, db.ForeignKey('practical_experiment.id'), nullable=False)
)

Manage_City = db.Table('manage_city',
    db.Column('user_id', db.Integer, db.ForeignKey('system_administrator.id'), nullable=False),
    db.Column('city_id', db.Integer, db.ForeignKey('city.id'), nullable=False)
)


