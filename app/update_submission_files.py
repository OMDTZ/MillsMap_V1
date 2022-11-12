import os, json, time

from app.odk_requests import number_submissions, odata_submissions, \
    get_submission_details, update_attachments_from_form
from app.helper_functions import flatten_dict
from app.config import *


def read_local_tables_together(folder):
    """
    Read all the csv files in a folder and combine them together
    Returns a list a dictionaries
    """

    path = os.path.join(submission_files_path, folder)
    form_names = os.listdir(path)
    csv_files = [s for s in form_names if ".csv" in s]
    # Combine the files together
    form_data = list()
    for form in csv_files:
        start_time = time.perf_counter()
        file = list()
        table_path = os.path.join(path, form)
        with open(table_path, newline='') as data_file:
            csv_file = csv.DictReader(data_file)
            for row in csv_file:
                row['non_operational'] = row['non_operational'].split(' ')
                row['energy_source'] = row['energy_source'].split(' ')
                row['commodity_milled'] = row['commodity_milled'].split(' ')
                row['Location_addr_region'] = row['Location_addr_region']
                row['Location_addr_district'] = row['Location_addr_district']
                for column in array_columns:
                    row[column] = [item.capitalize().replace('_', ' ') for item in row[column]]
                for column in single_columns:
                        row[column] = row[column].capitalize().replace('_', ' ')
                try:
                    # transform the coordinates from a string to a list
                    row['Location_mill_gps_coordinates'] = row['Location_mill_gps_coordinates'][1:-1].split(',')
                except:
                    next
                file.append(row)
        data_file.close()
        form_data.append(file)
        form_reader_time = time.perf_counter()
        print(f'Read table {form} in {form_reader_time - start_time}s')
    return [item for elem in form_data for item in elem]


def check_new_submissions_odk():
    """
    Checks whether there are new submissions in the active forms and triggers fetching them if there are
    Checks if the config file has less forms and removes those
    Updates the config file based on the latest updates
    """
    check_removed_forms(form_details, submission_files_path)
    for form_index in range(0, len(form_details)):
        # Check whether the form is active or not, or if it has not been checked before
        if form_details[form_index]['activityStatus'] == '1' or form_details[form_index]['lastChecked'] == '':
            # Check if there are new submissions in the form
            if type(form_details[form_index][
                        'lastNumberRecordsMills']) != int:  # if it's not int, double check the submissions
                try:
                    form_details[form_index]['lastNumberRecordsMills'] = int(
                        form_details[form_index]['lastNumberRecordsMills'])
                except:
                    form_details[form_index]['lastNumberRecordsMills'] = 0
            formId = form_details[form_index]['formId']
            old_submission_count = form_details[form_index]['lastNumberRecordsMills']
            new_submission_count = number_submissions(base_url, aut, projectId, formId)
            # If there are new submissions, get the submission ids that are missing
            if new_submission_count - old_submission_count > 0:
                print('New Submissions!')
                # new_sub_ids = get_new_sub_ids(table='Submissions', formId=formId, odk_details_column='instanceId',
                #                               local_column='__id')
                # Retrieve the missing submissions by fetching the form
                table = fetch_odk_submissions(base_url, aut, projectId, formId)
                # Update the figures:                update_attachments_from_form(table, figures_path, base_url, aut, projectId, formId)

                # fetch_odk_csv(base_url, aut, projectId, formId, table='Submissions', sort_column = '__id')
                # fetch_odk_csv(base_url, aut, projectId, formId, table='Submissions.machines.machine', sort_column = '__Submissions-id')
                # todo: find out if it is possible to get the submissions based on ids, and append them to the existing csv
            # Update form_config file
                form_details[form_index]['lastNumberRecordsMachines'] = len(table)
            form_details[form_index]['lastNumberRecordsMills'] = new_submission_count
            form_details[form_index]['lastChecked'] = time.localtime(time.time())
            update_form_config_file(form_details)


def get_new_sub_ids(table, formId, odk_details_column, local_column):
    """
    Retrieve a column from odk details, compare it to the locally saved list of ids
    Return a list of ids that are in odk but are not present in the locally saved file
    """
    submission_id_list = get_form_column(formId, local_column)
    submission_odk_details = get_submission_details(base_url, aut, projectId, formId, table)
    submission_odk_ids = [row[odk_details_column] for row in submission_odk_details]
    submission_odk_ids = sorted(submission_odk_ids)
    new_submission_ids = list(set(submission_odk_ids) - set(submission_id_list))
    return new_submission_ids


def check_removed_forms(form_details, submission_files_path):
    """
    Go through the form_details and if there are files in the folder that do not exist in the form details,
    remove them.
    @param form_details: a dictionary of details for the odk formIds, projectIds, activityStatus etc.
        retrieved from config.csv file
    @param submission_files_path: string for the path in which folder are the saved odk submissions saved
    """
    form_names = [form['formId'] for form in form_details]
    path = submission_files_path
    sub_files = os.listdir(path)
    sub_files = [file for file in sub_files if '.csv' in file]
    for file in sub_files:
        file_name = os.path.splitext(file)[0]
        if file_name not in form_names:
            mills_path = os.path.join(path, file)
            os.remove(mills_path)
            print(f'Removed {mills_path}')
            # todo include also removing the figures automatically


