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

"""Extract observations from MySQL database.

This script creates a psiz.trials.Observations object for the
user-supplied `project_id`. All COMPLETED assignments (i.e.,
status_code = 1) belonging to the requested project are selected from
the database and instantiated as an Observations object. The created
observations are saved in a directory with the same name as the
supplied `project_id`, i.e.,
`.psiz-collect/projects/<project_id>/obs.hdf5` (see README for more
regarding the assumed directory structure).

Important to note, the Observations object uses the MySQL database
`assignment_id` as the `agent_id`. This allows the created Observations
object to be used to make subsequent queries to the database about each
agent. For example, if a particular project includes an add-on survey.

It is assumed that your MySQL credentials are stored at
`~/.mysql/credentials` in the `psiz` block (see README). If
they are stored somewhere else, with a different format, the variable
`fp_mysql_credentials`, `host`, `user`,`passwd`, and `db` need to be
changed.

Arguments:
    See the argument parser or execute
    `python extract_observations.py -h`.

Example Usage:
    python extract_observations "birds-region"

"""

import os
import sys
import configparser
from pathlib import Path
from datetime import datetime
import argparse

import mysql.connector
import numpy as np
import pandas as pd
import psiz.trials

# Consants used/assumed in the MySQL database.
STATUS_CREATED = 0  # Incomplete and not expired.
STATUS_ACCEPTED = 1  # Completed and met grading criteria.
STATUS_EXPIRED = 2  # Incomplete and expired.
STATUS_DROPPED = 3  # Completed but did not meet grading criteria.
N_MAX_REF = 8


def main(fp_mysql_credentials, fp_app, project_id, verbose):
    """Run script."""
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
    mydb = mysql.connector.connect(
        host=config['psiz']['servername'],
        user=config['psiz']['username'],
        passwd=config['psiz']['password'],
        database=config['psiz']['database']
    )
    sql_cursor = mydb.cursor()

    # Retrieve assignment_id's of all participants in the database.
    tbl_assignment = fetch_assignment(sql_cursor, project_id)

    # Create psiz.trials.Observations object.
    obs, meta = create_obs(sql_cursor, tbl_assignment)
    obs.save(fp_obs)
    write_metadata(meta, fp_meta)

    # Save a plain text summary of the Observations.
    write_summary(obs, meta, fp_summary)


def fetch_assignment(sql_cursor, project_id):
    """Fetch data in assignment table.

    Arguments:
        sql_cursor: A MySQL cursor.
        project_id: The requested project ID.
    """
    query_assignment = (
        "SELECT assignment_id, status_code, begin_hit, end_hit, protocol_id "
        "FROM assignment WHERE project_id=%s"
    )
    vals = (project_id,)
    sql_cursor.execute(query_assignment, vals)

    sql_result = sql_cursor.fetchall()
    assignment_id_list = []
    protocol_id_list = []
    status_list = []
    begin_hit = []
    end_hit = []
    duration_hit = []

    n_row = len(sql_result)
    for i_row in range(n_row):
        assignment_id_list.append(sql_result[i_row][0])
        protocol_id_list.append(sql_result[i_row][4])
        status_list.append(sql_result[i_row][1])
        begin_datetime = sql_result[i_row][2]
        end_datetime = sql_result[i_row][3]
        begin_hit.append(begin_datetime)
        end_hit.append(end_datetime)
        duration_hit.append(end_datetime - begin_datetime)

    tbl_assignment = {
        "assignment_id": np.asarray(assignment_id_list),
        "protocol_id": np.asarray(protocol_id_list),
        "status_code": np.asarray(status_list),
        "begin_hit": begin_hit,
        "end_hit": end_hit,
        "duration_hit": duration_hit
    }
    return tbl_assignment


def create_obs(sql_cursor, tbl_assignment):
    """Create Observations object for all agents.

    Arguments:
        sql_cursor: A MySQL cursor.
        assignment_id_list: A list of database assignment_id's.
    """
    n_assignment = len(tbl_assignment["assignment_id"])

    # Initialize.
    obs = None
    meta = {
        "agent_id": tbl_assignment["assignment_id"],
        "protocol_id": tbl_assignment["protocol_id"],
        "status_code": tbl_assignment["status_code"],
        "duration_hit": tbl_assignment["duration_hit"],
        "n_trial": np.zeros([n_assignment], dtype=int),
    }

    query_trial = (
        "SELECT trial_id, assignment_id, n_select, is_ranked, q_idx, "
        "r1_idx, r2_idx, r3_idx, r4_idx, r5_idx, r6_idx, r7_idx, r8_idx, "
        "start_ms, r1_rt_ms, r2_rt_ms, r3_rt_ms, r4_rt_ms, r5_rt_ms, "
        "r6_rt_ms, r7_rt_ms, r8_rt_ms "
        "FROM trial WHERE assignment_id=%s"
    )

    for idx, assignment_id in enumerate(meta["agent_id"]):
        vals = (int(assignment_id),)
        sql_cursor.execute(query_trial, vals)

        sql_result = sql_cursor.fetchall()
        n_trial = len(sql_result)

        if n_trial > 0:
            meta["n_trial"][idx] = n_trial
            if meta["status_code"][idx] == STATUS_ACCEPTED:
                obs_agent = create_obs_agent(sql_result, assignment_id)
                if obs is None:
                    obs = obs_agent
                else:
                    obs = psiz.trials.stack((obs, obs_agent))

    return obs, meta


