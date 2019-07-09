"""Extract observations from MySQL database.

This script creates a psiz.trials.Observations object for the
user-supplied `project_id`. All COMPLETED assignments (i.e.,
status_code = 1) belonging to the requested project are selected from
the database and instantiated as an Observations object. The created
observations are saved in a directory with the same name as the
supplied `project_id`, i.e., `.psiz-collect/obs/<project_id>/obs.hdf5`
(see README for more regarding the assumed directory structure). It is
also assumed that this script resides in the `obs/` directory and is
called from within the `obs/` directory.

Important to note, the Observations object uses the MySQL database
`assignment_id` as the `agent_id`. This allows the created Observations
object to be used to make subsequent queries to the database about each
agent. For example, if a particular project includes an add-on survey.

It is assumed that your MySQL credentials are stored at
`~/.mysql/credentials` with the appropriate format (see README). If
they are stored somewhere else, with a different format, the variable
`fp_mysql_credentials`, `host`, `user`,`passwd`, and `db` need to be
changed.

Arguments: project_id: A string identifier which will be used to fetch
    the appropriate observations.

Example Usage: python extract_observations "birds-region"

Todo:
    Add more robust argument parsing.
    Add option to include incomplete assignments.
    Optional arguments for alternative save locations.

"""

import os
import sys
import configparser
from pathlib import Path
import datetime
import argparse

import mysql.connector
import numpy as np
import psiz.trials

# Consants used/assumed in the MySQL database.
STATUS_CREATED = 0
STATUS_COMPLETED = 1
STATUS_EXPIRED = 2
N_MAX_REF = 8


def main(fp_mysql_credentials, fp_data, project_id, verbose):
    """Run script."""
    # Set the project path.
    fp_project = fp_data / Path(project_id)
    if not os.path.exists(fp_project):
        os.makedirs(fp_project)
    fp_obs = fp_project / Path("obs.hdf5")
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

    wrn_msg = ''

    # Retrieve assignment_id's of participants that have successfully
    # completed the task.
    assignment_id_list, wrn_msg = get_completed_assignments(
        sql_cursor, project_id, wrn_msg
    )

    obs = None
    comp_stats = None
    if len(assignment_id_list) > 0:
        # Determine time to complete task.
        comp_stats, wrn_msg = completion_statistics(
            sql_cursor, assignment_id_list, wrn_msg
        )

        # Create psiz.trials.Observations object.
        obs, wrn_msg = create_obs_all(sql_cursor, assignment_id_list, wrn_msg)
        obs.save(fp_obs)

    # Save a plain text summary of the Observations.
    write_summary(obs, comp_stats, wrn_msg, fp_summary)


def get_completed_assignments(sql_cursor, project_id, wrn_msg):
    """Select completed assignment_id's.

    Arguments:
        sql_cursor: A MySQL cursor.
        project_id: The requested project ID.
    """
    sql = (
        "SELECT assignment_id FROM assignment WHERE project_id=%s AND"
        " status_code=%s"
    )
    vals = (project_id, STATUS_COMPLETED)
    sql_cursor.execute(sql, vals)

    sql_result = sql_cursor.fetchall()
    assignment_id_list = []

    n_row = len(sql_result)
    if n_row > 0:        
        for i_row in range(n_row):
            assignment_id_list.append(sql_result[i_row][0])
    return assignment_id_list, wrn_msg


def completion_statistics(sql_cursor, assignment_id_list, wrn_msg):
    """Determine completion statistics.

    Arguments:
        sql_cursor: A MySQL cursor.
        assignment_id_list: A list of database assignment_id's.
    """
    time_m_list = []
    for assignment_id in assignment_id_list:
        sql = (
            "SELECT begin_hit, end_hit FROM assignment WHERE assignment_id=%s"
        )
        vals = (assignment_id,)
        sql_cursor.execute(sql, vals)

        sql_result = sql_cursor.fetchall()
        total_time_m = (
            sql_result[0][1] - sql_result[0][0]
        ).total_seconds() / 60
        time_m_list.append(total_time_m)
    comp_stats = {
        "time_total_m": {
            "min": np.min(time_m_list),
            "max": np.max(time_m_list),
            "mean": np.mean(time_m_list),
            "median": np.median(time_m_list)
        }
    }
    return comp_stats, wrn_msg


