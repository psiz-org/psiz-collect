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

import datetime
import json
import os
from pathlib import Path
import pickle
import subprocess

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import psiz.datasets
import psiz.dimensionality
import psiz.generator
import psiz.models
import psizcollect.amt
import psizcollect.pipes as pzc_pipes
import psizcollect.utils as pzc_utils


def get_current_round(fp_active, verbose=0):
    """Get the current round of active selection.

    If the log hasn't been created also create the log.

    Arguments:
        fp_active: Path to active selection directory.
        verbose (optional): Verbosity of output.

    Returns:
        current_round: The current round.

    """
    # Settings.
    fp_log = fp_active / Path('log.txt')

    if not os.path.isfile(fp_log):
        current_round = 0
        f = open(fp_log, 'a')
        f.write('round,n_dim,loss_train,loss_val\n')
        f.close()
    else:
        round_history = np.loadtxt(fp_log, delimiter=',', ndmin=2, skiprows=1)
        current_round = int(round_history[-1, 0])
    if verbose > 0:
        print('    Current round: {0}'.format(current_round))

    return current_round


def update_andor_request(
        compute_node, host_node, project_id, active_spec, amt_spec):
    """Update the round and/or request more observations.

    Before requesting more observations, the budget is checked.

    Arguments:
        compute_node:
        host_node:
        project_id:
        active_spec:
        amt_spec:
    """
    # Check if there is sufficient data.
    is_sufficient, current_total = check_if_sufficient_data(
        compute_node, active_spec, verbose=1
    )

    if is_sufficient:
        update_step(
            compute_node, host_node, project_id, active_spec
        )
        n_assignment = active_spec['nAssignment']
    else:
        n_assignment = np.maximum(
            0, active_spec['nAssignment'] - current_total
        )

    # Check budget.
    is_under_budget = check_if_under_budget(amt_spec['budget'])
    # Check time.
    is_appropriate_time = psizcollect.amt.check_time(amt_spec['utcForbidden'])

    if is_under_budget and is_appropriate_time:
        # Can create HIT.
        print('Creating a HIT with {0} assignment(s).'.format(n_assignment))
        psizcollect.pipes.create_hit_on_host(
            host_node, amt_spec['profile'], is_live=True,
            n_assignment=n_assignment, verbose=1
        )
    else:
        print('HIT cannot be created.')
        if not is_under_budget:
            print('  Insufficient budget.')
        if not is_appropriate_time:
            print('  Outside allowed time.')


def check_if_sufficient_data(compute_node, active_spec, verbose=0):
    """Check if current round of data meets requirements."""
    is_sufficient = True

    fp_assets = Path(compute_node['assets'])
    fp_active = Path(compute_node['active'])
    fp_meta = fp_assets / Path('obs', 'meta.txt')

    current_round = get_current_round(fp_active, verbose=0)
    meta = pd.read_csv(fp_meta)
    accepted_protocol_list = meta.protocol_id.values[meta.is_accepted.values]
    accepted_protocol_list = accepted_protocol_list.tolist()

    sub = 'protocol_a_{0}-'.format(current_round)
    current_protocols = [s for s in accepted_protocol_list if sub in s]
    unique_list, protocol_count = np.unique(
        current_protocols, return_counts=True
    )
    current_unique = len(unique_list)
    current_total = np.sum(protocol_count)

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


def check_if_under_budget(budget):
    """Check that the project is still under budget."""
    is_under_budget = True  # TODO
    return is_under_budget


