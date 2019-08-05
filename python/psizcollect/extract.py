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

"""Moduel for extracting observations from a MySQL database.

It is assumed that your MySQL credentials are stored at
`~/.mysql/credentials` in the `psiz` block (see README). If
they are stored somewhere else, with a different format, the variable
`fp_mysql_credentials`, `host`, `user`,`passwd`, and `db` need to be
changed.

"""

import argparse
import configparser
from datetime import datetime
import os
from pathlib import Path

import mysql.connector
import numpy as np
import pandas as pd
import psiz.trials
import psiz.preprocess
import psizcollect.pipes

# Consants used/assumed in the MySQL database.
STATUS_CREATED = 0  # Incomplete and not expired.
STATUS_ACCEPTED = 1  # Completed and met grading criteria.
STATUS_EXPIRED = 2  # Incomplete and expired.
STATUS_DROPPED = 3  # Completed but did not meet grading criteria.
N_MAX_REF = 8


def extract_observations(
        project_id, grade_mode="lenient", grade_threshold=.8, verbose=0):
    """Extract and process observations from MySQL database.

    Data stored in a MySQL database is extracted and processed into
    three separate files: obs.hdf5, meta.txt, and summary.txt.

    This script creates a psiz.trials.Observations object for the
    user-supplied `project_id`. All COMPLETED assignments (i.e.,
    status_code = 1 or status_code=3) belonging to the requested
    project are graded to see if they meet threshold for being
    accepted and included in the final Observations object.

    Completed assignments are graded based on catch trial performance
    and dropped if they do not meet the provided criterion. In
    addition, the status code of assignments that do not meet criterion
    is updated to status_code=3. After grading, all catch trials are
    removed before saving the observations to disk.

    The accepted observations are saved in a directory with the same
    name as the supplied `project_id`, i.e.,
    `.psiz-collect/projects/<project_id>/obs.hdf5` (see README for more
    regarding the assumed directory structure).

    In addition to the observations object, metadata (meta.txt) and a
    summary is generated (summary.txt). The metadata file can be used
    to map agent ID's back to the MySQL database's assignment IDs.

    Arguments:
        project_id: String indicating project ID. This should
        correspond to a string used in the `project_id` column of the
            `assignments` table.
        grade_mode (optional): The grade mode to use when grading catch trials.
            See psiz.preprocessing.grade_catch_trials for details
            regarding the accepted inputs.
        grade_threshold (optional): The grading threshold to use for determining
            if an assignment should be accepted or dropped.
        verbose (optional): Verbosity of output.

    """
    fp_mysql_credentials = Path.home() / Path('.mysql/credentials')
    fp_app = Path.home() / Path('.psiz-collect')

    # Set the project path.
    fp_project = fp_app / Path('projects', project_id)
    if not os.path.exists(fp_project):
        os.makedirs(fp_project)
    fp_obs = fp_project / Path("obs.hdf5")
    fp_meta = fp_project / Path("meta.txt")
    fp_summary = fp_project / Path("summary.txt")

    # Establish MySQL connection using stored credentials.
    config = configparser.ConfigParser()
    config.read(fp_mysql_credentials)
    my_cxn = mysql.connector.connect(
        host=config['psiz']['servername'],
        user=config['psiz']['username'],
        passwd=config['psiz']['password'],
        database=config['psiz']['database']
    )

    # Retrieve assignment_id's of all participants in the database.
    tbl_assignment = fetch_assignment(my_cxn, project_id)

    # Create psiz.trials.Observations object.
    obs, meta = assemble_accepted_obs(
        my_cxn, tbl_assignment, grade_mode, grade_threshold
    )
    # Close the connection.
    my_cxn.close()

    # Save observations, metadata, and summary.
    obs.save(fp_obs)
    psizcollect.pipes.write_metadata(meta, fp_meta)
    psizcollect.pipes.write_summary(obs, meta, fp_summary)


