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

"""Active module.

Tools for performing active learning. These tools assume a particular
directory structure in order to work.

Functions:
    get_current_round:
    update_andor_request:
    check_if_sufficient_data:
    check_if_under_budget:
    update_step:
    update_embedding:
    plot_ig_summary:

"""

from datetime import datetime, timedelta
from glob import glob
import json
import os
from pathlib import Path
import pickle
import re
import subprocess
from threading import Timer

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import psiz.catalog
import psiz.dimensionality
import psiz.generator
import psiz.models
import psizcollect.amt
import psizcollect.pipes as pzc_host
import psizcollect.utils as pzc_utils


def get_current_round(fp_active, verbose=0):
    """Get the last recorded round of active selection.

    If the log hasn't been created also create the log.

    Arguments:
        fp_active: Path to active selection directory.
        verbose (optional): Verbosity of output.

    Returns:
        current_round: The last recorded round.

    """
    # Settings.
    fp_log = fp_active / Path('log.txt')

    if not os.path.isfile(fp_log):
        current_round = -1
        f = open(fp_log, 'a')
        f.write('round,n_trial,n_dim,loss_train,loss_val\n')
        f.close()
    else:
        round_history = np.loadtxt(fp_log, delimiter=',', ndmin=2, skiprows=1)
        try:
            current_round = int(round_history[-1, 0])
        except:
            current_round = -1

    if verbose > 0:
        print('    Current round: {0}'.format(current_round))

    return current_round


def update_andor_request(
        compute_node, host_node, project_id, grade_spec, amt_spec,
        active_spec):
    """Update the round and/or request more observations.

    Before requesting more observations, the budget is checked.

    Arguments:
        compute_node:
        host_node:
        project_id:
        grade_spec:
        amt_spec:
        active_spec:

    """
    fp_master_log = Path(compute_node['masterLog'])
    fp_assets = Path(compute_node['assets'])
    fp_obs = fp_assets / Path('obs', 'obs_train.hdf5')
    fp_meta = fp_assets / Path('obs', 'meta.txt')
    fp_amt = Path(compute_node['amt'])
    fp_active = Path(compute_node['active'])
    fp_hit_log = fp_amt / Path('hit-log')

    pzc_host.pull_hit_log(host_node, project_id, fp_amt)

    # Check if still waiting on any assignments.
    n_waiting = psizcollect.amt.check_for_outstanding_assignments(
        amt_spec['profile'], True, fp_hit_log
    )

    if n_waiting == 0:
        # Update local assets.
        pzc_host.update_obs_on_host(
            host_node, project_id, grade_spec['mode'], grade_spec['threshold'],
            verbose=1
        )
        pzc_host.pull_obs(
            host_node, project_id, fp_assets, verbose=1
        )
        msg = 'Updated local assets.'
        write_master_log(msg, fp_master_log)

        # Load local assets.
        df_meta = pd.read_csv(fp_meta)

        # Check if there is sufficient data.
        current_round = get_current_round(fp_active, verbose=0)
        pattern = 'protocol_train_{0}-.*'.format(current_round)  # TODO factor out
        is_sufficient, current_total = check_if_sufficient_data(
            df_meta, pattern, active_spec, verbose=1
        )

        if is_sufficient:
            obs_train = psiz.trials.load_trials(fp_obs)
            update_step(
                obs_train, compute_node, project_id, active_spec,
                fp_master_log=fp_master_log
            )
            pzc_host.push_payload(
                compute_node['payload'], host_node, project_id
            )
            n_assignment = active_spec['nAssignment']
        else:
            n_assignment = np.maximum(
                0, active_spec['nAssignment'] - current_total
            )

        # Check budget.
        is_under_budget = check_if_under_budget(
            compute_node, amt_spec, verbose=1
        )
        # Check time.
        is_appropriate_time = psizcollect.amt.check_time(
            amt_spec['utcForbidden']
        )

        if is_under_budget and is_appropriate_time:
            # Can create HIT.
            msg = 'Creating a HIT with {0} assignment(s).'.format(n_assignment)
            write_master_log(msg, fp_master_log)
            psizcollect.pipes.create_hit_on_host(
                host_node, amt_spec['profile'], is_live=True,
                n_assignment=n_assignment, verbose=1
            )
            psizcollect.pipes.pull_hit_log(
                host_node, project_id, fp_amt
            )
            # Check back in 30 minutes.
            secs = 60 * 30
            msg = 'Checking back in 00:30:00 ...'
            write_master_log(msg, fp_master_log)
            t = Timer(
                secs, update_andor_request, args=[
                    compute_node, host_node, project_id, grade_spec, amt_spec,
                    active_spec
                ]
            )
            t.start()
        else:
            msg = 'HIT cannot be created.'
            write_master_log(msg, fp_master_log)
            if not is_under_budget:
                msg = '  Insufficient budget.'
                write_master_log(msg, fp_master_log)
            if not is_appropriate_time:
                msg = '  Outside allowed time.'
                write_master_log(msg, fp_master_log)
                # Schedule another check when inside allowed time.
                delta_t = psizcollect.amt.wait_time(amt_spec['utcForbidden'])

                msg = 'Checking back in {0} ...'.format(str(delta_t))
                write_master_log(msg, fp_master_log)

                secs = delta_t.total_seconds()
                t = Timer(
                    secs, update_andor_request, args=[
                        compute_node, host_node, project_id, grade_spec,
                        amt_spec, active_spec
                    ]
                )
                t.start()
    else:
        msg = 'There are still {0} outstanding assignment(s).'.format(
            n_waiting
        )
        write_master_log(msg, fp_master_log)

        # Check back in 15 minutes
        secs = 60 * 15
        msg = 'Checking back in 00:15:00 ...'
        write_master_log(msg, fp_master_log)
        t = Timer(
            secs, update_andor_request, args=[
                compute_node, host_node, project_id, grade_spec, amt_spec,
                active_spec
            ]
        )
        t.start()


