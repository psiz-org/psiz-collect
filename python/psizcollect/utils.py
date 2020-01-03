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

"""Module for preparing psiz dockets and protocols for psiz-collect.

Functions:
    docket_message: Create a message.
    create_protocol: Create a protocol.
    fulfill_block_spec:
    catch_trial_locations:
    docket_trial: Create a trial.

Todo:
    in fulfill_block_spec
        only grab trials that fullfil spec requirements. For example,
        spec might request 2-choose-1 or 8-choose-2
    in count_real_trial
        handle cases besides block spec

"""

import numpy as np


def docket_message(fname):
    """Create appropriately formated message for docket."""
    msg = {
        "content": "message",
        "fname": fname
    }
    return msg


def create_protocol_set(protocol_spec, n_protocol, active_docket, n_stimuli):
    """Create all protocols."""
    n_trial_per_protocol = count_real_trials(protocol_spec)
    n_total_trial = n_protocol * n_trial_per_protocol

    # Randomize trial order to scramble trial difficulty across
    # protocols.
    idx_rand = np.random.permutation(n_total_trial)
    active_docket = active_docket.subset(idx_rand)

    protocol_list = []
    idx_start = 0
    for _ in range(n_protocol):
        # Grab subset of docket.
        idx_end = idx_start + n_trial_per_protocol
        idx_subset = np.arange(idx_start, idx_end)
        curr_docket = active_docket.subset(idx_subset)

        curr_protocol = create_protocol(
            protocol_spec, curr_docket, n_stimuli
        )
        protocol_list.append(curr_protocol)
        idx_start = idx_end

    return protocol_list


def create_protocol(protocol_spec, avail_docket, n_stimuli):
    """Create JSON protocols from provided docket.

    Arguments:
        protocol_spec:
        avail_docket:
        n_stimuli:

    Returns:
        protocol: JSON protocol for psiz-collect.

    """
    # Initialize JSON docket list.
    docket_json = []
    # Initialize counter.
    avail_counter = 0

    for part in protocol_spec['docket']:
        if part['content'] == 'blockSpec':
            docket_json, avail_counter = fulfill_block_spec(
                docket_json, part, avail_docket, avail_counter, n_stimuli
            )
        else:
            docket_json.append(part)

    # Wrap.
    docket_json = {
        "docket": docket_json
    }
    return docket_json


def fulfill_block_spec(
        docket_json, block_spec, avail_docket, avail_counter, n_stimuli):
    """Fullfill block specification."""
    is_catch_array = catch_trial_locations(
        block_spec['nTrial'], block_spec['nCatch']
    )

    for i_trial in range(block_spec['nTrial']):
        if is_catch_array[i_trial]:
            # Add catch trial.
            is_catch = True
            r = np.random.choice(
                n_stimuli, block_spec['nReference'], replace=False
            )
            q = np.random.choice(r, 1)[0]
            catch_trial = docket_trial(
                q, r, block_spec['nSelect'], block_spec['isRanked'], is_catch
            )
            docket_json.append(catch_trial)
        else:
            # Add real trial.
            is_catch = False
            q = avail_docket.stimulus_set[avail_counter, 0]
            r = avail_docket.stimulus_set[avail_counter, 1:]
            r = r[np.not_equal(r, -1)]
            n_select = avail_docket.n_select[avail_counter]
            is_ranked = avail_docket.n_select[avail_counter]
            real_trial = docket_trial(
                q, r, n_select, is_ranked, is_catch
            )
            docket_json.append(real_trial)
            avail_counter = avail_counter + 1
    return docket_json, avail_counter


def catch_trial_locations(n_trial, n_catch):
    """Randomly assign catch trial locations.

    Arguments:
        n_trial: The totoal number of trials trials.
        n_catch: The number of catch trials.

    Return:
        is_catch: Boolean array indicating catch trial locations.

    """
    if n_catch > n_trial:
        raise ValueError("The argument n_trial must be greater than n_catch.")

    n_real = n_trial - n_catch
    is_catch = np.hstack((
        np.zeros([n_real], dtype=bool),
        np.ones([n_catch], dtype=bool)
    ))
    rand_catch = np.random.permutation(n_trial)
    is_catch = is_catch[rand_catch]
    return is_catch


def docket_trial(q, r, n_select, is_ranked, is_catch):
    """Create trial for JSON docket."""
    if isinstance(r, np.ndarray):
        r = r.tolist()
    t = {
        "content": "trial",
        "query": int(q),
        "references": r,
        "nSelect": int(n_select),
        "isRanked": bool(is_ranked),
        "isCatch": bool(is_catch)
    }
    return t


def count_real_trials(protocol):
    """Count the number of real trials in a protocol.

    Arguments:
        protocol: A protocol.

    Returns;
        n_real_trial: The number of real trials.

    """
    docket = protocol['docket']

    n_real_trial = 0
    for part in docket:
        if part['content'] == 'blockSpec':
            n_real_trial = n_real_trial + part['nTrial'] - part['nCatch']
        # elif part['content'] == 'trial':  TODO
    return n_real_trial


def print_protocol_summary(df_meta):
    """Print summary of unique protocols."""
    is_accepted_list = df_meta['is_accepted'].values
    protocol_id_list = df_meta['protocol_id'].values
    protocol_accept_list = protocol_id_list[is_accepted_list]
    uniq_list, protocol_count = np.unique(
        protocol_accept_list, return_counts=True
    )
    print('  |----------------------------|')
    print('  | N  | protocol_id           |')
    print('  |----------------------------|')
    print(
        '  | {0: <2} | total                 |'.format(np.sum(protocol_count))
    )
    for idx, protocol_id in enumerate(uniq_list):
        print('  | {0: <2} | {1} |'.format(protocol_count[idx], protocol_id))
    print('  |----------------------------|')