def get_form_column(formId, column='__id'):
    """
    Retrieve a specific column from a csv file
    Return the column as a list
    """
    file_name = ''.join([formId, '.csv'])
    path = os.path.join(submission_files_path, file_name)
    with open(path, newline='') as data_file:
        csv_file = csv.DictReader(data_file)
        file = list()
        # combine the new and old data (new_submissions and new_flatsubs)
        for row in csv_file:
            file.append(row)
    data_file.close()
    # select only the wanted column
    formId_list = [row[column] for row in file]
    return formId_list


def update_form_config_file(form_details):
    """
    Update the config file with the new number of submissions and the new current timestamp
    @param form_details: a dictionary of details for the odk formIds, projectIds, activityStatus etc.
    retrieved from config.csv file
    """

    with open('app/static/form_config.csv', 'w', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=form_details[form_index].keys())
        writer.writeheader()
        for row in form_details:
            writer.writerow(row)


def fetch_odk_submissions(form_index, base_url: str, aut: object, projectId: str, formId: str):
    """
    Get all the data from the ODK server, merge them together and save them as a csv file
    """
    # Fetch the data
    tables_list = ['Submissions', 'Submissions.machines.machine']
    tables_data = []
    start_time = time.perf_counter()
    for table, id in zip(tables_list, id_columns):
        start_time = time.perf_counter()
        submissions_response = odata_submissions(base_url, aut, projectId, formId, table)
        mill_fetch_time = time.perf_counter()
        submissions = submissions_response.json()['value']
        flatsubs = [flatten_dict(sub) for sub in submissions]
        print(f'Fetched table {table} for the form {formId} in {mill_fetch_time - start_time}s')
        # select only the wanted columns
        # WARNING columns is a dict imported from
        # config.py via star import!!! Dont do this
        wanted_columns = columns[table]
        form_data = [{key: row[key] for key in wanted_columns} for row in flatsubs]
        flatsubs = form_data
        # if the id column is not __id then change the id column to the right column
        if id != '__id':
            for row in flatsubs:
                row['machine_id'] = row['__id']
                row['__id'] = row[id]
                del row[id]
        # sort the data base on the '__id' column
        flatsubs = sorted(flatsubs, key=lambda d: d['__id'])
        tables_data.append(flatsubs)
    all_tables = []
    # Merge the tables together iteratively
    mills_iterator = 0
    for i in range(0, len(tables_data[1])):
        machines_iterator = i
        # if the ids are the same at the machine and the mill, update the data to include the mills data
        if tables_data[0][mills_iterator]['__id'] == tables_data[1][machines_iterator]['__id']:
            mill_update = tables_data[0][mills_iterator].copy()
            all_tables.append(mill_update)
            machine_update = tables_data[1][machines_iterator].copy()
            all_tables[i].update(machine_update)
        else:
            mills_iterator += 1
            mill_update = tables_data[0][mills_iterator].copy()
            all_tables.append(mill_update)
            machine_update = tables_data[1][machines_iterator].copy()
            all_tables[i].update(machine_update)
    merging_tables_time = time.perf_counter()
    print(f'Merged the mills and machines in {merging_tables_time - start_time}s')
    # open a file for writing
    file_name = ''.join([formId, '.csv'])
    dir = 'app/submission_files'
    path = os.path.join(dir, file_name)
    for row in all_tables:
        # transform the columns to have capitals and no underscores
        row['interviewee_mill_owner'] = row['interviewee_mill_owner'].capitalize()
        row['interviewee_mill_owner'] = row['interviewee_mill_owner'].replace('_', ' ')

    with open(path, 'w') as data_file:
        csv_writer = csv.writer(data_file)
        # Counter variable used for writing
        count = 0
        # write the rows
        for emp in all_tables:
            try:
                emp['geo'] = ','.join(str(l) for l in (emp['Location_mill_gps_coordinates'][-2:-4:-1]))
            except:
                print('No gps coordinates found')
            if count == 0:
                # Writing headers of CSV file
                header = emp.keys()
                csv_writer.writerow(header)
                count += 1
            # Writing data of CSV file
            csv_writer.writerow(emp.values())
        data_file.close()

    # Update the config file
    new_submission_count = number_submissions(base_url, aut, projectId, formId)
    form_details[form_index]['lastNumberRecordsMills'] = new_submission_count
    form_details[form_index]['lastNumberRecordsMachines'] = len(all_tables)
    form_details[form_index]['lastChecked'] = time.localtime(time.time())
    update_form_config_file(form_details)
    return all_tables
