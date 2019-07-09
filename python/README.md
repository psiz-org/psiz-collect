On the web server, the assume directory structure is as follows:
`.psiz-collect/`
    `obs/`
        `extract_observations.py`
        `<my_project_0/>`
            `obs.hdf5`
            `summary.txt`
        `<my_project_1/>`
            `obs.hdf5`
            `summary.txt`


The Python script `extract_observations.py` is used for parsing MySQL data
into a psiz.trials.Obsevation object.

obs will be created and placed in a directory with the same name as the provided project ID. Any existing data will be over-written.

Some summary information is also written to summary.txt

To move to server:
scp Websites/psiz-collect/python/extract_observations.py bdroads@104.236.150.245:/home/bdroads/.psiz-collect/obs/extract_observations.py
