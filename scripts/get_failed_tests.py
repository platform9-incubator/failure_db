import os
import json
import hashlib
import re
import requests
from bs4 import BeautifulSoup

TEAMCITY_BASE_URL = os.getenv('TEAMCITY_URL',
                              'https://teamcity.platform9.horse')
TEAMCITY_TOKEN = os.getenv('TEAMCITY_TOKEN', None)
TEAMCITY_USERNAME = os.getenv('TEAMCITY_USERNAME', None)
TEAMCITY_PASSWORD = os.getenv('TEAMCITY_PASSWORD', None)

req_headers = {'Accept': 'application/json'}
if TEAMCITY_TOKEN:
    req_headers['Authorization'] = f'Bearer {TEAMCITY_TOKEN}'
    req_auth = None
elif TEAMCITY_USERNAME and TEAMCITY_PASSWORD:
    req_auth = (TEAMCITY_USERNAME, TEAMCITY_PASSWORD)


def verify_tc_credentials():
    if not TEAMCITY_TOKEN and not (TEAMCITY_USERNAME or TEAMCITY_PASSWORD):
        print(
            "TEAMCITY_TOKEN or TEAMCITY_USERNAME or TEAMCITY_PASSWORD not set."
        )
        return False
    return True


def get_failed_builds(buildtype):
    resp = requests.get(
            auth=req_auth,
            headers=req_headers,
            url=f'{TEAMCITY_BASE_URL}/app/rest/builds?locator=buildType:{buildtype},state:finished,branch:atherton,status:failure,sinceDate:20220724T102014%2B0000')
    return resp.json()


def get_message_from_xunit_file(build_id, test_suite, test_name):
    #print(str(build_id) + "---" + test_suite + "---" + test_name)
    xml_file_name = 'testbed_create.xml' if 'testbed_create' in test_name else 'xunit.xml'
    resp = requests.get(
            auth=req_auth,
            headers=req_headers,
            url=f'{TEAMCITY_BASE_URL}/app/rest/builds/id:{build_id}/artifacts/content/testing/{test_suite}/{xml_file_name}')
    data = resp.text
    bs_data = BeautifulSoup(data, "xml")
    error_message = bs_data.find('error')
    actual_error_message = error_message.get('message').split('>>')[0]
    parsed_actual_error_message = actual_error_message.split('\n')[0].lstrip('<')
    return parsed_actual_error_message


def get_du_chart(build_id, test_suite, test_name):
    resp = requests.get(
            auth=req_auth,
            headers=req_headers,
            url=f'{TEAMCITY_BASE_URL}/app/rest/builds/id:{build_id}/artifacts/content/testing/{test_suite}/kubedu-du-artifact.json')
    json_data = json.loads(resp.text)
    du_chart_list = json_data['du_artifacts']
    if len(du_chart_list) > 1:
        du_chart = json_data['du_artifacts'][1].split('/')[-1]
    else:
        du_chart = json_data['du_artifacts'][0].split('/')[-1]
    return du_chart


def fetch_teamcity_props(build_id=os.getenv('TEAMCITY_BUILD_ID', None)):
    """
    Retrieves Teamcity build properties
    :param build_id: unique teamcity build number
    :return: True if matches regex_string, False otherwise
    """
    if not build_id:
        raise Exception('TEAMCITY_BUILD_ID not set')
    if not verify_tc_credentials():
        print("Invalid credentials.")
        return False

    build_details_dict_resp = requests.get(
        auth=req_auth,
        headers=req_headers,
        url=f'{TEAMCITY_BASE_URL}/app/rest/builds/buildId:{build_id}')
    return build_details_dict_resp.json()

def fetch_tests(build_id, count=1000):
    """
    Get test results associated with a particular build.
    :param: build_id: Unique id assigned to each build by teamcity.
    """
    if not verify_tc_credentials():
        print("Invalid credentials. Cannot get test results.")
        return False

    fetch_url = f"{TEAMCITY_BASE_URL}/app/rest/testOccurrences?locator=build:(id:{build_id}),count:{count}"
    resp = requests.get(fetch_url, auth=req_auth, headers=req_headers)
    resp.raise_for_status()
    return resp.json()

