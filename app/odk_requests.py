#!/usr/bin/python3
"""Utilities for interacting with ODK Central API

These are functions that return replies from an ODK Central server. https://docs.getodk.org/central-intro/

These functions mostly return requests.Response() objects. That object contains status code of the request (200, 404, etc), and the data itself, as well as a number of other attributes.

Here's a great reference on how to use the returned objects: https://www.w3schools.com/python/ref_requests_response.asp

The base_url parameter is just the URL of the ODK Central server. The extra characters needed to actually reach the API ('/v1/') are built into the functions.

The aut parameter is a tuple of the username and password used to authenticate the requester on the server, in the form (username, password). The passwords are in plain text; ideally this should be a hash but I haven't gotten around to that.

Simple usage:
If you want to see if a server is working and you are able to reach it, use the projects function:

url = 'https://3dstreetview.org'
aut = ('myusername', 'mypassword')
r = fetch.projects(url, aut)
r.status_code

If all went well, that'll return '200'. If you got the username/password wrong (or aren't authorized on the server for whatever reason) it'll return '401', or '404' if the server isn't found at all.

To see the data:

r.json()

That'll return a JSON-formatted string with information about the projects on the server.

To see the information on a single project:

r.json()[0]

That'll return a dictionary with the attributes of the first project on the server.

To see the name of the first project:

r.json()[0]['name']

"""

import sys, os, io, time
import requests
import json
import zlib
import codecs
import urllib
from PIL import Image


def submissions(base_url, aut, projectId, formId):
    """Fetch a list of submission instances for a given form."""
    url = f'{base_url}/v1/projects/{projectId}/forms/{formId}/submissions'
    return requests.get(url, auth = aut)

def get_attachment(base_url, aut, projectId, formId, instanceId, filename):
    """Fetch a specific attachment by filename from a submission to a form."""
    url = f'{base_url}/v1/projects/{projectId}/forms/{formId}/submissions/{instanceId}/attachments/{filename}'
    return requests.get(url, auth = aut)

def all_attachments_from_form(base_url, aut, projectId, formId, outdir):
    """Downloads all available attachments from a given form"""
    submission_values = submissions(base_url, aut, projectId, formId)
    for submission in submission_values.json():
        sub_id = submission['instanceId']
        start_atachment_time = time.perf_counter()
        attachments = attachment_list(base_url, aut, projectId, formId, sub_id)
        print(f'Received the attachments for subid {sub_id} in {time.perf_counter()-start_atachment_time}')
        for attachment in attachments.json():
            start_atachment_time = time.perf_counter()
            fn = attachment['name']
            outfilepath = os.path.join(outdir, fn)
            if os.path.isfile(outfilepath):
                print(f'Apparently {fn} has already been downloaded')
            else:
                try:
                    attresp = get_attachment(base_url, aut, projectId, formId, sub_id, fn)
                    im = Image.open(io.BytesIO(attresp.content))
                    # resize the image
                    percentage = 0.3
                    resized_im = im.resize((round(im.size[0] * percentage), round(im.size[1] * percentage)))
                    resized_im.save(outfilepath)
                except:
                    print(f'Submission request for the attachment {sub_id} with filename {fn} failed')
            print(f'Saved the attachement for subid {sub_id} for the form {formId} in {time.perf_counter() - start_atachment_time}')