def create_obs_all(sql_cursor, assignment_id_list, wrn_msg):
    """Create Observations object for all agents.

    Arguments:
        sql_cursor: A MySQL cursor.
        assignment_id_list: A list of database assignment_id's.
    """
    obs_all = None
    for assignment_id in assignment_id_list:
        sql = (
            "SELECT trial_id, assignment_id, n_select, is_ranked, q_idx, "
            "r1_idx, r2_idx, r3_idx, r4_idx, r5_idx, r6_idx, r7_idx, r8_idx, "
            "start_ms, r1_rt_ms, r2_rt_ms, r3_rt_ms, r4_rt_ms, r5_rt_ms, "
            "r6_rt_ms, r7_rt_ms, r8_rt_ms "
            "FROM trial WHERE assignment_id=%s"
        )
        vals = (assignment_id,)
        sql_cursor.execute(sql, vals)

        sql_result = sql_cursor.fetchall()
        n_trial = len(sql_result)
        if n_trial == 0:
            wrn_msg = (
                wrn_msg +
                '    assignment_id={0} | n_trial: 0\n'.format(assignment_id)
            )
        else:
            # print("    Trials: {0}".format(n_trial))
            obs = create_obs_agent(sql_result, assignment_id)
            if obs_all is not None:
                obs_all = psiz.trials.stack((obs_all, obs))
            else:
                obs_all = obs
    return obs_all, wrn_msg


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

    rt_ms = np.max(rt_ms, axis=1)  # TODO may want to handle differently.
    obs = psiz.trials.Observations(
        response_set, n_select=n_select, is_ranked=is_ranked,
        agent_id=agent_id, rt_ms=rt_ms
    )
    return obs


def write_summary(obs, comp_stats, wrn_msg, fp_summary):
    """Write a plain-text summary of the observations.

    Arguments:
        obs: A psiz.trials.Observations object.
        fp_summary: The file path of the summary file.

    """
    f = open(fp_summary, "w")
    f.write("Observations Summary\n")
    f.write("Last Updated: {0}\n\n".format(str(datetime.datetime.now())))

    if len(wrn_msg) > 0:
        f.write("Warnings\n")
        f.write(wrn_msg + "\n")

    if obs is None:
        f.write("No completed assignments.\n")
    else:
        n_agent = len(np.unique(obs.agent_id))
        n_unique_stim = len(np.unique(obs.stimulus_set))

        f.write("General\n")
        f.write("    n_agent: {0}\n".format(n_agent))
        f.write("    n_trial: {0}\n".format(obs.n_trial))
        f.write("    n_unique_stimuli: {0}\n\n".format(n_unique_stim))

        f.write("Total Time (min)\n")
        f.write("    min: {0:.2f}\n".format(comp_stats["time_total_m"]["min"]))
        f.write("    max: {0:.2f}\n".format(comp_stats["time_total_m"]["max"]))
        f.write("    mean: {0:.2f}\n".format(comp_stats["time_total_m"]["mean"]))
        f.write("    median: {0:.2f}\n".format(
            comp_stats["time_total_m"]["median"]
        ))

    f.close()


if __name__ == "__main__":
    fp_data = Path.home() / Path('.psiz-collect', 'obs')
    fp_mysql_credentials = Path.home() / Path('.mysql/credentials')

    # Parse arguments.
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "project_id", type=str,
        help="String indicating project_id."
    )
    parser.add_argument(
        "-v", "--verbose", type=int, default=0,
        help="increase output verbosity"
    )
    args = parser.parse_args()
    main(fp_mysql_credentials, fp_data, args.project_id, args.verbose)