def update_step(compute_node, host_node, project_id, active_spec, verbose=0):
    """Update step of active selection procedure."""
    fp_assets = Path(compute_node['assets'])
    fp_obs = fp_assets / Path('obs', 'obs.hdf5')
    fp_catalog = fp_assets / Path('catalog.hdf5')
    fp_payload = Path(compute_node['payload'])

    fp_active = Path(compute_node['active'])

    # Current assets.
    fp_current = fp_active / Path('current')
    if not fp_current.exists():
        fp_current.mkdir(parents=True)
    fp_docket = fp_current / Path('docket.hdf5')

    catalog = psiz.datasets.load_catalog(fp_catalog)
    obs = psiz.trials.load_trials(fp_obs)

    current_round = get_current_round(fp_active, verbose=0)
    current_round = current_round + 1
    print('    Current round: {0}'.format(current_round))

    # Archive assets.
    fp_archive = fp_active / Path('archive')
    if not fp_archive.exists():
        fp_archive.mkdir(parents=True)
    fp_samples_archive = fp_archive / Path('samples_{0}.p'.format(
        current_round
    ))
    fp_ig_archive = fp_archive / Path('ig_info_{0}.p'.format(
        current_round
    ))

    # Update embedding.
    emb = update_embedding(
        obs, catalog.n_stimuli, current_round, fp_active,
        dim_check_interval=active_spec['intervalCheckDim'], verbose=2
    )

    # Update samples.
    samples = emb.posterior_samples(
            obs, n_final_sample=1000, n_burn=100, thin_step=10, verbose=1
    )
    pickle.dump(samples, open(fp_samples_archive, 'wb'))

    # fp_emb = fp_current / Path('emb.hdf5')  # TODO
    # emb = psiz.models.load_embedding(fp_emb)  # TODO
    # samples = pickle.load(open(fp_samples_archive, 'rb'))  # TODO

    # Select docket using active selection.
    n_real_trial = pzc_utils.count_real_trials(active_spec['protocol'])
    n_total_trial = active_spec['nProtocol'] * n_real_trial
    active_gen = psiz.generator.ActiveShotgunGenerator(
        n_reference=8, n_select=2, n_trial_shotgun=2000, priority='kl'
    )
    active_docket, ig_info = active_gen.generate(
        n_total_trial, emb, samples, verbose=1
    )
    active_docket.save(fp_docket)
    pickle.dump(ig_info, open(fp_ig_archive, 'wb'))

    # active_docket = trials.load_trials(fp_docket)  # TODO
    # ig_info = pickle.load(open(fp_ig_archive, 'rb'))  # TODO

    # TODO move to separate function.
    # Generate a random docket of trials for comparison.
    random_gen = psiz.generator.RandomGenerator(8, 2)
    rand_docket = random_gen.generate(8000, catalog.n_stimuli)
    ig_random = psiz.generator.information_gain(emb, samples, rand_docket)

    # Summary plots.
    ig_trial = ig_info['ig_trial']
    fp_fig_ig = fp_active / Path(
        'archive', 'ig_info_{0}.pdf'.format(current_round)
    )
    plot_ig_summary(ig_trial, ig_random, fp_fig_ig)

    # Create protocols.
    protocol_list = pzc_utils.create_protocol_set(
        active_spec['protocol'], active_spec['nProtocol'], active_docket,
        catalog.n_stimuli
    )
    # Save new protocols.
    for idx, curr_protocol in enumerate(protocol_list):
        fp_protocol = fp_payload / Path(
            'protocol_a_{0}-{1}.json'.format(current_round, idx)
        )
        with open(fp_protocol, 'w') as outfile:
            json.dump(curr_protocol, outfile)

    # Retire previous active protocols.
    if current_round > 0:
        cmd = 'mv {0}/protocol_a_{1}-*.json {0}/retired/'.format(
            os.fspath(fp_payload), current_round-1
        )
        subprocess.run(cmd, shell=True)

    # Sync payload.
    pzc_pipes.sync_payload(fp_payload, host_node, project_id)


def update_embedding(
        obs, n_stimuli, current_round, fp_active, dim_check_interval=5,
        verbose=0):
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
    # Settings.
    fp_log = fp_active / Path('log.txt')
    fp_emb = fp_active / Path('current', 'emb.hdf5')
    fp_emb_archive = fp_active / Path(
        'archive', 'emb', 'emb_{0}.hdf5'.format(current_round)
    )
    fp_dim_summary = fp_active / Path(
        'archive', 'dim', 'dim_summary_{0}.hdf5'.format(current_round)
    )

    # Load last embedding or initialize to default.
    if current_round is 0:
        # Initialize to two dimensional embedding.
        emb = psiz.models.Exponential(n_stimuli, n_dim=2)
    else:
        emb = psiz.models.load_embedding(fp_emb)
    n_dim_last = emb.n_dim

    # Check dimensionality.
    if np.mod(current_round, dim_check_interval) == 0:
        if verbose > 0:
            print('    Checking dimensionality...')
        dim_summary = psiz.dimensionality.dimension_search(
            obs, psiz.models.Exponential, n_stimuli, dim_list=range(2, 20),
            n_restart=100, n_split=10, n_fold=5, verbose=verbose
        )
        pickle.dump(dim_summary, open(fp_dim_summary, 'wb'))
        n_dim_best = dim_summary['dim_best']
    else:
        n_dim_best = n_dim_last

    if n_dim_best == n_dim_last:
        # Finetune existing embedding.
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
    f.write('{0},{1},{2:.4f},{3:.4f}\n'.format(
        current_round, n_dim_best, loss_train, loss_val
    ))
    f.close()

    return emb


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