def update_attachments_from_form(submission_table, attachment_folder, base_url, aut, projectId, formId):
    """Update the attachments that do not exist yet from a given form"""
    current_attachments = os.listdir(attachment_folder)
    # Compare to the list in the new form
    #get the image file names
    image_fns = [row['img_machines'] for row in submission_table]
    #get the sorted list of new image files
    new_image_fns = sorted(list(set(image_fns) - set(current_attachments)))
    #sort the submission table also on the file names, so that they match
    submission_table = sorted(submission_table, key=lambda d: d['img_machines'])
    ids = [row['__id'] for row in submission_table if row['img_machines'] in new_image_fns]
    for (sub_id, attachment) in zip(ids,new_image_fns):
            fn = attachment
            outfilepath = os.path.join(attachment_folder, fn)
            if os.path.isfile(outfilepath):
                print(f'Apparently {fn} has already been downloaded')
            else:
                attresp = get_attachment(base_url, aut, projectId, formId, sub_id, fn)
                try:
                    im = Image.open(io.BytesIO(attresp.content))
                    #resize the image
                    percentage = 0.3
                    resized_im = im.resize((round(im.size[0]*percentage), round(im.size[1]*percentage)))
                    resized_im.save(outfilepath)
                    print(f'Downloaded the image {fn} with sub_id {sub_id} in form {formId}')
                except:
                    print(f'The image {fn} with sub_id {sub_id} in form {formId} could not be processed')

def odata_submissions_table(base_url, auth, projectId, formId, table):
    """
    Fetch the submissions using the odata api. 
    use submissions.json()['value'] to get a list of dicts, wherein 
    each dict is a single submission with the form question names as keys.
    """    
    url = f'{base_url}/v1/projects/{projectId}/forms/{formId}.svc/{table}'
    submissions = requests.get(url, auth = auth).json()
    return submissions

def odata_submissions(base_url, auth, projectId, formId, table):
    """
    Fetch the submissions using the odata api. 
    use submissions.json()['value'] to get a list of dicts, wherein 
    each dict is a single submission with the form question names as keys.
    """    
    url = f'{base_url}/v1/projects/{projectId}/forms/{formId}.svc/{table}'
    submissions = requests.get(url, auth = auth)
    return submissions

def odata_attachments(base_url, auth, projectId, formId, instanceId):
    """
    Fetch the attachments 
    """ 
    url = f'{base_url}/v1/projects/{projectId}/forms/{formId}/submissions/{instanceId}/attachments'
    # download the file contents in binary format
    return requests.get(url, auth = auth)

def list_attachments(base_url, auth, projectId, formId):
    """
    Fetch the details of the attachments
    """
    url = f'{base_url}/v1/projects/{projectId}/forms/{formId}/attachments'
    # download the file contents in binary format
    return requests.get(url, auth = auth)

def number_submissions(base_url, auth, projectId, formId):
    """
    Fetch the number of submissions in a form
    Returns the number of submissions
    """
    url = f'{base_url}/v1/projects/{projectId}/forms/{formId}'
    return requests.get(url, auth = auth, headers={'X-Extended-Metadata': 'true'}).json()['submissions']

def get_submission_details(base_url, auth, projectId, formId, table):
    """
    Fetch the number of submission details in a form
    Returns the submission ids
    """
    url = f'{base_url}/v1/projects/{projectId}/forms/{formId}/{table}'
    return requests.get(url, auth=auth).json()

def get_newest_submissions(base_url, auth, projectId, formId, new_records_count):
    """
    Fetch the number of submissions in a form from the top
    Returns the submissions
    """
    url = f'{base_url}/v1/projects/{projectId}/forms/{formId}.svc/Submissions?$top={new_records_count}'
    return requests.get(url, auth = auth)

def export_submissions(base_url, auth, projectId, formId):
    """
    Fetch the submissions in a zip format
    Returns object, where the zip is in the .content
    """ 
    url = f'{base_url}/v1/projects/{projectId}/forms/{formId}/submissions.csv.zip?'
    # download the file contents in binary format
    return requests.get(url, auth = auth)

# ---------------------------------------------------------------------------------------------------------------------------------------------------


def projects(base_url, aut):
    """Fetch a list of projects on an ODK Central server."""
    url = f'{base_url}/v1/projects'
    return requests.get(url, auth = aut)

def project_id(base_url, aut, projectName):
    """Fetch the id of a project based on the name on an ODK Central server."""
    url = f'{base_url}/v1/projects'
    projects = requests.get(url, auth = aut).json()
    projectId = [p for p in projects if p['name']== projectName][0]['id']
    return projectId

def forms(base_url, aut, projectId):
    """Fetch a list of forms in a project."""
    url = f'{base_url}/v1/projects/{projectId}/forms'
    return requests.get(url, auth = aut)


