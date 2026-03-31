from flask import render_template,redirect,request,url_for,flash
from sqlalchemy import or_
from .model import *
from app import app
from datetime import datetime
import os
from werkzeug.utils import secure_filename

@app.route("/")
def home():
    return render_template("home.html")

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method=="POST":
        email=request.form.get("email")
        password=request.form.get("password")
        user=User.query.filter_by(email=email).first()

        if user and user.password==password:
            if user.role=="admin":
                return redirect(url_for("admin_dashboard"))
            elif user.role=="student":
                student=Student.query.filter_by(user_id=user.id).first()
                if student and student.is_blacklisted:
                    flash("Your account has been blacklisted.")
                    return redirect(url_for("login"))
                return redirect(url_for("student_dashboard",u_id=user.id))
            elif user.role=="company":
                company=Company.query.filter_by(user_id=user.id).first()
                if company and not company.is_approved:
                    flash("Your profile is pending admin approval.")
                    return redirect(url_for("login"))
                return redirect(url_for("company_dashboard",u_id=user.id))
        else:
            flash("Invalid email or password.")
    return render_template("login.html")

@app.route("/register", methods=["GET","POST"])
def register():
    if request.method=="POST":
        name=request.form.get("name")
        email=request.form.get("email")
        password=request.form.get("password") 
        role=request.form.get("role")

        if not name or len(name)<3:
            flash("Please enter a valid full name (at least 3 characters).")
            return redirect(url_for("register"))
        if not email or "@" not in email:
            flash("Please enter a valid email address.")
            return redirect(url_for("register"))
        if not password or len(password)<7:
            flash("Password must be at least 7 characters long.")
            return redirect(url_for("register"))
        if User.query.filter_by(email=email).first():
            flash("Email already registered!")
            return redirect(url_for("register"))
        
        new=User(email=email,password=password,role=role)
        db.session.add(new)
        db.session.commit()

        if role=="student":
            new_profile=Student(name=name,user_id=new.id)
            db.session.add(new_profile)
            db.session.commit()
            flash("Welcome to your student dashboard!")
            return redirect(url_for("student_dashboard",u_id=new.id))
        else:
            new_profile=Company(name=name,user_id=new.id,is_approved=False)
            db.session.add(new_profile)
            db.session.commit()
            flash("Company registered! Waiting for admin approval.")
            return redirect(url_for("login"))  
    return render_template("register.html")

######################################################### ADMIN #################################################################

@app.route("/admin/dashboard")
def admin_dashboard():
    student_count=Student.query.count()
    pending_company_count=Company.query.filter_by(is_approved=False).count()
    active_drive_count=Placement_drive.query.filter_by(status='Approved').count()
    total_users=User.query.count()
    pending_drive_count=Placement_drive.query.filter_by(status='Pending').count()
    total_apps=Application.query.count()
    placement_count=Application.query.filter_by(status='Accepted').count()

    return render_template("admin_dashboard.html",students=student_count,pending=pending_company_count,drives=active_drive_count,pending_drives=pending_drive_count,users=total_users,total_apps=total_apps,placements=placement_count)

@app.route("/admin/manage-students")
def manage_students():
    search_query=request.args.get('search','')
    if search_query:
        students=Student.query.filter(
            or_(
                Student.name.ilike(f"%{search_query}%"),
                Student.id==search_query if search_query.isdigit() else False
            )
        ).all()
    else:
        students=Student.query.all()
    return render_template("admin_manage_stu.html",students=students)

@app.route("/admin/toggle-blacklist/<int:student_id>")
def toggle_blacklist(student_id):
    student=Student.query.get(student_id)

    if student:
        student.is_blacklisted=not student.is_blacklisted
        db.session.commit()
        status="blacklisted" if student.is_blacklisted else "unbanned"
        flash(f"Student {student.name} has been {status}!")
    return redirect(url_for("manage_students"))

