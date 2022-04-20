# Time-stamp: <2022-04-20 11:29:05 cp983411>

import pandas as pd
import numpy as np

def locate_events(sampling_times, binary_sequence):
    """Find the positions of leading and falling edges in a binary sequence and
    report the onsets and durations of associated events.

    :param binary_sequence: a sequence of 0s and 1s (int)
    :return: A dataframe with to colmumns: onset and duration of each event

    Example::

    .. warning:
       The numbers of leading and falling edges may not match if the state differ on the first and last lines!
    """
    leading_edges = 1 + np.flatnonzero((binary_sequence[:-1] == 0) & (binary_sequence[1:] == 1))
    falling_edges = 1 + np.flatnonzero((binary_sequence[:-1] == 1) & (binary_sequence[1:] == 0))

    if len(leading_edges) > len(falling_edges):
        # there is a event that started but not ended
        # LEt's assume it is the last one, and we remove it (TODO: clean potential BUG!)
        leadind_edges = leading_edges[-len(leading_edges)]

                                      
    #print(sampling_times)
    #print(leading_edges)
    onsets = sampling_times[leading_edges]
    durations = sampling_times[falling_edges] - onsets
                                      
    return pd.DataFrame(({'onset': onsets, 'duration': durations}))


#if __name__ == '__main__':
events = pd.read_csv('example_of_dscm_output.csv')

print(locate_events(events.timestamp, events.Opto1))