def users(base_url, aut):
    """Fetch a list of users."""
    url = f'{base_url}/v1/users'
    return requests.get(url, auth = aut)

def app_users(base_url, aut, projectId):
    """Fetch a list of app-users."""
    url = f'{base_url}/v1/projects/{projectId}/app-users'
    return requests.get(url, auth = aut)

# Should work with ?media=false appended but doesn't.
# Probably a bug in ODK Central. Use the odata version; it works.
def csv_submissions(base_url, aut, projectId, formId):
    """Fetch a CSV file of the submissions to a survey form."""
    url = f'{base_url}/v1/projects/{projectId}/forms/{formId}/submissions.csv.zip'
    return requests.get(url, auth = aut)


def attachment_list(base_url, aut, projectId, formId, instanceId):
    """Fetch an individual media file attachment."""
    url = f'{base_url}/v1/projects/{projectId}/forms/{formId}/submissions/'\
        f'{instanceId}/attachments'
    return requests.get(url, auth = aut)

# POST 
def create_project(base_url, aut, project_name):
    """Create a new project on an ODK Central server"""
    url = f'{base_url}/v1/projects'
    return requests.post(url, auth = aut, json = {'name': project_name})

def create_app_user(base_url, aut, projectId, app_user_name = 'Surveyor'):
    """
    Create a new project on an ODK Central server

    Atm. you can create multiple app users with the same name, should this be possible, or give an error? 
    """
    url = f'{base_url}/v1/projects/{projectId}/app-users'
    return requests.post(url, auth = aut, json = {'displayName': app_user_name})


def give_access_app_users(base_url, aut, projectId):
    """Give all the app-users in the project access to all the forms in that project"""
    url = f'{base_url}/v1/projects/{projectId}/forms'
    forms = requests.get(url, auth = aut).json()

    for form in forms:
        formId = form['xmlFormId']
        url = f'{base_url}/v1/projects/{projectId}/app-users'
        app_users = requests.get(url, auth = aut).json()
        for user in app_users:
            actorId = user['id']        
            roleId = 2
            url = f'{base_url}/v1/projects/{projectId}/forms/{formId}/assignments/{roleId}/{actorId}' 
            requests.post(url, auth = aut)
    return 200

def delete_project(base_url, aut, project_id):
    """Permanently delete project from an ODK Central server. Probably don't."""
    url = f'{base_url}/v1/projects/{project_id}'
    return requests.delete(url, auth = aut)


def create_form(base_url, aut, projectId, path2Form):
    """Create a new form on an ODK Central server"""
    base_name = os.path.basename(path2Form)
    file_name = os.path.splitext(base_name)[0]
    form_file = open(path2Form, 'rb')
    #sheet = form_file.active

    headers = {
    'Content-Type': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    f'X-XlsForm-FormId-Fallback': file_name
    }
    url = f'{base_url}/v1/projects/{projectId}/forms?ignoreWarnings=true&publish=true'
    values = form_file

    # From the requests, gives the same error
    return requests.post(url, auth = aut, data = form_file, headers = headers)

general={
        "form_update_mode":"match_exactly",
        "autosend":"wifi_and_cellular"
        }



# Test QR settings data
# See here to see all the possible settings: https://docs.getodk.org/collect-import-export/?highlight=configur

# qr_data = {
#   "general": {
#     "protocol": "odk_default",
#     "constraint_behavior": "on_finalize"
#   },
#   "admin": {
#     "edit_saved": false
#   }
# }
# # A QR code from one app user from the website
# qr_data = {
#     "general":{
#         "server_url":"https://3dstreetview.org/v1/key/bm$OwmsI$lYPLjXJyKbSPKmmydD5JuNJH2mwi8$KcUaFVE9EdYiq3mhX4BLDynwH/projects/15",
#         "form_update_mode":"match_exactly",
#         "autosend":"wifi_and_cellular"},
#     "admin":{}
#     }









if __name__ == '__main__':
    pass

