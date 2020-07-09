import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from datacontroller import DatabaseController

db = DatabaseController.get_heroku_db()

case_ids = db.fetch_all_case_ids()

print('Case ids: ', *case_ids, sep='\n')

case_id = None
while case_id not in case_ids:
    case_id = input('Choose case id: ').strip()

# fetch the first 500 of each category for case_id
data_normal = db.fetch_as_df(f'SELECT * FROM data WHERE label_temp="normal" AND caseid="{case_id}" ORDER BY id ASC LIMIT 500;')
data_split = db.fetch_as_df(f'SELECT * FROM data WHERE label_temp="split" AND caseid="{case_id}" ORDER BY id ASC LIMIT 500;')
data_unclassified = db.fetch_as_df(f'SELECT * FROM data WHERE label_temp="unclassified" AND caseid="{case_id}" ORDER BY id ASC LIMIT 500;')

data_all = pd.concat([data_normal, data_split, data_unclassified])

# select first 100 rows where label is None
data_normal_filtered = data_normal[data_normal['label'].isnull()].head(100)
data_split_filtered = data_split[data_split['label'].isnull()].head(100)
data_unclassified_filtered = data_unclassified[data_unclassified['label'].isnull()].head(100)

data_all_filtered = pd.concat([data_normal_filtered, data_split_filtered, data_unclassified_filtered])

current_row_iter = data_all_filtered.iterrows()

while True:
    _, current_row = next(current_row_iter)
    current_id = current_row['id']
    current_egm = np.fromstring(current_row['egm'], sep=' ', dtype=np.float)

    # find nn5
    nn5_ids = [int(i) for i in current_row['nn5'].split(',')]
    nn5 = []
    for index, row in data_all.iterrows():
        if row['id'] in nn5_ids:
            egm = row['egm']
            egm = np.fromstring(egm, sep=' ', dtype=np.float)
            nn5.append(egm)
            if len(nn5) == 5:
                break
    # skip if not found
    if len(nn5) != 5:
        print(f'Skipped {current_row["id"]}, found nn5: {len(nn5)}')
        continue

    # plot
    egms = [current_egm, *nn5]
    fig, axes = plt.subplots(6, 1)
    for i, ax in enumerate(axes):
        egm = egms[i]
        # calc y limits
        min = np.min(egm) * 1.3
        max = np.max(egm) * 1.3
        ax.plot(egm)
        ax.set_ylim(min, max)
        if i == 0:
            ax.set_title(f'Current EGM {current_id}')
    
    plt.show()

    # input label
    prompt = '''
    Enter label:
    [-1] skip
    [0] normal
    [1] split
    [2] unclassified
    '''
    label = None
    while label not in [-1, 0, 1, 2]:
        label = int(input(prompt))
    
    if label == -1:
        continue
    # translate to str
    label = ['normal', 'split', 'unclassified'][label]

    # upload to db
    db.execute(f'UPDATE data SET label="{label}" WHERE caseid="{case_id}" AND id="{current_id}";')
