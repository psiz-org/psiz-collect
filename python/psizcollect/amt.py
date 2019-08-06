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

Example usage:
# TODO add checks (budget, etc.)
# Create a live HIT.
n_assignment  = 4
is_live = False
aws_profile = 'roads'


"""

import datetime
import json
from pathlib import Path

import boto3
import paramiko


def create_hit_on_host(
        host_node, aws_profile, is_live=False, n_assignment=1, verbose=0):
    """Create AMT HIT on host node."""
    # TODO Temporary safety checks.
    if n_assignment <= 9:
        # Connect.
        client = paramiko.SSHClient()
        client.load_system_host_keys()
        client.connect(
            host_node["ip"], port=host_node["port"], username=host_node["user"]
        )

        cmd_python = (
            "from psizcollect import amt; "
            "amt.create_hit('{0}', {1}, {2}, {3})"
        ).format(
            host_node["hitConfig"], aws_profile, n_assignment, is_live
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
        fp_hit_config, aws_profile, n_assignment, is_live, fp_app=None,
        verbose=0):
    """Create AMT HIT using the provided hit configuration file.

    Arguments:
        fp_hit_config:
        aws_profile:
        n_assignment:
        is_live:
        fp_app:
    """
    # Load AMT configuration file.
    with open(fp_hit_config) as f:
        hit_cfg = json.load(f)

    if fp_app is None:
        fp_app = Path.home() / Path('.amt-voucher')

    # Create log directories if necessary.
    fp_logs = fp_app / Path('logs', aws_profile)
    if not fp_logs.exists():
        fp_logs.mkdir(parents=True)

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
        with open(fp_logs / Path('hit_live.txt'), 'a') as f:
            f.write(
                "{0}, {1}, {2}\n".format(hitId, ymd_str, fp_hit_config)
            )
        if verbose > 0:
            print("    Created live HIT {0}".format(hitId))
    else:
        with open(fp_logs / Path('hit_sandbox.txt'), 'a') as f:
            f.write(
                "{0}, {1}, {2}\n".format(hitId, ymd_str, fp_hit_config)
            )
        if verbose > 0:
            print("    Created sandbox HIT {0}".format(hitId))


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