def fetch_assignment(my_cxn, project_id):
    """Fetch data in assignment table.

    Arguments:
        my_cursor: A MySQL cursor.
        project_id: The requested project ID.

    Returns:
        tbl_assignment: All of the assignment table information
            organized as a dictionary.

    """
    query_assignment = (
        "SELECT assignment_id, protocol_id, worker_id, status_code, "
        "begin_hit, end_hit FROM assignment WHERE project_id=%s"
    )
    vals = (project_id,)
    my_cursor = my_cxn.cursor()
    my_cursor.execute(query_assignment, vals)
    sql_result = my_cursor.fetchall()
    my_cursor.close()

    assignment_id_list = []
    protocol_id_list = []
    worker_id_list = []
    status_list = []
    begin_hit = []
    end_hit = []
    duration_hit_min = []

    n_row = len(sql_result)
    for i_row in range(n_row):
        assignment_id_list.append(sql_result[i_row][0])
        protocol_id_list.append(sql_result[i_row][1])
        worker_id_list.append(sql_result[i_row][2])
        status_list.append(sql_result[i_row][3])
        begin_datetime = sql_result[i_row][4]
        end_datetime = sql_result[i_row][5]

        begin_hit.append(begin_datetime)
        end_hit.append(end_datetime)
        duration_datetime = end_datetime - begin_datetime
        duration_hit_min.append(
            duration_datetime.total_seconds() / 60.
        )

    tbl_assignment = {
        "assignment_id": np.asarray(assignment_id_list),
        "protocol_id": np.asarray(protocol_id_list),
        "worker_id": np.asarray(worker_id_list),
        "status_code": np.asarray(status_list),
        "begin_hit": begin_hit,
        "end_hit": end_hit,
        "duration_hit_min": np.asarray(duration_hit_min)
    }
    return tbl_assignment


def assemble_accepted_obs(
        my_cxn, tbl_assignment, grade_mode, grade_thresh):
    """Create Observations object for accepted data.

    Arguments:
        my_cxn: A MySQL connection.
        assignment_id_list: A list of database assignment_id's.
    """
    n_assignment = len(tbl_assignment["assignment_id"])

    worker_list = pd.unique(tbl_assignment["worker_id"])
    agent_id_list = np.arange(len(worker_list))

    # Initialize.
    obs = None
    meta = {
        'assignment_id': tbl_assignment['assignment_id'],
        'agent_id': np.zeros([n_assignment], dtype=int),
        'protocol_id': tbl_assignment['protocol_id'],
        'status_code': tbl_assignment['status_code'],
        'duration_hit_min': tbl_assignment['duration_hit_min'],
        'avg_trial_rt': np.zeros([n_assignment]),
        'n_trial': np.zeros([n_assignment], dtype=int),
        'n_catch': np.zeros([n_assignment], dtype=int),
        'grade': np.zeros([n_assignment]),
        'is_accepted': np.zeros(n_assignment, dtype=bool)
    }

    query_trial = (
        "SELECT trial_id, assignment_id, n_select, is_ranked, q_idx, "
        "c1_idx, c2_idx, c3_idx, c4_idx, c5_idx, c6_idx, c7_idx, c8_idx, "
        "start_ms, c1_rt_ms, c2_rt_ms, c3_rt_ms, c4_rt_ms, c5_rt_ms, "
        "c6_rt_ms, c7_rt_ms, c8_rt_ms, submit_rt_ms "
        "FROM trial WHERE assignment_id=%s"
    )

    for idx, assignment_id in enumerate(meta["assignment_id"]):
        vals = (int(assignment_id),)
        my_cursor = my_cxn.cursor()
        my_cursor.execute(query_trial, vals)
        sql_result = my_cursor.fetchall()
        my_cursor.close()

        n_trial = len(sql_result)

        if n_trial > 0:
            agent_id = agent_id_list[np.equal(
                tbl_assignment["worker_id"][idx], worker_list
            )]
            meta['agent_id'][idx] = agent_id
            obs_agent = create_obs_agent(sql_result, agent_id)
            meta['avg_trial_rt'][idx] = np.mean(obs_agent.rt_ms)
            meta['n_trial'][idx] = n_trial
            (avg_grade, _, is_catch) = (
                psiz.preprocess.grade_catch_trials(
                    obs_agent, grade_mode=grade_mode
                )
            )
            meta['n_catch'][idx] = np.sum(is_catch)
            meta['grade'][idx] = avg_grade

            # Accept or drop.
            if (
                meta['status_code'][idx] == STATUS_ACCEPTED or
                meta['status_code'][idx] == STATUS_DROPPED
            ):
                if avg_grade < grade_thresh:
                    meta['is_accepted'][idx] = False
                    # psizcollect.pipes.update_status(
                    #     my_cxn, assignment_id, STATUS_DROPPED
                    # ) TODO
                    meta['status_code'][idx] = STATUS_DROPPED
                else:
                    meta['is_accepted'][idx] = True
                    # psizcollect.pipes.update_status(
                    #     my_cxn, assignment_id, STATUS_ACCEPTED
                    # ) TODO
                    meta['status_code'][idx] = STATUS_ACCEPTED
                    if obs is None:
                        obs = obs_agent
                    else:
                        obs = psiz.trials.stack((obs, obs_agent))

    obs = psiz.preprocess.remove_catch_trials(obs)

    return obs, meta


