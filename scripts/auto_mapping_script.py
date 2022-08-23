import os
import json
import requests

class Analysis():
    headers = {'Content-Type': 'application/json'}
    failure_url = "http://srinivas-dev.pf9.io/build_failures"

    def __init__(self):
        self.a = 1
        self.build_failure = {}

    def update_failure(self, build_id, payload_dict):
        payload = json.dumps(payload_dict)
        url = self.failure_url + "/" + str(build_id)
        response = requests.request("POST", url, headers=self.headers, data=payload)

        if response.status_code == 200:
            print(f"Successfully updated the failure ID [{build_id}] with bug [{payload_dict['bug_id']}]")
        #print(response.text)

    def get_build_failure_data(self):
        response = requests.request("GET", self.failure_url, headers=self.headers)
        self.build_failure = response.json()

    def get_unanalyzed_failure(self):
        url = self.failure_url + "?is_analyzed=0"
        response = requests.request("GET", url, headers=self.headers)
        return response.json()        

    def get_analyzed_failures(self):
        url = self.failure_url + "?is_analyzed=1"
        response = requests.request("GET", url, headers=self.headers)
        return response.json()                


if __name__ == "__main__":
    Obj = Analysis()
    # payload = json.dumps({
    #     "bug_id": "TESTS-1234",
    #     "analyzed_by": "sriniaa",
    #     "is_analyzed": "1"
    # })
    #Obj.update_failure(7, payload)
    Obj.get_build_failure_data()
    #print(Obj.build_failure)

    analyzed_failures = Obj.get_analyzed_failures()
    unanalyzed_failures = Obj.get_unanalyzed_failure()
    user = "Piyush"
    for failure in unanalyzed_failures:
        #print(failure)
        for analyzed_failure in analyzed_failures:
            if failure['md5sum'] == analyzed_failure['md5sum']:
                bug = analyzed_failure['bug_id']
                payload_dict = {
                    "bug_id": bug,
                    "analyzed_by": user,
                    "is_analyzed": "1"                    
                }
                print(f"Found Match for Failure ID: {failure['id']}")
                Obj.update_failure(failure['id'], payload_dict)
                break
        else:
            print(f"Could not Found Match for Failure ID: {failure['id']}")