@app.route("/admin/edit-student/<int:s_id>", methods=["GET","POST"])
def admin_edit_student(s_id):
    student=Student.query.get(s_id)

    if request.method=="POST":
        student.name=request.form.get("name")
        student.skills=request.form.get("skills")
        db.session.commit()
        flash(f"Profile for {student.name} updated!")
        return redirect(url_for("manage_students"))
    return render_template("admin_edit_stu.html",student=student)

@app.route("/admin/delete-student/<int:s_id>")
def delete_student(s_id):
    student=Student.query.get(s_id)

    if student:
        user=User.query.get(student.user_id)
        db.session.delete(student)
        if user:
            db.session.delete(user)
        db.session.commit()
        flash("Student account deleted permanently.")
    return redirect(url_for("manage_students"))

@app.route("/admin/review-pending-companies")
def review_pending_companies():
    pending=Company.query.filter_by(is_approved=False).all()
    return render_template("admin_pending_comp.html",companies=pending)

@app.route("/admin/manage-approved-companies")
def manage_approved_companies():
    search_query=request.args.get('search','')
    if search_query:
        approved=Company.query.filter(
            Company.is_approved==True,
            or_(
                Company.name.ilike(f"%{search_query}%"),
                Company.hr_contact.ilike(f"%{search_query}%")
            )
        ).all()
    else:
        approved=Company.query.filter_by(is_approved=True).all()
    return render_template("admin_manage_comp.html",companies=approved)

@app.route("/admin/toggle-approval/<int:company_id>")
def toggle_company_approval(company_id):
    company=Company.query.get(company_id)
    
    if company:
        original_status=company.is_approved
        company.is_approved=not company.is_approved
        db.session.commit()
        status="approved" if company.is_approved else "moved to pending"
        flash(f"Company {company.name} has been {status}!")

        if not original_status:
            return redirect(url_for("review_pending_companies"))
        return redirect(url_for("manage_approved_companies"))
    
    return redirect(url_for("admin_dashboard"))

@app.route("/admin/edit-company/<int:c_id>", methods=["GET","POST"])
def admin_edit_company(c_id):
    company=Company.query.get(c_id)
    if request.method=="POST":
        company.name=request.form.get("name")
        company.hr_contact=request.form.get("hr_contact")
        company.website=request.form.get("website")
        db.session.commit()
        flash(f"Company {company.name} profile updated!")
        return redirect(url_for("manage_companies"))
    return render_template("admin_edit_company.html",company=company)

@app.route("/admin/delete-company/<int:c_id>")
def delete_company(c_id):
    company=Company.query.get(c_id)
    if company:
        user=User.query.get(company.user_id)
        db.session.delete(company)
        if user:
            db.session.delete(user)
        db.session.commit()
        flash("Company deleted successfully!")
    return redirect(url_for("manage_companies"))

@app.route("/admin/review-pending-drives")
def review_pending_drives():
    pending=Placement_drive.query.filter_by(status='Pending').all()
    return render_template("admin_pending_drives.html",pending_drives=pending)

@app.route("/admin/manage-live-drives")
def manage_live_drives():
    approved=Placement_drive.query.filter_by(status='Approved').all()
    return render_template("admin_manage_drives.html",approved_drives=approved)

@app.route("/admin/toggle-drive-status/<int:drive_id>")
def toggle_drive_status(drive_id):
    drive=Placement_drive.query.get(drive_id)
    if drive:
        drive.status='Approved' if drive.status=='Pending' else 'Pending'
        db.session.commit()
        status="approved" if drive.status=='Approved' else "moved back to pending"
        flash(f"Drive for {drive.job} has been {status}!")
    return redirect(url_for("review_pending_drives"))