def sanitise_message(message):
    """
    This function sanitises the given message string.
    i.e. it removes time, memory address, URLs, DU Names etc.
    """
    #print(message)
    # sanitising time in seconds
    new_message = re.sub("[\d]+ seconds", "NN seconds", message)
    # sanitising memory address
    new_message = re.sub("0x[0-9a-f]+", "MEM_ADDR", new_message)
    # sanitising URLs
    new_message = re.sub("(http|ftp|https):\/\/([\w_-]+(?:(?:\.[\w_-]+)+))([\w.,@?^=%&:\/~+#-]*[\w@?^=%&\/~+#-])", "URL", new_message)
    # sanitising test DU name
    new_message = re.sub("test[\w\d\-.]+du[\w\d\-.]+", "DU_NAME", new_message)
    # sanitising test cluster name
    new_message = re.sub("test[\w\d\-.]+cluster[\w\d\-.]+", "CLUSTER_NAME", new_message)
    # sanitising time stamps
    new_message = re.sub("\"[TZ(\d\:\-)]+\"", "\"DATETIME\"", new_message)
    # sanitising the pod names
    new_message = re.sub("on pod \[[\d\w\W]+\]", "on pod PODNAME", new_message)
    return new_message

if __name__ == '__main__':
    buildtype = 'Pf9project_IntegrationPipelineOnKubeDU_020pmkTestsOnBareos'
    failed_builds = get_failed_builds(buildtype)
    failed_builds_list = []
    for build in failed_builds['build']:
        build_id = build['id']
        build_properties = fetch_teamcity_props(build_id)
        build_number = build_properties["number"]
        tests = fetch_tests(build_id)
        failed_tests = []
        if "testOccurrence" in tests:
            failed_tests = [
                    ft["name"]
                    for ft in tests["testOccurrence"]
                    if ft["status"] != "SUCCESS" and "ignored" not in ft
                    ]
        for test in failed_tests:
            split_test = test.split(':')
            test_suite = split_test[0]
            test_name = split_test[1]
            du_chart = get_du_chart(build_id, test_suite, test_name)
            message = get_message_from_xunit_file(build_id, test_suite, test_name)

        failed_build_record = {'build_id': build_id, 'teamcity_build_number': build_number, 'du_chart': du_chart, 'suite': test_suite, 'testname': test_name, 'message': message}
        failed_builds_list.append(failed_build_record)

    for failed_build in failed_builds_list:
        # sanitising the message field.
        sanitized_message = sanitise_message(failed_build["message"])
        failed_build["sanitized_message"] = sanitized_message

        # Generating MD5 of the failure
        # currently we are creating MD5 using testname and sanitised message.
        failed_string = failed_build["testname"] + ":" + sanitized_message
        failure_md5 = hashlib.md5(failed_string.encode('utf-8')).hexdigest()
        failed_build["failure_md5"] = failure_md5

    print(failed_builds_list)

    headers = {'Content-Type': 'application/json'}
    url = "http://srinivas-dev.pf9.io/build_failures"
    print("Doing POST Calls to load data into DB")
    for failed_data in failed_builds_list:
        payload = json.dumps({
            "build_id": failed_data['du_chart'],
            "bug_id": "", # Default value
            "analyzed_by": "", # Default value
            "is_analyzed": "0", # Default value
            "job_name": "020-pmk-tests-on-bareos", # Keeping it hard coded
            "job_id": failed_data['teamcity_build_number'],
            "suite": failed_data['suite'],
            "teamcity_build_number": failed_data['build_id'],
            "test_module": "test_bareos", # Keeping it hard coded
            "test": failed_data['testname'],
            "message": failed_data['message'],
            "md5sum": failed_data['failure_md5']
        })
        print(payload)
        response = requests.request("POST", url, headers=headers, data=payload)
        print(response.text)
