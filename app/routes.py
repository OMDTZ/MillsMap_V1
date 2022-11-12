from flask import render_template, send_from_directory, request
import atexit
import csv
import requests, os
from werkzeug.wrappers import Response
import json
import pandas as pd
from apscheduler.schedulers.background import BackgroundScheduler
from os.path import exists
import time
# Local imports
from app import app
from app.odk_requests import odata_submissions, export_submissions, \
    odata_submissions_table, list_attachments, odata_attachments, \
    all_attachments_from_form, update_attachments_from_form
from app.helper_functions import get_filters, nested_dictionary_to_df, flatten_dict
from app.graphics import count_items, unique_key_counts, charts
from app.update_submission_files import fetch_odk_submissions, update_form_config_file, get_form_column, \
    get_new_sub_ids, check_new_submissions_odk, read_local_tables_together

# Configured values
from app.config import *
# todo: set these values to another config file that is read in the beginning


# Functions for downloading attachments
def get_submission_ids(mills_table):
    submission_ids = [row['__id'] for row in mills_table]
    return submission_ids

# Check if the files folder exist, if not, create one and fetch the data from odk to fill it
path = 'app/submission_files'
if not os.path.exists('app/submission_files'):
    os.makedirs('app/submission_files')

# check if the files exists, if not, fetch the data from ODK
formId_list = list()
for i in range(0, len(form_details)):
    form_index = i
    formId = form_details[form_index]['formId']
    formId_list.append(formId)
    file_name = ''.join([formId, '.csv'])
    for id in id_columns:
        path = os.path.join(submission_files_path, file_name)
        if exists(path):
            next
        else:
            # fetch all the mills data from odk
            all_tables = fetch_odk_submissions(form_index, base_url, aut, projectId, formId)
            update_form_config_file(form_details)

sched = BackgroundScheduler(daemon=True)
sched.add_job(check_new_submissions_odk, 'interval', seconds=update_time)
sched.start()
atexit.register(lambda: sched.shutdown())

@app.route('/download_attachments')
def download_attachments():
    if not os.path.exists(figures_path):
        os.makedirs(figures_path)
        for formId in formId_list:
            all_attachments_from_form(base_url, aut, projectId, formId, figures_path)
    else:
        # check how many machines in the config file and how many in the folder
        last_record_machines = 0
        for row in form_details:
            try:
                last_record_machines += int(row['lastNumberRecordsMachines'])
            except:
                last_record_machines += 0
        attachment_figures_in_folder = len(os.listdir('app/static/figures'))
        if attachment_figures_in_folder < last_record_machines:
            for formId in formId_list:
                file_name = ''.join([formId, '.csv'])
                path = os.path.join(submission_files_path, file_name)
                with open(path, newline='') as data_file:
                    csv_file = csv.DictReader(data_file)
                    file = list()
                    for row in csv_file:
                        file.append(row)
                data_file.close()
                update_attachments_from_form(file, figures_path, base_url, aut, projectId, formId)

sched2 = BackgroundScheduler(daemon=True)
sched2.add_job(download_attachments, 'interval', seconds=600)
sched2.start()
atexit.register(lambda: sched2.shutdown())

@app.route('/file_names', methods=['POST'])
def get_main_tables():
    folder = 'mills'
    path = os.path.join(submission_files_path, folder)
    form_names = os.listdir(path)
    return json.dumps(form_names)

@app.route('/mills')
def mills():
    # Read the data
    mills = read_local_tables_together(folder='Submissions')
    return json.dumps(mills)


@app.route('/machines')
def machines():
    machines = read_local_tables_together(folder='Submissions.machines.machine')
    return json.dumps(machines)

@app.route('/read_submissions')
def read_submissions():
    start_time = time.perf_counter()
    file = read_local_tables_together(folder='')
    read_csv_time = time.perf_counter() - start_time
    print(f'Read the merged csv table in {read_csv_time}')
    return json.dumps(file)

@app.route('/get_merged_dictionaries')
def get_merged_dictionaries():
    start_time = time.perf_counter()
    machines = read_local_tables_together(folder='Submissions.machines.machine')
    mills = read_local_tables_together(folder='Submissions')
    reading_local_tables_time = time.perf_counter()
    print(f'Read local tables in {reading_local_tables_time - start_time}s')
    machine_i = 0
    start_time = time.perf_counter()
    for i in range(len(mills)):
        number_machines = int(mills[i]['machines_machine_count'])
        machine_list = list()
        for j in range(number_machines):
            machine_list.append(machines[machine_i])
            machine_i += 1
        mills[i]['machines'] = machine_list
    merging_time = time.perf_counter()
    print(f'Merged tables together in {merging_time - start_time}s')
    return json.dumps(mills)

