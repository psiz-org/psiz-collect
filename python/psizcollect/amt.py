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

Functions:
    create_hit_on_host:
    create_hit:
    external_question_xml:

"""

import datetime
import json
from pathlib import Path

import boto3
import paramiko


def create_hit_on_host(
        host_node, aws_profile, is_live=False, n_assignment=1, verbose=0):
    """Create AMT HIT on host node."""
    # Connect.
    client = paramiko.SSHClient()
    client.load_system_host_keys()
    client.connect(
        host_node["ip"], port=host_node["port"], username=host_node["user"]
    )

    cmd_python = (
        "from psizcollect import amt; "
        "amt.create_hit('{0}', '{1}', {2}, {3}, verbose={4})"
    ).format(
        host_node["hitConfig"], aws_profile, n_assignment, is_live, verbose
    )
    cmd = (
        '{0} -c "{1}"'
    ).format(
        host_node["python"], cmd_python
    )
    _, stdout, stderr = client.exec_command(cmd)
    if verbose > 0:
        print(stdout.readlines())
        print(stderr.readlines())
    client.close()


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
    if (n_assignment > 0) and (n_assignment <= 9):  # TODO Temporary safety check.
        # Load AMT configuration file.
        with open(fp_hit_config) as f:
            hit_cfg = json.load(f)

        if fp_log is None:
            fp_log = Path.home() / Path('.amt-voucher', 'logs', aws_profile)
        # Create log directories if necessary.
        if not fp_log.exists():
            fp_log.mkdir(parents=True)

        ymd_str = datetime.datetime.today().strftime('%Y-%m-%d')

        # Start client.
        session = boto3.Session(profile_name=aws_profile)
        # Any clients created from this session will use credentials
        # from the [<aws_profile>] section of ~/.aws/credentials.

        endpoint_url = 'https://mturk-requester-sandbox.us-east-1.amazonaws.com'
        if is_live:
            endpoint_url = 'https://mturk-requester.us-east-1.amazonaws.com'
        amt_client = session.client('mturk', endpoint_url=endpoint_url)

        # Create question XML.
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
        hitId = response['HIT']['HITId']

        if is_live:
            with open(fp_log / Path('hit_live.txt'), 'a') as f:
                f.write(
                    "{0}, {1}, {2}\n".format(hitId, ymd_str, fp_hit_config)
                )
            if verbose > 0:
                print(
                    "    Created live HIT {0}: {1} assignment(s)".format(
                        hitId, n_assignment
                    )
                )
        else:
            with open(fp_log / Path('hit_sandbox.txt'), 'a') as f:
                f.write(
                    "{0}, {1}, {2}\n".format(hitId, ymd_str, fp_hit_config)
                )
            if verbose > 0:
                print(
                    "    Created sandbox HIT {0}: {1} assignment(s)".format(
                        hitId, n_assignment
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


def check_for_outstanding_assignments(
        aws_profile, is_live, is_all=False, verbose=0):
    """Check for HITs that are not done.

    Check for pending or available assignments.
    """
    fp_log = Path('/Users/bdroads/Projects/psiz-projects/imagenet/hits')  # TODO
    fp_hit_log = get_hit_log(fp_log, aws_profile, is_live)

    if verbose > 0:
        print_mode(is_live)

    # AMT client.
    session = boto3.Session(profile_name=aws_profile)
    amt_client = session.client(
        'mturk', endpoint_url=get_endpoint_url(is_live)
    )

    #  Assemble HIT ID list.
    hit_id_list = []
    if is_all:
        hit_id_list = get_all_hits(amt_client)
    else:
        hit_id_list = get_log_hits(fp_hit_log)

    # Check HITs.
    n_hit = len(hit_id_list)
    print('Number of HITs: {0}\n'.format(n_hit))
    for i_hit in range(n_hit):
        hit_info = inspect_hit(amt_client, hit_id_list[i_hit])
        is_done = hit_is_done(hit_info)
        if not is_done:
            print_hit_summary(hit_info)


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


def hit_is_done(hit_info):
    """Check if HIT is done."""
    is_done = False
    if hit_info['is_expired']:
        is_done = True
    else:
        n_submitted = hit_info['n_complete'] + hit_info['n_waiting']
        if n_submitted == hit_info['n_max']:
            is_done = True
    return is_done


def hit_needs_approval(hit_info):
    """Determine if HIT needs approval."""
    needs_approval = False
    if hit_info['n_waiting'] > 0:
        needs_approval = True
    # n_submitted = hit_info['n_complete'] + hit_info['n_waiting']
    # if hit_info['is_expired']:
    #     if (hit_info['n_complete'] + hit_info['n_available']) != hit_info['n_max']:
    #         needs_approval = True
    # else:
    #     if (
    #         hit_info['n_complete'] + hit_info['n_pending'] +
    #         hit_info['n_available']
    #     ) != hit_info['n_max']:
    #         needs_approval = True
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
        endpoint_url = 'https://mturk-requester-sandbox.us-east-1.amazonaws.com'
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
    hit_id_list = []
    if fp_hit_log.exists():
        f = open(fp_hit_log, 'r')
        for ln in f:
            parts = ln.split(',')
            # print(parts[0].strip())
            hit_id_list.append(
                parts[0].strip()
            )
        f.close()
    return hit_id_list


def get_hit_log(fp_log, aws_profile, is_live):
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
