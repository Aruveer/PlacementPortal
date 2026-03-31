# Campus Placement Portal 🎓
 
 A comprehensive web-based placement management system built with Flask. This platform connects students, company recruiters, and the college placement administration into one seamless workflow.
 
 ##  Key Features
 
 The portal is divided into three role-based dashboards:
 
 * **Admin:** Dashboard to monitor platform statistics, approve/reject company registrations, approve placement drives, and manage the student database.
 * **Company:** Recruiters can register (pending admin approval), post new job drives, review student applications, and update candidate statuses.
 * **Student:** Students can create profiles, upload resumes, browse approved job postings, apply for roles, and track their application history.
 
 ##  Tech Stack
 
 * **Backend:** Python, Flask, Flask-SQLAlchemy
 * **Database:** SQLite
 * **Frontend:** HTML5, CSS3, Bootstrap 5, Jinja2
 * **Data Visualization:** Chart.js
 
 ---
 
 ##  How to Run the Project Locally
 
 Follow these steps to get the portal running on your local machine.
 
 ### 1. Prerequisites
 Make sure you have Python 3 installed on your computer.
 
 ### 2. Clone the Repository
 Open your terminal and clone this project:
  
 ### 3. Set Up the Virtual Environment
 It is highly recommended to run this project in an isolated virtual environment.
 
 
 ```bash
 python -m venv myenv
 myenv\Scripts\activate
 ```
 

 
 ### 4. Install Dependencies
 Install all required Python packages using the requirements file:
 
 ```bash
 pip install -r requirements.txt
 ```
 
 ### 5. Run the Application
 Start the Flask server:
 
 ```bash
 python app.py
 ```

 
 
 ---
 
 ##  Default Admin Access
 To test the Admin dashboard functionalities, use the following pre-configured credentials:
 
 * **Email:** admin@gmail.com
 * **Password:** admin123