@app.route('/get_filter_options')
def get_filter_options():
    return json.dumps([{'test':'jee'}])

@app.route('/sites')
def sites():
    import concurrent.futures
    results = []
    with concurrent.futures.ThreadPoolExecutor() as ex:
        futures = [mills, machines]
        for future in concurrent.futures.as_completed(futures):
            results.append(future.result())


@app.route('/mill_points')
def mill_points():
    start_time = time.perf_counter()
    submissions = odata_submissions(base_url, aut, projectId, formId, table='Submissions')
    submissions_machine = odata_submissions(base_url,
                                            aut, projectId, formId, table='Submissions.machines.machine')
    requests_complete_time = time.perf_counter()
    submissions_table = pd.DataFrame(submissions.json()['value'])
    submissions_machine_table = \
        pd.DataFrame(submissions_machine.json()['value'])
    pd_df_complete_time = time.perf_counter()
    charts(submissions_machine.json()['value'], submissions.json()['value'])
    charts_complete_time = time.perf_counter()

    # Dataframe with nested dictionaries to flat dictionary
    submissions_table = nested_dictionary_to_df(submissions_table)
    submissions_machine_table = \
        nested_dictionary_to_df(submissions_machine_table)
    submissions_all = submissions_table.merge(submissions_machine_table,
                                              left_on='__id',
                                              right_on='__Submissions-id')
    tables_to_flat_complete_time = time.perf_counter()

    # List the columns from the submissions that will be retained
    # by the filter to send to the webmap client
    mill_filter_list = ['mill_owner', 'flour_fortified',
                        'flour_fortified_standard',
                        'Location_addr_region',
                        'Location_addr_district']
    machine_filter_list = ['commodity_milled',
                           'mill_type', 'operational_mill',
                           'non_operational', 'energy_source']
    mill_filter_selection = get_filters(mill_filter_list, submissions_all)
    machine_filter_selection = get_filters(machine_filter_list,
                                           submissions_all)
    get_filters_complete_time = time.perf_counter()
    submissions_table_filtered_machine = \
        submissions_machine_table.to_dict(orient='index')
    submissions_filtered_dict = submissions_table.to_dict(orient='index')
    # submissions_table_filtered_dict = json.loads(submissions_table_filtered)
    # Make submissions_table_filtered into dictionary of dictionaries
    # with machine information nested within
    submissions_dict = submissions_filtered_dict
    for submission_id in submissions_dict:
        submissions_dict[submission_id]['machines'] = {}
        for machine_index in submissions_table_filtered_machine:
            machine_submission_id = \
                submissions_table_filtered_machine[machine_index] \
                    ['__Submissions-id']
            machine_id = \
                submissions_table_filtered_machine[machine_index]['__id']
            if machine_submission_id == submission_id:
                submissions_dict[submission_id]['machines'][machine_index] = \
                    submissions_table_filtered_machine[machine_index]
    submissions_filtered_json = json.dumps(submissions_dict)

    to_json_complete_time = time.perf_counter()
    print(f'Requests are complete at {requests_complete_time - start_time}s,' \
          f'pandas dataframes are complete at '
          f'{pd_df_complete_time - requests_complete_time}s, charts are complete' \
          f'at {charts_complete_time - pd_df_complete_time}s, tables are flat ' \
          f'in {tables_to_flat_complete_time - charts_complete_time}s, got ' \
          f'filters in ' \
          f'{get_filters_complete_time - tables_to_flat_complete_time}s, ' \
          f'and to_json in {to_json_complete_time - get_filters_complete_time}s')
    return submissions_filtered_json


@app.route('/json_test')
def json_test():
    test_submission = json.load(open('individual_test_submission.json', 'r'))
    return json.dumps(test_submission)


@app.route('/')
@app.route('/index')
@app.route('/home')
def index():
    return render_template('index.html', title='Map')


