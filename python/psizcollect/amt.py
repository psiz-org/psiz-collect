
# -*- coding: utf-8 -*-
# Copyright 2019 The PsiZ Authors. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================

"""Module for handling Amazon Mechanical Turk HITs.

It is assumed that credentials are stored in the [<aws_profile>]
section of ~/.aws/credentials.

Functions:
    create_hit:
    external_question_xml:
    write_to_log:

"""

import datetime
import json
from pathlib import Path

import boto3
import numpy as np
import pandas
import paramiko

# TODO must refactor code to handle fact that HIT info is expired on AMT servers.

def create_hit(
        fp_hit_config, aws_profile, n_assignment, is_live, fp_log=None,
        verbose=0):
    """Create AMT HIT using the provided hit configuration file.

    Arguments:
        fp_hit_config:
        aws_profile:
        n_assignment:
        is_live:
        fp_log:
    """
    if (n_assignment > 0) and (n_assignment <= 9):
        # Load AMT configuration file.
        with open(fp_hit_config) as f:
            hit_cfg = json.load(f)

        # Set path for HIT log.
        if fp_log is None:
            fp_log = Path.home() / Path('.amt-voucher', 'logs')
            if not fp_log.exists():
                fp_log.mkdir(parents=True)
        else:
            fp_log = Path(fp_log)

        # Create AMT client.
        session = boto3.Session(profile_name=aws_profile)
        amt_client = session.client(
            'mturk', endpoint_url=get_endpoint_url(is_live)
        )

        # Create the HIT.
        question_xml = external_question_xml(hit_cfg['QuestionUrl'])
        response = amt_client.create_hit(
            MaxAssignments=n_assignment,
            # AutoApprovalDelayInSeconds=123,
            LifetimeInSeconds=hit_cfg['LifetimeInSeconds'],
            AssignmentDurationInSeconds=hit_cfg['AssignmentDurationInSeconds'],
            Reward=hit_cfg['Reward'],
            Title=hit_cfg['Title'],
            Keywords=hit_cfg['Keywords'],
            Description=hit_cfg['Description'],
            Question=question_xml,
            # RequesterAnnotation='string',
            QualificationRequirements=hit_cfg['QualificationRequirements'],
            # UniqueRequestToken='string',
            # AssignmentReviewPolicy={
            #     'PolicyName': 'string',
            #     'Parameters': [
            #         {
            #             'Key': 'string',
            #             'Values': [
            #                 'string',
            #             ],
            #             'MapEntries': [
            #                 {
            #                     'Key': 'string',
            #                     'Values': [
            #                         'string',
            #                     ]
            #                 },
            #             ]
            #         },
            #     ]
            # },
            # HITReviewPolicy={
            #     'PolicyName': 'string',
            #     'Parameters': [
            #         {
            #             'Key': 'string',
            #             'Values': [
            #                 'string',
            #             ],
            #             'MapEntries': [
            #                 {
            #                     'Key': 'string',
            #                     'Values': [
            #                         'string',
            #                     ]
            #                 },
            #             ]
            #         },
            #     ]
            # },
            # HITLayoutId='string',
            # HITLayoutParameters=[
            #     {
            #         'Name': 'string',
            #         'Value': 'string'
            #     },
            # ]
        )
        hit_id = response['HIT']['HITId']

        # Record the creation of the HIT.
        write_to_log(fp_log, aws_profile, is_live, hit_id, fp_hit_config)

        if verbose > 0:
            if is_live:
                print(
                    "    Created live HIT {0}: {1} assignment(s)".format(
                        hit_id, n_assignment
                    )
                )
            else:
                print(
                    "    Created sandbox HIT {0}: {1} assignment(s)".format(
                        hit_id, n_assignment
                    )
                )
    else:
        print("Cannot create HIT with {0} assignment(s).".format(n_assignment))


