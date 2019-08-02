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

"""Pipes module.

Tools for assembling pipelines.

Functions:
    psiz_cursor:
    fetch_assignment:
"""

import configparser
from datetime import datetime
import os
import subprocess
from pathlib import Path

import mysql.connector
import numpy as np
import pandas as pd
import paramiko
import psiz.trials
import psiz.preprocess

# Consants used/assumed in the MySQL database.
STATUS_CREATED = 0  # Incomplete and not expired.
STATUS_ACCEPTED = 1  # Completed and met grading criteria.
STATUS_EXPIRED = 2  # Incomplete and expired.
STATUS_DROPPED = 3  # Completed but did not meet grading criteria.
N_MAX_REF = 8


def update_obs_on_host(
        host_node, project_id, grade_mode, grade_threshold, verbose=0):
    """Update observations on host node.

    Arguments:
        host_node:
        project_id:
        grade_mode:
        grade_threshold;
        verbose (optional):
    """
    # Connect.
    client = paramiko.SSHClient()
    client.load_system_host_keys()
    client.connect(
        host_node["ip"], port=host_node["port"], username=host_node["user"]
    )

    cmd_python = (
        "from psizcollect import extract; "
        "extract.extract_observations('{0}', '{1}', {2})"
    ).format(
        project_id, grade_mode, grade_threshold
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


def write_metadata(meta, fp_meta):
    """Write metadata to plain-text file.

    Arguments:
        meta: The metadata.
        fp_meta: The file path of the metadata file.

    """
    df = pd.DataFrame.from_dict(meta)
    df.to_csv(fp_meta, index=False)


def write_summary(obs, meta, fp_summary):
    """Write a plain-text summary of the observations.

    Arguments:
        obs: A psiz.trials.Observations object.
        meta: Metadata for the observations.
        fp_summary: The file path of the summary file.

    """
    f = open(fp_summary, "w")
    f.write("Summary\n")
    f.write("Last Updated: {0}\n\n".format(str(datetime.now())))

    # Assignment summary.
    summ_assign = assignment_summary(obs, meta)
    f.write(summ_assign)

    # Observation summary.
    summ_obs = observation_summary(obs, meta)
    f.write(summ_obs)

    # Protocol summary.
    summ_protocol = protocol_summary(obs, meta)
    f.write(summ_protocol)

    # Warning summary.
    summ_warning = warning_summary(obs, meta)
    f.write(summ_warning)

    f.close()


def assignment_summary(obs, meta):
    """Return a plain-text summary of assignments.

    Arguments:
        obs: psiz.trials.Observations object.
        meta: The metadata.

    Returns:
        msg: A string containing an appropriately formated summary.

    """
    msg = "Assignments\n"
    locs_accepted = np.equal(meta['status_code'], STATUS_ACCEPTED)
    locs_dropped = np.equal(meta['status_code'], STATUS_DROPPED)
    locs_completed = np.sum(np.logical_or(
        locs_accepted, locs_dropped
    ))
    grade_accepted = meta['grade'][locs_accepted]
    duration_accepted = meta['duration_hit_min'][locs_accepted]
    grade_dropped = meta['grade'][locs_dropped]
    duration_dropped = meta['duration_hit_min'][locs_dropped]

    msg += "              | N    | Grade            | Duration (min)   |\n"
    msg += "              |      | min   med   max  | min   med   max  |\n"
    msg += "    --------------------------------------------------------\n"
    msg += (
        "    Completed | {0: <4} |                  |                  | \n"
    ).format(
        np.sum(locs_completed)
    )
    msg += (
        "    Accepted  | {0: <4} | {1:.2f}  {2:.2f}  {3:.2f} | {4: <4}  "
        "{5: <4}  {6: <4} |\n"
    ).format(
        np.sum(locs_accepted),
        np.min(grade_accepted),
        np.median(grade_accepted),
        np.max(grade_accepted),
        np.round(np.min(duration_accepted)),
        np.round(np.median(duration_accepted)),
        np.round(np.max(duration_accepted))
    )
    msg += (
        "    Dropped   | {0: <4} | {1:.2f}  {2:.2f}  {3:.2f} | {4: <4}  "
        "{5: <4}  {6: <4} |\n"
    ).format(
        np.sum(locs_dropped),
        np.min(grade_dropped),
        np.median(grade_dropped),
        np.max(grade_dropped),
        np.round(np.min(duration_dropped)),
        np.round(np.median(duration_dropped)),
        np.round(np.max(duration_dropped))
    )
    msg += "\n"
    return msg


def observation_summary(obs, meta):
    """Return a plain-text summary of observations.

    Arguments:
        obs: psiz.trials.Observations object.
        meta: The metadata.

    Returns:
        msg: A string containing an appropriately formated summary.

    """
    msg = "Observations\n"
    if obs is None:
        msg += "    No observations.\n"
    else:
        n_agent = len(np.unique(obs.agent_id))
        n_unique_stim = len(np.unique(obs.stimulus_set))
        avg_trial_rt = np.mean(obs.rt_ms) / 1000
        msg += "    Unique agents: {0}\n".format(n_agent)
        msg += "    Total trials: {0}\n".format(obs.n_trial)
        msg += "    Unique stimuli: {0}\n".format(n_unique_stim)
        msg += "    Avg. trial RT: {0:.2f} s\n".format(avg_trial_rt)
        msg += "\n"
    return msg


def protocol_summary(obs, meta):
    """Return a plain-text summary of protocols.

    Arguments:
        obs: psiz.trials.Observations object.
        meta: The metadata.

    Returns:
        msg: A string containing an appropriately formated summary.

    """
    # Settings
    n_last = 5

    locs_completed = np.logical_or(
        np.equal(meta["status_code"], STATUS_ACCEPTED),
        np.equal(meta["status_code"], STATUS_DROPPED)
    )
    locs_accepted = np.equal(meta["status_code"], STATUS_ACCEPTED)

    uniq_completed_list = pd.unique(meta["protocol_id"][locs_completed])
    n_uniq_completed = len(uniq_completed_list)

    uniq_accepted_list = pd.unique(meta["protocol_id"][locs_accepted])
    n_uniq_accepted = len(uniq_accepted_list)

    msg = "Protocols\n"
    msg += "    Unique protocols:\n"
    msg += "      Completed | {0: <3} |\n".format(
        n_uniq_completed
    )
    msg += "      Accepted  | {0: <3} |\n".format(
        n_uniq_accepted
    )
    msg += "\n"

    msg += "    Last {0} protocols:\n".format(n_last)
    msg += "      | N  | protocol_id\n"
    msg += "      ------------------\n"
    n_start = np.maximum(n_uniq_accepted - n_last, 0)
    for idx in np.arange(n_start, n_uniq_accepted):
        i_protocol = uniq_accepted_list[idx]
        n_curr_protocol = 0
        for j_protocol in meta["protocol_id"][locs_accepted]:
            if i_protocol == j_protocol:
                n_curr_protocol = n_curr_protocol + 1
        msg += "      | {0: <2} | {1}\n".format(
            n_curr_protocol, str(i_protocol)
        )
    msg += "\n"
    return msg


def warning_summary(obs, meta):
    """Return a plain-text summary of warning.

    Arguments:
        obs: psiz.trials.Observations object.
        meta: The metadata.

    Returns:
        msg: A string containing an appropriately formated summary.

    """
    msg = ''
    wrn_count = 0
    for idx, assignment_id in enumerate(meta["assignment_id"]):
        if (
            meta["status_code"][idx] == STATUS_ACCEPTED and
            meta["n_trial"][idx] == 0
        ):
            msg += (
                '    assignment_id={0} | '
                'Marked ACCEPTED, but n_trial=0\n'.format(assignment_id)
            )
            wrn_count += 1
        if (
            (
                meta["status_code"][idx] != STATUS_ACCEPTED and
                meta["status_code"][idx] != STATUS_DROPPED
            ) and
            meta["n_trial"][idx] > 0
        ):
            msg += (
                '    assignment_id={0} | '
                'Marked INCOMPLETE, but n_trial>0\n'.format(assignment_id)
            )
            wrn_count += 1
    if wrn_count > 0:
        msg = "{0} Warning(s)\n".format(wrn_count) + msg
    return msg


def pull_obs_from_host(host_node, project_id, fp_assets, verbose=0):
    """Pull observations from host to local machine."""
    fp_obs = fp_assets / Path('obs')
    if not fp_obs.exists():
        fp_obs.mkdir(parents=True)

    cmd = 'scp {0}@{1}:.psiz-collect/projects/{2}/obs.hdf5 {3}/'.format(
        host_node["user"], host_node["ip"], project_id, os.fspath(fp_obs)
    )
    subprocess.run(cmd, shell=True)

    cmd = 'scp {0}@{1}:.psiz-collect/projects/{2}/meta.txt {3}/'.format(
        host_node["user"], host_node["ip"], project_id, os.fspath(fp_obs)
    )
    subprocess.run(cmd, shell=True)

    cmd = 'scp {0}@{1}:.psiz-collect/projects/{2}/summary.txt {3}/'.format(
        host_node["user"], host_node["ip"], project_id, os.fspath(fp_obs)
    )
    subprocess.run(cmd, shell=True)