@app.route('/filterform', methods=['GET', 'POST'])
def filter_data():
    if request.method == 'POST':
        choices = request.form
        choices_dict = {}
        for choice in choices:
            choice_element = choice.split(", ")[0]
            if choice_element not in choices_dict:
                choices_dict[choice_element] = []
            choices_dict[choice_element].append(choice.split(", ")[1])

            submissions = odata_submissions(base_url, aut, projectId, formId, table='Submissions')
            submissions_machine = odata_submissions(base_url, aut, projectId, formId,
                                                    table='Submissions.machines.machine')
            # charts(submissions_machine.json()['value'],
            #       submissions.json()['value'])
            submissions_table = \
                pd.DataFrame(odata_submissions_table(base_url, aut,
                                                     projectId, formId,
                                                     'Submissions')['value'])
            submissions_machine_table = \
                pd.DataFrame(odata_submissions_table(base_url, aut, \
                                                     projectId, formId,
                                                     'Submissions.machines.machine')['value'])
            # Dataframe with nested dictionaries to flat dictionary
            submissions_table = nested_dictionary_to_df(submissions_table)
            submissions_machine_table = \
                nested_dictionary_to_df(submissions_machine_table)
            submissions_all = \
                submissions_table.merge(submissions_machine_table,
                                        left_on='__id',
                                        right_on='__Submissions-id')
            mill_filter_list = ['mill_owner', 'flour_fortified',
                                'flour_fortified_standard']
            machine_filter_list = ['commodity_milled', 'mill_type',
                                   'operational_mill', 'non_operational',
                                   'energy_source']
            mill_filter_selection = get_filters(mill_filter_list,
                                                submissions_all)
            # Filtering based on the form for machines
            for dict_key, dict_values in zip(list(choices_dict.keys()),
                                             list(choices_dict.values())):
                if dict_key in submissions_machine_table.columns:
                    submissions_machine_table = \
                        submissions_machine_table.loc[submissions_machine_table[dict_key].isin(dict_values)]
            submissions_table_filtered_machine = \
                submissions_machine_table.to_dict(orient='index')
            # submissions_table_filtered_machine_dict = \
            #    json.loads(submissions_table_filtered_machine)
            # {k: [d[k] for d in dicts] for k in dicts[0]}

            # Filtering based on the form for the mill
            # if all the selections have been deselected from one category
            for mill_key in mill_filter_selection:
                if mill_key not in list(choices_dict.keys()):
                    submissions_table.drop(submissions_table.index, inplace=True)
            # filter based on the choices
            for dict_key, dict_values in zip(list(choices_dict.keys()), list(choices_dict.values())):
                if dict_key in submissions_table.columns:
                    submissions_table[dict_key] = \
                        list(map(str, list(submissions_table[dict_key])))
                    submissions_table = \
                        submissions_table.loc[submissions_table[dict_key].isin(dict_values)]
                submissions_table.set_index('__id', inplace=True)
                submissions_filtered_dict = \
                    submissions_table.to_dict(orient='index')
                # submissions_table_filtered_dict = \
                #    json.loads(submissions_table_filtered)

                # Make submissions_table_filtered into dictionary of
                # dictionaries with machine information nested within
                submissions_dict = submissions_filtered_dict
                for submission_id in submissions_dict:
                    submissions_dict[submission_id]['machines'] = {}
                    for machine_index in submissions_table_filtered_machine:
                        machine_submission_id = \
                            submissions_table_filtered_machine[machine_index]['__Submissions-id']
                        machine_id = \
                            submissions_table_filtered_machine[machine_index]['__id']
                        if machine_submission_id == submission_id:
                            submissions_dict[submission_id]['machines'][machine_index] = \
                                submissions_table_filtered_machine[machine_index]

        submissions_filtered_json = json.dumps(submissions_dict)
        return render_template('index.html',
                               submissions_filtered=submissions_filtered_json,
                               mill_filter_selection=mill_filter_selection,
                               title='Map', choices_dict=choices_dict)


@app.route('/download_data/')
def export_data():
    # Export all the data from ODK form
    r = export_submissions(base_url, aut, projectId, formId)
    file_name = formId
    if not os.path.exists('files'):
        outdir = os.makedirs('files')

        # Saves the file also locally
        with open(f'files/{file_name}.zip', 'wb') as zip:
            zip.write(r.content)
    basename = os.path.basename(f'files/{file_name}.zip')
    dirname = os.path.dirname(os.path.abspath(f'files/{file_name}.zip'))
    send_from_directory(dirname, basename, as_attachment=True)

    # Stream the response as the data is generated
    response = Response(r.content, content_type='zip')
    response.headers.set("Content-Disposition", "attachment",
                         filename=f"{file_name}.zip")
    return response