def create_obs_agent(sql_result, assignment_id):
    """Create Observations object for single agent."""
    n_trial = len(sql_result)

    agent_id = assignment_id * np.ones([n_trial], dtype=int)
    response_set = -1 * np.ones([n_trial, 1 + N_MAX_REF], dtype=int)
    n_select = np.ones([n_trial], dtype=int)
    is_ranked = np.ones([n_trial], dtype=int)
    rt_ms = np.zeros([n_trial, N_MAX_REF], dtype=int)
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

    rt_ms = np.max(rt_ms, axis=1)
    obs = psiz.trials.Observations(
        response_set, n_select=n_select, is_ranked=is_ranked,
        agent_id=agent_id, rt_ms=rt_ms
    )
    return obs


def write_summary(obs, meta, fp_summary):
    """Write a plain-text summary of the observations.

    Arguments:
        obs: A psiz.trials.Observations object.
        fp_summary: The file path of the summary file.

    """
    f = open(fp_summary, "w")
    f.write("Observations Summary\n")
    f.write("Last Updated: {0}\n\n".format(str(datetime.now())))

    f.write("Completed Assignments\n")
    if obs is None:
        f.write("    No observations.\n")
    else:
        n_agent = len(np.unique(obs.agent_id))
        n_unique_stim = len(np.unique(obs.stimulus_set))
        n_unique_protocol = len(np.unique(
            meta["protocol_id"][np.equal(
                meta["status_code"], STATUS_ACCEPTED
            )]
        ))
        avg_trial_rt = np.mean(obs.rt_ms) / 1000

        f.write("    n_agent: {0}\n".format(n_agent))
        f.write("    n_trial: {0}\n".format(obs.n_trial))
        f.write("    n_unique_stimuli: {0}\n".format(n_unique_stim))
        f.write("    n_unique_protocol: {0}\n".format(n_unique_protocol))
        f.write("    avg_trial_rt: {0:.2f} s\n".format(avg_trial_rt))
        f.write("\n")

        # f.write("Total Time (min)\n")
        # f.write("    min: {0:.2f}\n".format(comp_stats["time_total_m"]["min"]))
        # f.write("    max: {0:.2f}\n".format(comp_stats["time_total_m"]["max"]))
        # f.write(
        #     "    mean: {0:.2f}\n".format(comp_stats["time_total_m"]["mean"])
        # )
        # f.write("    median: {0:.2f}\n".format(
        #     comp_stats["time_total_m"]["median"]
        # ))

    wrn_msg = ''
    wrn_count = 0
    for idx, agent_id in enumerate(meta["agent_id"]):
        if (
            meta["status_code"][idx] == STATUS_ACCEPTED and
            meta["n_trial"][idx] == 0
        ):
            wrn_msg = wrn_msg + (
                '    agent_id={0} | '
                'Marked COMPLETED, but n_trial=0\n'.format(agent_id)
            )
            wrn_count += 1
        if (
            meta["status_code"][idx] != STATUS_ACCEPTED and
            meta["n_trial"][idx] > 0
        ):
            wrn_msg = wrn_msg + (
                '    agent_id={0} | '
                'Marked INCOMPLETE, but n_trial>0\n'.format(agent_id)
            )
            wrn_count += 1
    if wrn_count > 0:
        f.write("{0} Warning(s)\n".format(wrn_count))
        f.write(wrn_msg)

    f.close()


def write_metadata(md, fp_meta):
    """Write metadata to plain-text file.

    Arguments:
        md: The metadata.
        fp_meta: The file path of the metadata file.

    """
    df = pd.DataFrame.from_dict(md)
    df.to_csv(fp_meta, index=False)


if __name__ == "__main__":
    fp_app = Path.home() / Path('.psiz-collect')
    fp_mysql_credentials = Path.home() / Path('.mysql/credentials')

    # Parse arguments.
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "project_id", type=str,
        help="String indicating project ID."
    )
    parser.add_argument(
        "-v", "--verbose", type=int, default=0,
        help="increase output verbosity"
    )
    args = parser.parse_args()
    main(fp_mysql_credentials, fp_app, args.project_id, args.verbose)