def check_if_under_budget(compute_node, amt_spec, is_live=True, verbose=0):
    """Check that the project is still under budget."""
    is_under_budget = False

    if is_live:
        fn = 'hit_live.txt'
    else:
        fn = 'hit_sandbox.txt'

    fp_hit_log = Path(compute_node['amt']) / Path(
        'hit-log', amt_spec['profile'], fn
    )
    hit_id_list = psizcollect.amt.get_log_hits(fp_hit_log)
    total_expend = psizcollect.amt.compute_expenditures(
        hit_id_list, amt_spec['profile'], is_live
    )

    if total_expend < amt_spec['budget']:
        is_under_budget = True

    if verbose > 0:
        print(
            (
                'Budget: {0:.2f} | Expenditures: {1:.2f} | '
                'Remaining funds: {2:.2f}'
            ).format(
                amt_spec['budget'], total_expend,
                amt_spec['budget'] - total_expend
            )
        )
    return is_under_budget


def update_step(
        obs, compute_node, project_id, active_spec, fp_master_log=None,
        verbose=0):
    """Update step of active selection procedure."""
    fp_catalog = Path(compute_node['catalog'])
    fp_payload = Path(compute_node['payload'])
    fp_active = Path(compute_node['active'])

    # Current assets.
    fp_current = fp_active / Path('current')
    if not fp_current.exists():
        fp_current.mkdir(parents=True)
    fp_docket = fp_current / Path('docket.hdf5')

    catalog = psiz.catalog.load_catalog(fp_catalog)

    current_round = get_current_round(fp_active, verbose=0)
    current_round = current_round + 1
    msg = '    Current round: {0}'.format(current_round)
    write_master_log(msg, fp_master_log)

    # Archive asset filepaths.
    fp_archive = fp_active / Path('archive')
    fp_samples_archive = fp_archive / Path('samples', 'samples_{0}.p'.format(
        current_round
    ))
    fp_ig_archive = fp_archive / Path('ig', 'ig_info_{0}.p'.format(
        current_round
    ))
    # if not fp_samples_archive.exists():
    #     fp_samples_archive.mkdir(parents=True)
    # if not fp_ig_archive.exists():
    #     fp_ig_archive.mkdir(parents=True)

    # Update embedding.
    # fp_emb = fp_current / Path('emb.hdf5')
    # emb = psiz.models.load_embedding(fp_emb)
    # TODO Should not save embedding inside function.
    emb = update_embedding(
        obs, catalog.n_stimuli, current_round, fp_active,
        dim_check_interval=active_spec['intervalCheckDim'],
        fp_master_log=fp_master_log, verbose=2
    )

    # Update samples.
    # samples = pickle.load(open(fp_samples_archive, 'rb'))
    msg = 'Sampling from posterior ...'
    write_master_log(msg, fp_master_log)
    samples = emb.posterior_samples(
            obs, n_final_sample=1000, n_burn=100, thin_step=10, verbose=1
    )
    pickle.dump(samples, open(fp_samples_archive, 'wb'))

    # Create protocols using active selection.
    msg = 'Updating protocols ...'
    write_master_log(msg, fp_master_log)
    active_docket, ig_info, protocol_list = generate_active_protocols(
        active_spec, emb, samples, fp_master_log=fp_master_log,
        verbose=verbose
    )
    active_docket.save(fp_docket)
    pickle.dump(ig_info, open(fp_ig_archive, 'wb'))
    # active_docket = trials.load_trials(fp_docket)
    # ig_info = pickle.load(open(fp_ig_archive, 'rb'))

    # Save new protocols.
    for idx, curr_protocol in enumerate(protocol_list):
        # TODO factor out `protocol_train_`
        fp_protocol = fp_payload / Path(
            'protocol_train_{0}-{1}.json'.format(current_round, idx)
        )
        with open(fp_protocol, 'w') as outfile:
            json.dump(curr_protocol, outfile)

    # Retire previous active protocols, regardless of accepted data.
    if current_round > 0:
        # TODO factor out `protocol_train_`
        cmd = 'mv {0}/protocol_train_{1}-*.json {0}/retired/'.format(
            os.fspath(fp_payload), current_round-1
        )
        subprocess.run(cmd, shell=True)

    # TODO Move summary plots to separate function.
    # Generate a random docket of trials for comparison.
    random_gen = psiz.generator.RandomGenerator(
        catalog.n_stimuli, n_reference=8, n_select=2
    )
    rand_docket = random_gen.generate(8000)
    ig_random = psiz.generator.information_gain(emb, samples, rand_docket)
    ig_trial = ig_info['ig_trial']
    fp_fig_ig = fp_active / Path(
        'archive', 'ig', 'ig_info_{0}.pdf'.format(current_round)
    )
    plot_ig_summary(ig_trial, ig_random, fp_fig_ig)


