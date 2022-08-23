"""
Flask App to provide API wrappers over the Failure DB backend
"""
import os
import json
from flask import Flask, request, jsonify, render_template
from flask_mysqldb import MySQL

app = Flask(__name__)

app.config['MYSQL_HOST'] = os.getenv('MYSQL_HOST', 'srinivas-dev.pf9.io')
app.config['MYSQL_USER'] = os.getenv('MYSQL_USER', 'hkt_user')
app.config['MYSQL_PASSWORD'] = os.getenv('MYSQL_PASSWORD', 'hkt_password')
app.config['MYSQL_DB'] = 'failure_db'

mysql = MySQL(app)

def _list_items(table, return_json=False):
    """
    Generic method for all GET API calls. User can specify query params to the get call.
    The keys used for query are same as those documented in corresponding POST calls
    """
    try:
        print(request.args)
        query = f"SELECT * from {table}"
        if request.args: # Process any GET params
            query += " WHERE "
            for arg in request.args:
                query += f"{arg}='{request.args[arg]}'"
        print(query)

        cursor = mysql.connection.cursor()
        cursor.execute(query)
        row_headers=[x[0] for x in cursor.description] #this will extract row headers
        return_values = cursor.fetchall()
        json_data=[]
        for result in return_values:
            json_data.append(dict(zip(row_headers,result)))
        if return_json:
            return json_data
        return jsonify(json_data)
    except Exception as err:
        return jsonify({"status": "failed", "details": str(err)})

def _get_item_by_id(table, id, return_json=False):
    """
    Generic method for all GET API calls. User can specify query params to the get call.
    The keys used for query are same as those documented in corresponding POST calls
    """
    try:
        print(request.args)
        query = f"SELECT * from {table} where id={id}"
        print(query)

        cursor = mysql.connection.cursor()
        cursor.execute(query)
        row_headers=[x[0] for x in cursor.description] #this will extract row headers
        return_value = cursor.fetchone()
        json_data=[]
        json_data.append(dict(zip(row_headers,return_value)))
        print(json_data)
        if return_json:
            return json_data
        return jsonify(json_data)
    except Exception as err:
        return jsonify({"status": "failed", "details": str(err)})

def _insert_item(table):
    """
    Generic method for POST API calls. The function parses the payload and inserts
    data into the DB. The keys in the payload need to match the column names in DB
    """
    try:
        data = request.data.decode('utf8')
        print(data)
        record = json.loads(data)
        query = f"INSERT INTO {table} ("
        query += ",".join(record.keys())
        query += ") VALUES ("
        query += ",".join(f"'{w}'" for w in record.values())
        query += ")"
        print(query)

        cursor = mysql.connection.cursor()
        cursor.execute(query)
        mysql.connection.commit()
        return jsonify({"status": "success"})
    except Exception as err:
        return jsonify({"status": "failed", "details": str(err)})

@app.route('/users', methods=['GET'])
def list_users():
    """
    List all users from users table
    """
    return _list_items("users")

@app.route('/users', methods=['POST'])
def create_user():
    """
    Add user to the users table
    Expected payload structure:
    {"username": "srini"}
    """
    return _insert_item("users")

@app.route('/branches', methods=['GET'])
def list_branches():
    """
    List all branches from branches table
    """
    return _list_items("branches")

@app.route('/branches', methods=['POST'])
def create_branches():
    """
    Add branch to the branches table
    Expected payload structure:
    {"name": "atherton"}
    """
    return _insert_item("branches")

@app.route('/builds', methods=['GET'])
def list_builds():
    """
    List all builds from builds table
    """
    return _list_items("builds")

@app.route('/builds', methods=['POST'])
def create_builds():
    """
    Add build to the builds table
    Expected payload structure:
    {"id":"123456", "branch_id":"1", "date": "2022-08-22 12:34:56"}
    """
    return _insert_item("builds")

@app.route('/build_failures', methods=['GET'])
def list_build_failures():
    """
    List all build failures from build_failures table
    """
    return _list_items("build_failures")

@app.route('/build_failures', methods=['POST'])
def create_build_failures():
    """
    Add build failure to the build_failures table
    Expected payload structure:
    {"build_id": 1, "bug_id": "TESTS-1", "analyzed_by": "2", "is_analyzed": "0",
     "job_name": "020-pmk-tests-on-bareos", "job_id": "543", "suite": "qbert_bare_os_u20",
     "test_module": "test_bareos", "test": "test_cluster", "message": "test_k8s_api failed",
     "md5sum": "uniquemd5sumoffailure"}
    """
    return _insert_item("build_failures")


@app.route('/build_failures/<int:id>', methods=['POST'])
def update_build_failure(id):
    try:
        if request.form:
            data = request.form
            record = data
        else:
            data = request.data.decode('utf8')
            print(data)
            record = json.loads(data)
        _query = "UPDATE build_failures SET "
        _query += ",".join([f"{key}='{value}'" for key, value in record.items() if key != "id"])
        _query += f" WHERE id={id}"
        print(_query)

        cursor = mysql.connection.cursor()
        cursor.execute(_query)
        mysql.connection.commit()
        return jsonify({"status": "success"})
    except Exception as err:
        return jsonify({"status": "failed", "details": str(err)})

@app.route('/gui/build_failure/<int:id>', methods=['GET'])
def gui_build_failure(id):
    return render_template("failure.html", build_failures=_get_item_by_id("build_failures", id, return_json=True), title=f"Editing failure ID: {id}")

@app.route('/gui/build_failures', methods=['GET'])
def gui_build_failures():
    """
    List all build failures from build_failures table
    """
    return render_template("failures.html", build_failures=_list_items("build_failures", return_json=True), title="Failure list")

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=80)
