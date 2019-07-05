"""Script that runs some basic checks on a collection project.

This script does not constitute a comprehensive set of checks. It is up
to the user to make sure your project complies with the assumptions of
the web code.

"""

import os
import argparse
import json
import glob
import numpy as np


def main(args):
    """Run script."""
    # Settings.

    print("Checking project {0}".format(fp_project))
    fp_stimuli = os.path.join(fp_project, 'stimuli.txt')

    # Load in each line of stimuli.txt file separately.
    with open(fp_stimuli) as f:
        stimuli_list = f.readlines()
    stimuli_status, stimuli_msg = check_stimuli(stimuli_list)

    output_check("stimuli.txt", stimuli_status, stimuli_msg)
    print("")

    protocol_list = glob.glob(os.path.join(fp_project, "protocol_*.json"))
    for idx, i_protocol in enumerate(protocol_list):
        protocol_status, msg = check_protocol(i_protocol, stimuli_list)
        output_check(os.path.basename(i_protocol), protocol_status, msg)


def check_stimuli(stimuli_list):
    """Check stimuli.txt.

    Todo:
        check extensions.
        does basename handle raw text appropriately?
    """
    status = 0
    msg = ""
    n_stimuli = len(stimuli_list)

    basename_list = []
    for i_stim in stimuli_list:
        basename_list.append(os.path.basename(i_stim.rstrip()))
    n_unique_basename = len(np.unique(basename_list))

    if n_unique_basename < n_stimuli:
        status = np.maximum(status, 2)
        msg = msg + "ERROR: {0} stimuli filenames are not unique.\n".format(n_stimuli - n_unique_basename)
    return (status, msg)


def check_protocol(fp_protocol, stimuli_list):
    """Check protocol.

    Check:
    nCatch < nTrial (warning if percentale greater than .1)
    check nReference + 1 < n_stimuli
    check nSelect <= nReference (warning if equal)

    """
    with open(fp_protocol, 'r') as f:
        datastore = json.load(f)

    # TODO check if docketSpec exists, generator field no longer used.
    if datastore['generator'] == "stochastic":
        (status, msg) = check_protocol_stochastic(stimuli_list, datastore)
    elif datastore['generator'] == "deterministic":
        (status, msg) = check_protocol_deterministic(stimuli_list, datastore)

    return (status, msg)


def check_protocol_stochastic(stimuli_list, datastore):
    """Check stochastic protocol."""
    status = 0
    msg = ""
    n_stimuli = len(stimuli_list)

    if datastore["docketSpec"]["nCatch"] > datastore["docketSpec"]["nTrial"]:
        status = np.maximum(status, 2)
        msg = msg + "ERROR: You have requested more catch trials that total trials.\n"

    if datastore["docketSpec"]["nCatch"] / datastore["docketSpec"]["nTrial"] > .1:
        status = np.maximum(status, 1)
        msg = msg + "WARNING: You have requested a large number of catch trials.\n"

    if datastore["docketSpec"]["nReference"] + 1 > n_stimuli:
        status = np.maximum(status, 2)
        msg = msg + "ERROR: You have requested more stimuli per trial than are available.\n"

    if datastore["docketSpec"]["nSelect"] > datastore["docketSpec"]["nReference"]:
        status = np.maximum(status, 2)
        msg = msg + "ERROR: The supplied nSelect is greater than nReference.\n"

    if datastore["docketSpec"]["nSelect"] == datastore["docketSpec"]["nReference"]:
        status = np.maximum(status, 1)
        msg = msg + "WARNING: The supplied nSelect is equal to nReference. Are you sure this is what you want?\n"
    
    return (status, msg)


def check_protocol_deterministic(stimuli_list, datastore):
    """Check deterministic protocol."""
    status = 0
    msg = ""
    n_stimuli = len(stimuli_list)

    return (status, msg)


def output_check(fn, status, msg):
    """Output result of check."""
    print("    {0}    {1}".format(fn, convert_status(status)))
    if status > 0:
        print("        {0}".format(msg))


def convert_status(status):
    """Convert status integer to string."""
    if status == 0:
        status_str = "PASSED"
    elif status == 1:
        status_str = "WARNING"
    elif status == 2:
        status_str = "FAILED"
    return status_str


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'fp_project', type=str,
        help='The filepath to the collection project you would like to check.'
    )
    args = parser.parse_args()
    main(args.fp_project)
    # fp_project = "psiz-collect/c001"
    # main(fp_project)
