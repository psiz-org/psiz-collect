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

Tools for performing active selection.

These tools assume a particular directory structure in order to work.
"""

import os
from pathlib import Path
import pickle

import numpy as np
from psiz import models
from psiz.dimensionality import dimension_search


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
        f = open(fp_log, "a")
        f.write("round,n_dim,loss_train,loss_val\n")
        f.close()
    else:
        round_history = np.loadtxt(fp_log, delimiter=',', ndmin=2, skiprows=1)
        current_round = int(round_history[-1, 0]) + 1
    if verbose > 0:
        print("    Current round: {0}".format(current_round))

    return current_round


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
    fp_dim_summary = fp_active / Path('current', 'dim_summary.hdf5')

    # Load last embedding or initialize to default.
    if current_round is 0:
        # Initialize to two dimensional embedding.
        emb = models.Exponential(n_stimuli, n_dim=2)
    else:
        emb = models.load_embedding(fp_emb)
    n_dim_last = emb.n_dim

    # Check dimensionality.
    if np.mod(current_round, dim_check_interval) == 0:
        if verbose > 0:
            print("    Checking dimensionality...")
        dim_summary = dimension_search(
            obs, models.Exponential, n_stimuli, dim_list=range(2, 20),
            n_restart=100, n_split=10, n_fold=5, verbose=verbose
        )
        pickle.dump(dim_summary, open(fp_dim_summary, "wb"))
        n_dim_best = dim_summary["dim_best"]
    else:
        n_dim_best = n_dim_last

    if n_dim_best == n_dim_last:
        # Finetune existing embedding.
        loss_train, loss_val = emb.fit(
            obs, n_restart=10, init_mode="hot", verbose=3
        )
    else:
        # Initialize new embedding with changed dimensionality.
        emb = models.Exponential(n_stimuli, n_dim_best)

    # Infer new embedding using cold restarts.
    loss_train, loss_val = emb.fit(
        obs, n_restart=300, init_mode='cold', verbose=3
    )
    emb.save(fp_emb)

    # Log the dimensionality and loss.
    f = open(fp_log, "a")
    f.write("{0},{1},{2:.4f},{3:.4f}\n".format(
        current_round, n_dim_best, loss_train, loss_val
    ))
    f.close()

    return emb
