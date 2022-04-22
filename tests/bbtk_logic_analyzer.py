# Time-stamp: <2022-04-20 11:29:05 cp983411>

import pandas as pd
import numpy as np

DEBUG = False


INPUT_PORT_NAMES = ('Keypad4', 'Keypad3', 'Keypad2', 'Keypad1', 'Opto4',
                    'Opto3', 'Opto2', 'Opto1', 'TTLin2', 'TTLin1', 'Mic2',
                    'Mic1')

OUTPUT_PORT_NAMES = ('ActClose4', 'ActClose3', 'ActClose2', 'ActClose1',
                     'TTLout2', 'TTLout1', 'Sounder2', 'Sounder1')


def locate_edges(binary_sequence):
    """Find the positions of leading and falling edges in a binary sequence and
    report the onsets and durations of associated events.

    :param binary_sequence: a sequence of 0s and 1s (int)
    :return: A dataframe with to colmumns: onset and duration of each event
    """
    if isinstance(binary_sequence, (list, pd.core.series.Series)):
        binary_sequence = np.array(binary_sequence)
    assert len(binary_sequence) >= 3 
    assert binary_sequence[0] == 0   # check that the signal is at baseline when starting
    assert binary_sequence[-1] == 0   # check that the signal returned to baseline at the end
    leading_edges = 1 + np.flatnonzero((binary_sequence[:-1] == 0) & (binary_sequence[1:] == 1))
    falling_edges = 1 + np.flatnonzero((binary_sequence[:-1] == 1) & (binary_sequence[1:] == 0))

    if DEBUG:
        print(f"Number of leading edges: {len(leading_edges)}, falling_edges: {len(falling_edges)}")
                                      
    return leading_edges, falling_edges



def convert_raw_events_to_durations(sc_df):
    df_list = []
    for col_name in list(set(events.columns) & set(INPUT_PORT_NAMES)):
        start, end = locate_edges(events[col_name])
        if len(start) != 0:
            df_list.append(pd.DataFrame({'Type': col_name,
                                         'Onset': events.timestamp[start].values,
                                         'Duration': events.timestamp[end].values - events.timestamp[start].values}))

    return pd.concat(df_list, ignore_index=True)


    
#if __name__ == '__main__':
raw_events = pd.read_csv('example_of_dscm_output_1.csv')
dur = convert_raw_events_to_durations(raw_events)
print(dur)