def update_embedding(
        obs, n_stimuli, current_round, fp_active, dim_check_interval=5,
        fp_master_log=None, verbose=0):
    """Update the embedding.

    Arguments:
        obs:
        n_stimuli:
        current_round:
        fp_emb:
        fp_dim_summary:
        fp_active:
        dim_check_interval (optional):
        verbose (optional)

    Returns:
        emb: Updated embedding.

    """
    msg = 'Updating embedding ...'
    write_master_log(msg, fp_master_log)

    # Settings.
    fp_log = fp_active / Path('log.txt')

    fp_emb = fp_active / Path('current', 'emb.hdf5')
    if not fp_emb.parent.exists():
        fp_emb.parent.mkdir(parents=True)

    fp_emb_archive = fp_active / Path(
        'archive', 'emb', 'emb_{0}.hdf5'.format(current_round)
    )
    if not fp_emb_archive.parent.exists():
        fp_emb_archive.parent.mkdir(parents=True)

    fp_dim_summary = fp_active / Path(
        'archive', 'dim', 'dim_summary_{0}.hdf5'.format(current_round)
    )
    if not fp_dim_summary.parent.exists():
        fp_dim_summary.parent.mkdir(parents=True)

    # Load last embedding or initialize to default.
    if current_round is 0:
        # Initialize to two dimensional embedding.
        emb = psiz.models.Exponential(n_stimuli, n_dim=2)
    else:
        emb = psiz.models.load_embedding(fp_emb)
    n_dim_last = emb.n_dim
    n_group_last = emb.n_group
    n_stimuli_last = emb.n_stimuli

    # Check dimensionality.
    if np.mod(current_round, dim_check_interval) == 0:
        if verbose > 0:
            msg = '    Checking dimensionality ...'
            write_master_log(msg, fp_master_log)
        dim_summary = psiz.dimensionality.dimension_search(
            obs, psiz.models.Exponential, n_stimuli, dim_list=range(2, 20),
            n_restart=100, n_split=10, n_fold=5, verbose=verbose
        )
        pickle.dump(dim_summary, open(fp_dim_summary, 'wb'))
        n_dim_best = dim_summary['dim_best']
    else:
        n_dim_best = n_dim_last

    # Quickly finetune existing embedding (if possible).
    n_group = np.max(obs.group_id) + 1
    can_finetune = (
        (n_dim_best == n_dim_last) and
        (n_group == n_group_last) and
        (n_stimuli == n_stimuli_last)
    )
    if can_finetune:
        loss_train, loss_val = emb.fit(
            obs, n_restart=10, init_mode='hot', verbose=2
        )
    else:
        # Initialize new embedding with changed dimensionality.
        emb = psiz.models.Exponential(n_stimuli, n_dim_best)

    # Infer new embedding using cold restarts.
    loss_train, loss_val = emb.fit(
        obs, n_restart=300, init_mode='cold', verbose=2
    )
    emb.save(fp_emb)
    emb.save(fp_emb_archive)

    # Log the dimensionality and loss.
    f = open(fp_log, 'a')
    f.write('{0},{1},{2},{3:.4f},{4:.4f}\n'.format(
        current_round, obs.n_trial, n_dim_best, loss_train, loss_val
    ))
    f.close()

    return emb


