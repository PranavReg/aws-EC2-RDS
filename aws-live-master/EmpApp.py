from flask import Flask, render_template, request
from pymysql import connections
import os
import boto3
from config import *
from django.http import HttpResponse

app = Flask(__name__)

bucket = custombucket
region = customregion

db_conn = connections.Connection(
    host=customhost,
    port=3306,
    user=customuser,
    password=custompass,
    db=customdb

)
output = {}
table = 'employee'


@app.route("/", methods=['GET', 'POST'])
def home():
    return render_template('AddEmp.html')


@app.route("/about", methods=['POST'])
def about():
    return render_template('www.intellipaat.com')


@app.route("/addemp", methods=['POST'])
def AddEmp():
    emp_id = request.form['emp_id']
    first_name = request.form['first_name']
    last_name = request.form['last_name']
    pri_skill = request.form['pri_skill']
    location = request.form['location']
    emp_image_file = request.files['emp_image_file']

    insert_sql = "INSERT INTO employee VALUES (%s, %s, %s, %s, %s)"
    cursor = db_conn.cursor()

    if emp_image_file.filename == "":
        return "Please select a file"

    try:

        cursor.execute(insert_sql, (emp_id, first_name, last_name, pri_skill, location))
        db_conn.commit()
        emp_name = "" + first_name + " " + last_name
        # Uplaod image file in S3 #
        emp_image_file_name_in_s3 = "emp-id-" + str(emp_id) + "_image_file"
        s3 = boto3.resource('s3')

        try:
            print("Data inserted in MySQL RDS... uploading image to S3...")
            s3.Bucket(custombucket).put_object(Key=emp_image_file_name_in_s3, Body=emp_image_file)
            bucket_location = boto3.client('s3').get_bucket_location(Bucket=custombucket)
            s3_location = (bucket_location['LocationConstraint'])
            print(bucket_location)
            print(s3_location)

            if s3_location is None:
                s3_location = ''
            else:
                s3_location = '-' + s3_location

            object_url = "https://s3{0}.amazonaws.com/{1}/{2}".format(
                s3_location,
                custombucket,
                emp_image_file_name_in_s3)
            print(object_url)

        except Exception as e:
            return str(e)

    finally:
        cursor.close()

    print("all modification done...")
    return render_template('AddEmpOutput.html', name=emp_name)

@app.route("/getemp", methods=['POST'])
def GetEmp():
    return render_template('GetEmp.html')

@app.route("/fetchdata", methods=['POST'])
def fetchData():
    emp_id = request.form['emp_id']
    query = "SELECT * FROM employee WHERE emp_id=%s"
    cursor = db_conn.cursor()

    try:
        cursor.execute(query, (emp_id))
        outputdata=cursor.fetchall()
        print(outputdata)
        id=outputdata[0][0]
        fname=outputdata[0][1]
        lname = outputdata[0][2]
        interest = outputdata[0][3]
        location = outputdata[0][4]
    except Exception as e:
        id = "No data found"
        fname = "No data found"
        lname = "No data found"
        interest = "No data found"
        location = "No data found"

    try:
        emp_image_file_name_in_s3 = "emp-id-" + str(emp_id) + "_image_file"
        s3 = boto3.client('s3')
        #obj = s3.Object(custombucket, emp_image_file_name_in_s3)
        #file_stream = obj.get()['Body'].read()
        #response = HttpResponse(file_stream, content_type="image/jpeg")
        presigned_url = s3.generate_presigned_url('get_object', Params={'Bucket': custombucket, 'Key': emp_image_file_name_in_s3},
                                                         ExpiresIn=100)
        print(presigned_url)
    except Exception as e:
        presigned_url=None
    return render_template('GetEmpOutput.html',id=id,fname=fname,lname=lname,interest=interest, location=location,image=presigned_url)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True)
