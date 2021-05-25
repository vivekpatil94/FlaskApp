from app import db
from flask import Blueprint,jsonify,request,abort

class Defect_Report(db.Model):
    __tablename__ = 'defect_report'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    text = db.Column(db.String(250), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    status = db.Column(db.Boolean,nullable=False,default=False)



    def format(self):
        user = self.user
        return {
            'id': self.id,
            'userId': self.user_id,
            'text': self.text,
            'title': self.title,
            'status': self.status,
            'email': user.email,
            'phone': user.phone,
            'path': '/defect/{}'.format(self.id)
        }

    def insert(self):
        try:   
            db.session.add(self)
            db.session.commit()  
            return self    
        except:
            db.session.rollback()
            abort(400, 'حدث خطأ, يرجى المحاولة لاحقاً') 

    def delete(self):
        try:   
            db.session.delete(self)
            db.session.commit()       
        except:
            db.session.rollback()
            abort(400, 'حدث خطأ, يرجى المحاولة لاحقاً') 
    
    def change_state(self,status):
        try:
            self.status = status
            db.session.commit()
        except:
            db.session.rollback()
            abort(400, 'حدث خطأ, يرجى المحاولة لاحقاً')


class Valid_Token(db.Model):
    __tablename__ = 'valid_token'
    
    token = db.Column(db.String, nullable=False)
    user_id = db.Column(db.Integer,  db.ForeignKey('users.id'),primary_key=True)

    def insert(self):
        try:   
            db.session.add(self)
            db.session.commit()       
        except:
            db.session.rollback()
            abort(400, 'حدث خطأ, يرجى المحاولة لاحقاً') 
        finally:
            db.session.close()

    def delete(self):
        try:   
            db.session.delete(self)
            db.session.commit()       
        except:
            db.session.rollback()
            abort(400, 'حدث خطأ, يرجى المحاولة لاحقاً') 
   

