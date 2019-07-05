Assumed Server Directory structure
`obs\`
    `extract_observations.py`
    `<my_project_0\>`
        `obs.hdf5`
        `summary.txt`
    `<my_project_1\>`
        `obs.hdf5`
        `summary.txt`

Assumed Local Directory structure
    `<my_project_1\>`
        `raw\`
            `obs.hdf5`
            `summary.txt`
        `preprocess_obs.py`


on server, `\obs` directory

in `\obs` directory script `extract_observations.py` for parsing MySQL data into obs.

To move to server:
scp Projects/psiz-infrastracture/mysql/extract_observations.py bdroads@104.236.150.245:/home/bdroads/obs/extract_observations.py

obs will be created and placed in a directory with the same name as the provided project ID. Any existing data will be over-written.

Some summary information is also written to summary.txt

pulls obs and places them in a `raw\` directory for 