def create_obs_agent(sql_result, agent_id):
    """Create Observations object for single agent."""
    n_trial = len(sql_result)

    agent_id = agent_id * np.ones([n_trial], dtype=int)
    response_set = -1 * np.ones([n_trial, 1 + N_MAX_REF], dtype=int)
    n_select = np.ones([n_trial], dtype=int)
    is_ranked = np.ones([n_trial], dtype=int)
    rt_ms = np.zeros([n_trial, N_MAX_REF], dtype=int)
    rt_submit_ms = np.zeros([n_trial], dtype=int)
    for i_trial in range(n_trial):
        response_set[i_trial, 0] = sql_result[i_trial][4]
        response_set[i_trial, 1] = sql_result[i_trial][5]
        response_set[i_trial, 2] = sql_result[i_trial][6]
        response_set[i_trial, 3] = sql_result[i_trial][7]
        response_set[i_trial, 4] = sql_result[i_trial][8]
        response_set[i_trial, 5] = sql_result[i_trial][9]
        response_set[i_trial, 6] = sql_result[i_trial][10]
        response_set[i_trial, 7] = sql_result[i_trial][11]
        response_set[i_trial, 8] = sql_result[i_trial][12]

        n_select[i_trial] = sql_result[i_trial][2]
        is_ranked[i_trial] = sql_result[i_trial][3]

        rt_ms[i_trial, 0] = sql_result[i_trial][14]
        rt_ms[i_trial, 1] = sql_result[i_trial][15]
        rt_ms[i_trial, 2] = sql_result[i_trial][16]
        rt_ms[i_trial, 3] = sql_result[i_trial][17]
        rt_ms[i_trial, 4] = sql_result[i_trial][18]
        rt_ms[i_trial, 5] = sql_result[i_trial][19]
        rt_ms[i_trial, 6] = sql_result[i_trial][20]
        rt_ms[i_trial, 7] = sql_result[i_trial][21]
        rt_submit_ms[i_trial] = sql_result[i_trial][22]

    obs = psiz.trials.Observations(
        response_set, n_select=n_select, is_ranked=is_ranked,
        agent_id=agent_id, rt_ms=rt_submit_ms
    )
    return obs


def update_status(my_cxn, assignment_id, status_code):
    """Update the status code for a particular assignment.

    Arguments:
        my_cursor: A MySQL cursor.
        assignment_id: The assignment to update.
        status_code: The status code to apply.
    """
    query = (
        "UPDATE assignment SET status_code={0:d} WHERE assignment_id={1:d}"
    ).format(status_code, assignment_id)
    my_cursor = my_cxn.cursor()
    my_cursor.execute(query)
    my_cxn.commit()
    print(
        '      SET status_code={0:d} | {1} row(s) affected'.format(
            status_code, my_cursor.rowcount
        )
    )  # TODO
    my_cursor.close()