def create_fake_hit(
        fp_hit_config, aws_profile, n_assignment, is_live, fp_log=None,
        verbose=0):
    """Create AMT HIT using the provided hit configuration file.

    Arguments:
        fp_hit_config:
        aws_profile:
        n_assignment:
        is_live:
        fp_log:
    """
    if (n_assignment > 0) and (n_assignment <= 9):
        # Load AMT configuration file.
        with open(fp_hit_config) as f:
            hit_cfg = json.load(f)

        # Set path for HIT log.
        if fp_log is None:
            fp_log = Path.home() / Path('.amt-voucher', 'logs')
            if not fp_log.exists():
                fp_log.mkdir(parents=True)
        else:
            fp_log = Path(fp_log)

        # Create AMT client.
        session = boto3.Session(profile_name=aws_profile)
        amt_client = session.client(
            'mturk', endpoint_url=get_endpoint_url(is_live)
        )

        # Create the HIT.
        question_xml = (
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<QuestionForm xmlns="http://mechanicalturk.amazonaws.com/AWSMechanicalTurkDataSchemas/2017-11-06/QuestionForm.xsd">'
            '<Overview>'
            '<Title>Fake HIT</Title>'
            '<Text>Please answer the following question. Your HIT will be automatically approved regardless of your answer.</Text>'
            '</Overview>'
            '<Question>'
            '<QuestionIdentifier>question_0</QuestionIdentifier>'
            '<QuestionContent><Text>Who shot first?</Text></QuestionContent>'
            '<AnswerSpecification>'
            '<SelectionAnswer>'
            '<StyleSuggestion>radiobutton</StyleSuggestion>'
            '<Selections>'
            '<Selection>'
            '<SelectionIdentifier>han</SelectionIdentifier>'
            '<Text>Han Solo</Text>'
            '</Selection>'
            '<Selection>'
            '<SelectionIdentifier>greedo</SelectionIdentifier>'
            '<Text>Greedo</Text>'
            '</Selection>'
            '</Selections>'
            '</SelectionAnswer>'
            '</AnswerSpecification>'
            '</Question>'
            '</QuestionForm>'
        )

        response = amt_client.create_hit(
            MaxAssignments=n_assignment,
            AutoApprovalDelayInSeconds=5,
            LifetimeInSeconds=hit_cfg['LifetimeInSeconds'],
            AssignmentDurationInSeconds=hit_cfg['AssignmentDurationInSeconds'],
            Reward=hit_cfg['Reward'],
            Title=hit_cfg['Title'],
            Keywords=hit_cfg['Keywords'],
            Description=hit_cfg['Description'],
            Question=question_xml,
            # RequesterAnnotation='string',
            QualificationRequirements=hit_cfg['QualificationRequirements'],
            # UniqueRequestToken='string',
            # AssignmentReviewPolicy={
            #     'PolicyName': 'string',
            #     'Parameters': [
            #         {
            #             'Key': 'string',
            #             'Values': [
            #                 'string',
            #             ],
            #             'MapEntries': [
            #                 {
            #                     'Key': 'string',
            #                     'Values': [
            #                         'string',
            #                     ]
            #                 },
            #             ]
            #         },
            #     ]
            # },
            # HITReviewPolicy={
            #     'PolicyName': 'string',
            #     'Parameters': [
            #         {
            #             'Key': 'string',
            #             'Values': [
            #                 'string',
            #             ],
            #             'MapEntries': [
            #                 {
            #                     'Key': 'string',
            #                     'Values': [
            #                         'string',
            #                     ]
            #                 },
            #             ]
            #         },
            #     ]
            # },
            # HITLayoutId='string',
            # HITLayoutParameters=[
            #     {
            #         'Name': 'string',
            #         'Value': 'string'
            #     },
            # ]
        )
        hit_id = response['HIT']['HITId']

        # Record the creation of the HIT.
        write_to_log(fp_log, aws_profile, is_live, hit_id, fp_hit_config)

        if verbose > 0:
            if is_live:
                print(
                    "    Created live HIT {0}: {1} assignment(s)".format(
                        hit_id, n_assignment
                    )
                )
            else:
                print(
                    "    Created sandbox HIT {0}: {1} assignment(s)".format(
                        hit_id, n_assignment
                    )
                )
    else:
        print("Cannot create HIT with {0} assignment(s).".format(n_assignment))