def generate_active_protocols(
        active_spec, emb, samples, fp_master_log=None, verbose=0):
    """Generate protocols using active selection."""
    n_real_trial = pzc_utils.count_real_trials(active_spec['protocol'])
    n_total_trial = active_spec['nProtocol'] * n_real_trial
    active_gen = psiz.generator.ActiveGenerator(
        emb.n_stimuli, n_reference=8, n_select=2,
        max_candidate=active_spec['nTrialShotgun']
    )

    priority = psiz.generator.determine_stimulus_priority(
        emb, samples, mode='entropy'
    )
    active_docket, ig_info = active_gen.generate(
        n_total_trial, emb, samples, priority, verbose=1
    )

    # Create protocols.
    protocol_list = pzc_utils.create_protocol_set(
        active_spec['protocol'], active_spec['nProtocol'], active_docket,
        emb.n_stimuli
    )

    return active_docket, ig_info, protocol_list


def plot_ig_summary(ig_trial, ig_random, filename):
    """Plot summary of IG."""
    ig_master = np.hstack((ig_trial, ig_random))

    bins = np.linspace(np.min(ig_master), np.max(ig_master), 30)

    _, ax = plt.subplots()

    ax = plt.subplot(2, 1, 1)
    ax.hist(ig_random, bins=bins)
    ax.set_xlabel('Information Gain')
    ax.set_ylabel('Frequency')
    ax.set_title('Random')

    ax = plt.subplot(2, 1, 2)
    ax.hist(ig_trial, bins=bins)
    ax.set_xlabel('Information Gain')
    ax.set_ylabel('Frequency')
    ax.set_title('Active: Best')

    plt.tight_layout()
    if filename is None:
        plt.show()
    else:
        plt.savefig(
            os.fspath(filename), format='pdf', bbox_inches='tight', dpi=300
        )


def write_master_log(msg, fp_log, verbose=1):
    """Write to master log.

    Arguments:
        msg: The message to write.
        fp_log: The file path for the log.
        verbose (optional): Boolean indicating whether the message
            should also be printed using standard output.
    """
    dt_now_str = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    timestamped_msg = '{0} | {1}'.format(dt_now_str, msg)

    if fp_log is not None:
        f = open(fp_log, 'a')
        f.write(timestamped_msg + '\n')
        f.close()

    if verbose > 0:
        print(timestamped_msg)


def check_if_sufficient_data(df_meta, pattern, active_spec, verbose=0):
    """Check if current data meets requirements."""
    # TODO don't pass in pattern
    # TODO pass in master log
    # TODO combine with retirement logic, thus have minEach, minTotal, minUnique
    # can only provide minEach or minUnique
    is_sufficient = True

    accepted_protocol_list = df_meta.protocol_id.values[df_meta.is_accepted.values]
    uniq_accepted_list, accepted_protocol_count = np.unique(
        accepted_protocol_list, return_counts=True
    )

    # Filter down.
    locs_match = find_protocols(pattern, uniq_accepted_list)
    uniq_accepted_list = uniq_accepted_list[locs_match]
    accepted_protocol_count = accepted_protocol_count[locs_match]

    current_unique = len(uniq_accepted_list)
    current_total = np.sum(accepted_protocol_count)

    needed_unique = active_spec['sufficient']['minUnique'] - current_unique
    needed_total = active_spec['sufficient']['minTotal'] - current_total
    if needed_unique > 0:
        is_sufficient = False

    if needed_total > 0:
        is_sufficient = False

    if verbose > 0:
        if is_sufficient:
            print(
                'There is sufficient data to generate the next round of'
                ' protocols.'
            )
            print(
                'There are {0} assignments for the current round.'.format(
                    current_total
                )
            )
        else:
            print(
                'There is insufficient data to generate the next round of '
                'protocols.'
            )
            if needed_unique > 0:
                print(
                    '  Need {0} more unique protocols.'.format(needed_unique)
                )
            if needed_total > 0:
                print(
                    '  Need {0} more total protocols.'.format(needed_total)
                )

    return is_sufficient, current_total