@app.route("/admin/edit-drive/<int:drive_id>", methods=["GET","POST"])
def admin_edit_drive(drive_id):
    drive=Placement_drive.query.get(drive_id)
    if request.method=="POST":
        drive.job=request.form.get("job")
        drive.description=request.form.get("description")
        deadline_str=request.form.get("deadline")
        drive.salary=request.form.get("salary")
        drive.location=request.form.get("location")
        
        if deadline_str:
            drive.deadline=datetime.strptime(deadline_str,'%Y-%m-%dT%H:%M')

        db.session.commit()
        flash(f"Drive for {drive.job} updated successfully!")
        return redirect(url_for("manage_live_drives"))
    
    return render_template("admin_edit_drive.html",drive=drive)

@app.route("/admin/delete-drive/<int:drive_id>")
def delete_drive(drive_id):
    drive=Placement_drive.query.get(drive_id)

    if drive:
        db.session.delete(drive)
        db.session.commit()
        flash("Placement drive deleted.")
    return redirect(url_for("manage_live_drives"))

@app.route("/admin/drive-details/<int:drive_id>")
def admin_drive_details(drive_id):
    drive=Placement_drive.query.get(drive_id)
    return render_template("admin_drive_details.html",drive=drive)

@app.route("/admin/complete-drive/<int:drive_id>")
def complete_drive(drive_id):
    drive=Placement_drive.query.get(drive_id)

    if drive:
        drive.status='Completed'
        db.session.commit()
        flash(f"Drive for {drive.job} has been marked as completed.")
    return redirect(url_for("manage_live_drives"))

@app.route("/admin/all-applications")
def view_all_applications():
    apps=Application.query.all()
    return render_template("admin_view_apps.html",applications=apps)

@app.route("/admin/application-details/<int:app_id>")
def application_details(app_id):
    app_data=Application.query.get(app_id)
    return render_template("admin_app_details.html",app=app_data)

######################################################### COMPANY #################################################################

@app.route("/company/dashboard/<int:u_id>")
def company_dashboard(u_id):
    company=Company.query.filter_by(user_id=u_id).first()

    if not company:
        flash("Company profile not found.")
        return redirect(url_for('login'))
    
    all_drives=Placement_drive.query.filter_by(company_id=company.id).all()
    upcoming=[d for d in all_drives if d.status in ['Approved','Pending']]
    closed=[d for d in all_drives if d.status=='Completed']
    return render_template("company_dashboard.html",company=company,upcoming_drives=upcoming,closed_drives=closed,u_id=u_id)

@app.route("/company/complete-drive/<int:drive_id>/<int:u_id>")
def company_complete_drive(drive_id,u_id):
    drive=Placement_drive.query.get(drive_id)

    if drive:
        drive.status='Completed'
        db.session.commit()
        flash(f"Drive for {drive.job} has been completed.")
    return redirect(url_for("company_dashboard",u_id=u_id))

@app.route("/company/create-drive/<int:u_id>", methods=["GET","POST"])
def create_drive(u_id):
    if request.method=="POST":
        job=request.form.get("job")
        description=request.form.get("description")
        deadline_str=request.form.get("deadline")
        deadline=datetime.strptime(deadline_str,'%Y-%m-%dT%H:%M') if deadline_str else None
        sal=request.form.get("salary")      
        loc=request.form.get("location")
        company=Company.query.filter_by(user_id=u_id).first()

        if company:
            new_drive=Placement_drive(job=job,description=description,deadline=deadline,company_id=company.id,salary=sal,location=loc,status="Pending")
            db.session.add(new_drive)
            db.session.commit()
            flash("Drive posted successfully!")
            return redirect(url_for("company_dashboard",u_id=u_id))
    return render_template("company_create_drive.html",u_id=u_id)

@app.route("/company/view-applicants/<int:drive_id>/<int:u_id>")
def view_applicants(drive_id,u_id):
    drive=Placement_drive.query.get(drive_id)
    apps=Application.query.filter_by(drive_id=drive_id).all()
    return render_template("company_view_applicants.html",drive=drive,applications=apps,u_id=u_id)