def external_question_xml(question_url):
    """Return AMT-formatted XML for external question.

    See: https://docs.aws.amazon.com/AWSMechTurk/latest/AWSMturkAPI/
    ApiReference_ExternalQuestionArticle.html
    """
    question_xml = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<ExternalQuestion xmlns="http://mechanicalturk.amazonaws.com/'
        'AWSMechanicalTurkDataSchemas/2006-07-14/ExternalQuestion.xsd">'
        '<ExternalURL>{0}</ExternalURL>'
        '<FrameHeight>0</FrameHeight>'
        '</ExternalQuestion>'
    ).format(question_url)
    return question_xml


def write_to_log(
        fp_log, aws_profile, is_live, hit_id, fp_hit_config):
    """Record HIT creation in log.

    Creating an entry adds a row to the appopriate log file. Each row
    indicates the HIT ID, time of creation (YYYY-MM-DD), and name of
    the configuration file.

    Arguments:
        fp_log:
        aws_profile:
        is_live:
        hit_id:
        fp_hit_config:
    """
    # Create log directories if necessary.
    fp_log_profile = fp_log / Path(aws_profile)
    if not fp_log_profile.exists():
        fp_log_profile.mkdir(parents=True)

    ymd_str = datetime.datetime.today().strftime('%Y-%m-%d')
    fp_hit_log = get_hit_log_filepath(fp_log, aws_profile, is_live)
    with open(fp_hit_log, 'a') as f:
        f.write(
            "{0}, {1}, {2}\n".format(hit_id, ymd_str, fp_hit_config)
        )


def check_for_outstanding_assignments(
        aws_profile, is_live, fp_log=None, n_last=10, verbose=0):
    """Check for HITs that are not done.

    Check for pending or available assignments.

    Arguments:
        aws_profile:
        is_live:
        fp_log:
        n_last: The number of most recent HITs to check.
        verbose (optional):

    Returns:
        n_remain_total

    """
    if verbose > 0:
        print_mode(is_live)

    # AMT client.
    session = boto3.Session(profile_name=aws_profile)
    amt_client = session.client(
        'mturk', endpoint_url=get_endpoint_url(is_live)
    )

    #  Assemble HIT ID list.
    hit_id_list = []
    if fp_log is None:
        hit_id_list = get_all_hits(amt_client)
    else:
        fp_log = Path(fp_log)
        fp_hit_log = get_hit_log_filepath(fp_log, aws_profile, is_live)
        hit_id_list = get_log_hits(fp_hit_log)
    hit_id_list = hit_id_list[-n_last:]

    # Check HITs.
    n_remain_total = 0
    n_hit = len(hit_id_list)
    for i_hit in range(n_hit):
        hit_info = inspect_hit(amt_client, hit_id_list[i_hit])
        n_remain = check_remaining(hit_info)
        if n_remain != 0:
            n_remain_total = n_remain_total + n_remain
    return n_remain_total


def inspect_hit(amt_client, hit_id):
    """Inspect HIT for reviewable assignments."""
    resp = amt_client.get_hit(HITId=hit_id)

    hit_id = resp['HIT']['HITId']
    title = resp['HIT']['Title']
    hit_status = resp['HIT']['HITStatus']
    n_max = resp['HIT']['MaxAssignments']
    n_complete = resp['HIT']['NumberOfAssignmentsCompleted']
    n_pending = resp['HIT']['NumberOfAssignmentsPending']
    n_available = resp['HIT']['NumberOfAssignmentsAvailable']
    n_waiting = n_max - (n_complete + n_pending + n_available)
    dt_expiration = resp['HIT']['Expiration']
    is_expired = False
    dt_now = datetime.datetime.now(datetime.timezone.utc)
    if dt_expiration < dt_now:
        is_expired = True
    return {
        'hit_id': hit_id,
        'title': title,
        'hit_status': hit_status,
        'n_max': n_max,
        'n_complete': n_complete,
        'n_waiting': n_waiting,
        'n_pending': n_pending,
        'n_available': n_available,
        'is_expired': is_expired
    }