def find_retireable(df_meta, min=1):
    """Find protocols eligable for retirement.

    Eligability is determined by the minimum number of assignments that
    must be accepted for a protocol to be retired.

    Arguments:
        df_meta:
        min (optional):

    """
    accepted_protocol_list = df_meta.protocol_id.values[
        df_meta.is_accepted.values
    ]
    uniq_accepted_list, accepted_protocol_count = np.unique(
        accepted_protocol_list, return_counts=True
    )

    eligable_list = []
    for idx, protocol in enumerate(uniq_accepted_list):
        if accepted_protocol_count[idx] >= min:
            eligable_list.append(protocol)
    eligable_list = np.asarray(eligable_list)

    return eligable_list


def find_protocols(pattern, protocol_arr):
    """Find all protocols that match target.

    Arguments:
        pattern: A regular expression.
        protocol_arr: An array of (string) protocol IDs.

    Returns:
        locs_match: The locations where the protocol ID matches the
            supplied pattern.

    """
    locs_match = np.zeros([len(protocol_arr)], dtype=bool)
    for idx, protocol in enumerate(protocol_arr):
        result = re.match(pattern, protocol)
        if result is not None:
            locs_match[idx] = True
    return locs_match


def retire_protocols(fp_payload, eligable_protocol_arr, fp_retired=None):
    """Retire eligable protocols that match pattern.

    Arguments:
        fp_payload: File path to payload containing live protocols.
        eligable_protocol_arr: An array of protocols that are eligable
            for retirement.
        fp_retired (optional):

    """
    if fp_retired is None:
        fp_retired = fp_payload / Path('retired')

    # Make sure 'retired' directory exists inside `payload` directory.
    if not fp_retired.exists():
        fp_retired.mkdir()

    # Move eligable protocols to `retired` directory.
    for protocol in eligable_protocol_arr:
        fp_protocol = fp_payload / Path(protocol)
        if fp_protocol.exists():
            cmd = 'mv {0} {1}'.format(
                os.fspath(fp_protocol), os.fspath(fp_retired)
            )
            subprocess.run(cmd, shell=True)


def count_remaining_protocols(fp_payload, log=None, verbose=0):
    """Count remaining protocols in payload.

    Arguments:
        fp_payload:
        log:
        verbose:

    """
    dir_list = glob(os.fspath(fp_payload) + '/protocol_*.json')
    n_remain = len(dir_list)
    msg = 'There are {0} protocols remaining.'.format(n_remain)
    write_master_log(msg, log)
    return n_remain


def select_trials_by_protocol(pattern, obs, df_meta):
    """Select trials matching pattern.

    Arguments:
        pattern: A regular expression.
        obs: A psiz.trials.Observations object.
        df_meta: A metadata dataframe.

    """
    locs_accepted = df_meta.is_accepted.values
    accepted_protocol_arr = df_meta.protocol_id.values[locs_accepted]
    accepted_session_arr = df_meta.session_id.values[locs_accepted]

    locs_protocol_match = find_protocols(pattern, accepted_protocol_arr)
    match_session_arr = accepted_session_arr[locs_protocol_match]

    # Find data with protocols matching the supplied pattern.
    locs_match = np.zeros(obs.n_trial, dtype=bool)
    for session_id in match_session_arr:
        locs_session_id = np.equal(obs.session_id, session_id)
        locs_match = np.logical_or(locs_match, locs_session_id)

    if np.sum(locs_match) > 0:
        obs_match = obs.subset(locs_match)
    else:
        obs_match = None
    return obs_match