@app.route("/company/update-status/<int:app_id>/<string:new_status>/<int:u_id>")
def update_application_status(app_id,new_status,u_id):
    application=Application.query.get(app_id)

    if application:
        application.status=new_status 
        db.session.commit()
        flash(f"Application status updated to {new_status}!")
    return redirect(url_for('view_applicants',drive_id=application.drive_id,u_id=u_id))

@app.route("/company/edit-profile/<int:u_id>", methods=["GET","POST"])
def company_edit_profile(u_id):
    company=Company.query.filter_by(user_id=u_id).first()

    if request.method=="POST":
        company.name=request.form.get("name")
        company.hr_contact=request.form.get("hr_contact")
        company.website=request.form.get("website")
        db.session.commit()
        flash("Company profile updated successfully!")
        return redirect(url_for("company_dashboard",u_id=u_id))
    return render_template("company_edit_profile.html",company=company,u_id=u_id)

######################################################### STUDENT #################################################################

@app.route("/student/dashboard/<int:u_id>")
def student_dashboard(u_id):
    student=Student.query.filter_by(user_id=u_id).first()
    companies=Company.query.filter_by(is_approved=True).all()
    my_applications=Application.query.filter_by(student_id=student.id).all()
    applied_drive_ids=[app.drive_id for app in my_applications]

    return render_template("student_dashboard.html",student=student,companies=companies,my_apps=my_applications,applied_ids=applied_drive_ids,u_id=u_id)

@app.route("/student/edit-profile/<int:u_id>", methods=["GET","POST"])
def edit_profile(u_id):
    student=Student.query.filter_by(user_id=u_id).first()

    if request.method=="POST":
        student.name=request.form.get("name")
        student.skills=request.form.get("skills")
        file=request.files.get('resume')
        if file and file.filename!='':
            filename=secure_filename(f"user_{u_id}_{file.filename}")
            file.save(os.path.join(app.config['UPLOAD_FOLDER'],filename))
            student.resume=filename   
        db.session.commit()
        flash("Profile and resume updated!")
        return redirect(url_for("student_dashboard",u_id=u_id))
    return render_template("student_edit_profile.html",student=student,u_id=u_id)

@app.route("/toggle-apply/<int:drive_id>/<int:u_id>")
def toggle_application(drive_id,u_id):
    student=Student.query.filter_by(user_id=u_id).first()

    if not student:
        flash("Student profile not found.")
        return redirect(url_for("login"))
    existing_app=Application.query.filter_by(student_id=student.id,drive_id=drive_id).first()
    if existing_app:
        db.session.delete(existing_app)
        db.session.commit()
        flash("Application withdrawn successfully.")
    else:
        new_app=Application(student_id=student.id,drive_id=drive_id,status="Applied")
        db.session.add(new_app)
        db.session.commit()
        flash("Application submitted successfully!")
    return redirect(url_for("student_dashboard",u_id=u_id))

@app.route("/student/company-details/<int:company_id>/<int:u_id>")
def company_details_student(company_id,u_id):
    company=Company.query.get(company_id)
    drives=Placement_drive.query.filter_by(company_id=company_id,status='Approved').all()

    return render_template("student_view_company.html",company=company,drives=drives,u_id=u_id)

@app.route("/student/drive-details/<int:drive_id>/<int:u_id>")
def student_drive_details(drive_id,u_id):
    drive=Placement_drive.query.get(drive_id)
    student=Student.query.filter_by(user_id=u_id).first()
    is_applied=Application.query.filter_by(student_id=student.id,drive_id=drive_id).first() is not None

    return render_template("student_view_drive.html",drive=drive,u_id=u_id,is_applied=is_applied)

@app.route("/student/history/<int:u_id>")
def student_history(u_id):
    student=Student.query.filter_by(user_id=u_id).first()
    history=Application.query.filter_by(student_id=student.id).all()
    
    return render_template("student_history.html",student=student,history=history,u_id=u_id)
