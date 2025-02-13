import pooch

def filter_files(
        available_files: list,
        task: str = 'all',
        split: str = 'both',
        exclude: list = None,
        include: list = None
) -> tuple | list:
    """
    Function to filter files based on specifications.

    :param available_files: List of file paths.
    :param task: String specifying which task to load. Either of:
        - "level-1-smooth": Loads data from level-1 smooth experiment.
        - "level-1-saccades": Loads data from level-1 saccades experiment.
        - "level-2-smooth": Loads data from level-1 smooth experiment.
        - "level-2-saccades": Loads data from level-2 saccades experiment.
        - "level-1": Loads data from all level-1 experiments.
        - "level-2": Loads data from all level-2 experiments.
        - "smooth": Loads data from all smooth experiments.
        - "saccades": Loads data from all saccades experiments.
        - "all": Loads data from all experiments (default).
    :param split: String specifying which subset to load. Either of:
        - "train": Loads training data.
        - "test": Loads test data.
        - "both": Loads training and test data.
    :param exclude: List of recordings to exclude, given in the format
        "PXXX_YY", where XXX denotes the participant number and YY the session
        number.
    :param include: List of recordings to exclude, given in the format
        "PXXX_YY", where XXX denotes the participant number and YY the session
        number.
    :return: Returns a list of file paths, if 'split' in ['train', 'test'], and
        a tuple of both lists, if 'split' == 'both'.
    """

    if task == 'all':
        selected_files = available_files
    else:
        selected_files = [fp for fp in available_files if task in fp]

    if exclude is not None:
        selected_files = [fp for fp in selected_files
                          if not any(rec_id in fp for rec_id in exclude)]

    if include is not None:
        selected_files = [fp for fp in selected_files
                          if any(rec_id in fp for rec_id in include)]

    train_file = [fp for fp in selected_files if 'train' in fp]
    test_file = [fp for fp in selected_files if 'test' in fp]

    if split == 'both':
        files = train_file, test_file
    elif split == 'train':
        files = train_file
    elif split == 'test':
        files = test_file
    else:
        raise ValueError("Split must be either 'both' or 'train' or 'test'.")

    return files


def fetch_data(
        task: str = 'all',
        split: str = 'both',
        exclude: list = None,
        include: list = None
) -> tuple | list:
    """
    Function to fetch and manage data with the pooch module. The data is only
    downloaded ones.

    See the description of filter_files() for a description of keyword arguments.
    """
    data_fetcher = pooch.create(
        path=pooch.os_cache("eeg_eye_tracking"),
        base_url="doi:10.5281/zenodo.14860668",
        registry=None,
    )

    data_fetcher.load_registry_from_doi()
    available_files = data_fetcher.fetch(
        "csv_preprocessed.zip",
        processor=pooch.Unzip()
    )

    selected_files = filter_files(
        available_files,
        task=task,
        split=split,
        exclude=exclude,
        include=include
    )

    return selected_files


if __name__ == '__main__':
    files = fetch_data()
    print(files)