def check_remaining(hit_info):
    """Check if HIT is done."""
    n_remain = 0
    if hit_info['is_expired']:
        n_remain = 0
    else:
        n_submitted = hit_info['n_complete'] + hit_info['n_waiting']
        n_remain = hit_info['n_max'] - n_submitted
    return n_remain


def hit_needs_approval(hit_info):
    """Determine if HIT needs approval."""
    needs_approval = False
    if hit_info['n_waiting'] > 0:
        needs_approval = True
    return needs_approval


def print_hit_summary(hit_info):
    """Print HIT summary.

    Arguments:
        hit_info: Dictionary of HIT information..

    """
    print('HIT ID: {0}'.format(hit_info['hit_id']))
    print('  Title: {0}'.format(hit_info['title']))
    print('  Status: {0}'.format(hit_info['hit_status']))
    print('  max | comp, wait, pend, avail')
    print('   {0: <2} |   {1: <2},   {2: <2},   {3: <2},    {4: <2} '.format(
            hit_info['n_max'], hit_info['n_complete'], hit_info['n_waiting'],
            hit_info['n_pending'], hit_info['n_available']
        )
    )


def get_endpoint_url(is_live):
    """Return endpoint URL for AMT.

    Arguments:
        is_live: Boolean indicating whether the endpoint should be the
            live or sandbox site.

    Returns:
        endpoint_url: String indicating endpoint URL.

    """
    if is_live:
        endpoint_url = 'https://mturk-requester.us-east-1.amazonaws.com'
    else:
        endpoint_url = (
            'https://mturk-requester-sandbox.us-east-1.amazonaws.com'
        )
    return endpoint_url


def get_all_hits(amt_client):
    """Get all reviewable HITs associated with profile."""
    hit_id_list = []
    # Include all reviewable HITs in list.
    resp = amt_client.list_reviewable_hits()
    n_hit = resp['NumResults']
    for i_hit in range(n_hit):
        hit_id_list.append(
            resp['HITs'][i_hit]['HITId']
        )
    return hit_id_list


def get_log_hits(fp_hit_log):
    """Only review HITS stored in logs."""
    fp_hit_log = Path(fp_hit_log)

    hit_id_list = []
    if fp_hit_log.exists():
        f = open(fp_hit_log, 'r')
        for ln in f:
            parts = ln.split(',')
            hit_id_list.append(
                parts[0].strip()
            )
        f.close()
    return hit_id_list


def get_hit_log_filepath(fp_log, aws_profile, is_live):
    """Return filepath for hit log.

    Arguments:
        fp_log:
        aws_profile:
        is_live:

    Returns:
        fp_hit_log:

    """
    if is_live:
        fp_hit_log = fp_log / Path(aws_profile, 'hit_live.txt')
    else:
        fp_hit_log = fp_log / Path(aws_profile, 'hit_sandbox.txt')
    return fp_hit_log


def print_mode(is_live):
    """Print AMT mode.

    Arguments:
        is_live:
    """
    if is_live:
        print("Mode: LIVE")
    else:
        print("Mode: SANDBOX")


def check_time(utc_forbidden):
    """Check if HIT is allowed to be created at this time.

    Times are assumed to be UTC.

    Arguments:
        utc_forbidden: A list of UTC hours that indicates times when
            creating new HITs is forbidden.

    Returns:
        is_appropriate_time: A boolean indicating if the HIT can be
            created at this time.

    """
    is_appropriate_time = False
    dt_now = datetime.datetime.utcnow()
    if np.sum(np.equal(dt_now.hour, utc_forbidden)) == 0:
        is_appropriate_time = True
    return is_appropriate_time


