import pandas as pd
import os

def read_csv(filename):
    df = pd.read_csv(filename, skiprows=8)
    df.rename(columns={'# timestamp': 'timestamp'}, inplace=True)
    df = df.melt(id_vars='timestamp')
    prefix = os.path.basename(filename).replace('.csv','')
    df['attribute'] = prefix
    return df

def read_dir(filenames):
    df = pd.concat([ read_csv(x) for x in filenames ], axis=0, sort=False)  # axis = 0 for stacking
    #df.index = pd.to_datetime(df.index)
    tmp = df.pivot_table(index='timestamp', columns=['variable', 'attribute'], values='value')
    tmp.index = pd.to_datetime(tmp.index)
    final = tmp.reset_index().melt(id_vars='timestamp')
    return final