def wait_time(utc_forbidden):
    """Determine how many seconds until HIT is allowed to be created.

    Times are assumed to be UTC.

    Arguments:
        utc_forbidden: A list of UTC hours that indicates times when
            creating new HITs is forbidden.

    Returns:
        delta_t: A datetime.timedelta objecj indicating the time until
            the HIT can be created.

    """
    dt_now = datetime.datetime.utcnow()

    utc_hours = np.arange(0, 24)
    utc_allowed = []
    for hour in utc_hours:
        if np.sum(np.equal(hour, utc_forbidden)) == 0:
            utc_allowed.append(hour)
    utc_allowed = np.asanyarray(utc_allowed, dtype=int)

    locs = np.greater_equal(utc_allowed, dt_now.hour)
    utc_allowed_future = utc_allowed[locs]

    if len(utc_allowed_future) == 0:
        utc_next = dt_now + datetime.timedelta(days=1)
        utc_next = utc_next.replace(hour=utc_allowed[0])
    else:
        utc_next = dt_now
        utc_next = utc_next.replace(hour=utc_allowed_future[0])
        utc_next = utc_next.replace(minute=0)
        utc_next = utc_next.replace(second=1)

    delta_t = utc_next - dt_now
    return delta_t


def compute_expenditures(hit_id_list, aws_profile, is_live):
    """Compute expenditures.

    For each HIT:
    - Determine the reward per assignment
    - Determine the number of approved (i.e., paid) assignments
    - Determine AMT's commission on the HIT.

    Arguments:
        hit_id_list: List of HIT IDs to consider.
        aws_profile: The AWS profile to use.
        is_live: Boolean indicating whether to probe the live or
            sandbox database.

    Returns:
        total_expenditure: Total expenditures.

    """
    # Create AMT client.
    session = boto3.Session(profile_name=aws_profile)
    amt_client = session.client(
        'mturk', endpoint_url=get_endpoint_url(is_live)
    )

    # Pre-allocate variables.
    n_hit = len(hit_id_list)
    reward_list = np.zeros([n_hit])
    n_approve_list = np.zeros([n_hit])
    commission_rate_list = np.zeros([n_hit])

    for idx, hit_id in enumerate(hit_id_list):
        r = amt_client.get_hit(HITId=hit_id)
        n_max_assignment = r['HIT']['MaxAssignments']
        reward_list[idx] = r['HIT']['Reward']
        commission_rate_list[idx] = determine_amt_commission_rate(
            n_max_assignment
        )
        r = amt_client.list_assignments_for_hit(
            HITId=hit_id, AssignmentStatuses=['Approved']
        )
        n_approve_list[idx] = r['NumResults']

    # Total expenditures.
    hit_reward = n_approve_list * reward_list
    hit_expenditure = hit_reward * (1 + commission_rate_list)
    total_expenditure = np.sum(hit_expenditure)
    return total_expenditure


def determine_amt_commission_rate(n_max_assignment):
    """Determine AMT commission.

    Arguments:
        n_max_assignment: The maximum number of assignments associated
            with the HIT.
    """
    amt_commision = .2
    if n_max_assignment > 9:
        amt_commision = .4
    return amt_commision


def assign_qualification(aws_profile, is_live, worker_id, qualification_id, int_val=0):
    """Assign qualification to worker.

    Arguments:
        aws_profile: A string indicating the AWS profile.
        is_live: A boolean indicating if the HIT is live or not.
        worker_id: A string indicating the worker ID.
        qualification_id: A string indicating the qualification ID.

    """
    int_val = int(int_val)

    # Create AMT client.
    session = boto3.Session(profile_name=aws_profile)
    amt_client = session.client(
        'mturk', endpoint_url=get_endpoint_url(is_live)
    )
    response = amt_client.associate_qualification_with_worker(
        QualificationTypeId=qualification_id,
        WorkerId=worker_id,
        IntegerValue=int_val,
        SendNotification=False
    )
