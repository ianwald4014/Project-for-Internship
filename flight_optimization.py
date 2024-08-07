#! /usr/bin/env python3

"""This program takes the original naive collection of flight paths
offered by the airline, that collection that went to all possible
destinations, and prunes it based on profitability.

The criterion for eliminating a flight path is if it does not generate
profit above a certain threshold.

After eliminating a flight path, we need to find the *profitable*
flight path that comes closest to the eliminated one.  This metric for
"close" is the sum of distances of eliminated airports to airports on
a still-existing flight path.

So we take all the still-existing flight paths, calculate this metric,
and pick the path with the best metric, and advertise what the
replacement path is.

This program follows the new style of formatting.
"""

import sys
import pprint
import numpy as np
from math import radians, sin, cos, sqrt, atan2

from flight_utils import *

def main():
    """Load all the sorted flights, then do the elimination, then do the
    replacement."""
    sorted_fname = 'sorted_flights_new.txt'
    if len(sys.argv) > 2:
        raise Exception('Too many arguments')
    elif len(sys.argv) == 2:
        sorted_fname = sys.argv[1]
    # get the reordered but un-pruned list from file -- this file,
    # typically, has been generated by sort_flights_by_distance.py
    all_flights = load_flights_newstyle(sorted_fname)
    profitable, eliminated = prune_unprofitable_flights(all_flights)
    # now generate a list of "replacement flightpaths" -- these are
    # paths from the profitable list that come as close as possible to
    # the eliminated list
    replacement_dict = find_replacement_paths(profitable, eliminated)
    print('========== REPLACEMENT_DICT ===========')
    pprint.pprint(replacement_dict)
    print('====== DONE REPLACEMENT_DICT ========')

    # Accommodate passengers from eliminated flights to their replacements
    passengers = accommodate_passengers(profitable, eliminated, replacement_dict)
     
    # finally, save the profitable file, and a file describing replacements
    fname_out = 'profitable_flights.txt'
    write_flights_newstyle(fname_out, profitable)
    print('# wrote_profitable_files:', fname_out)
    
def find_replacement_paths(profitable, eliminated):
    """Takes all the eliminated paths and proposes an alternative
    "replacement" path, based on one of the profitable ones."""
    replacement_dict = {}
    for dead_record in eliminated:
        replacement_record = find_closest_match(profitable, dead_record)
        print(f"REPLACEMENT: Flight {dead_record['flight_number']}: {dead_record['flight_path']} -> Flight {replacement_record['flight_number']}: {replacement_record['flight_path']}")
        print(f"            $ {calc_income(dead_record) - calc_cost(dead_record)}"
              + f"   ->   $ {calc_income(replacement_record) - calc_cost(replacement_record)}")
        key = dead_record['flight_path']
        replacement_dict[key] = replacement_record
    return replacement_dict

def find_closest_match(flight_list, eliminated_record):
    """Scan the flight list to find the one which has the smallest
    cumulative distance to the cities in eliminated_record."""
    records_and_metric_list = []
    for candidate_rec in flight_list:
        candidate_city_list = flight_path2city_list(candidate_rec['flight_path'])
        eliminated_record_city_list = flight_path2city_list(eliminated_record['flight_path'])
        metric = calc_cumulative_distance_metric(candidate_city_list, eliminated_record_city_list)
        records_and_metric_list.append((candidate_rec, metric))
    records_and_metric_list.sort(key=lambda x: x[1])
    return records_and_metric_list[0][0]

def calc_cumulative_distance_metric(clist_candidate, clist_eliminated):
    """Calculates the total "min" distance you'd have to drive to go from
    each eliminated city."""
    sum_of_min_distances = 0
    for elim_city in clist_eliminated:
        distances_to_candidates = [city2city_distance(elim_city, cand_city) for cand_city in clist_candidate]
        sum_of_min_distances += min(distances_to_candidates)
    return sum_of_min_distances

def prune_unprofitable_flights(flight_list):
    """Goes through the list, calculates all costs and income, and removes
    those that fall under a cretain profit threshold."""
    # Set the profit threshold to filter flights with profits less than this value
    profit_threshold = 10000  # Change this value to the desired threshold
    profitable = []
    eliminated = []
    for record in flight_list:
        cost = calc_cost(record)
        income = calc_income(record)
        # print(record['flight_path'], '   ', cost, '   ', income, '   ', income - cost)
        if income - cost >= profit_threshold:
            profitable.append(record)
        else:
            eliminated.append(record)
    return profitable, eliminated

def calc_cost(record):
    """Looks at the flight record and calculate the costs costs for this
    flight path.
    """
    # our operating costs will come entirely from factors we can get
    # from the city list: (a) total flight length, which yields flight
    # time, which yields operational cost; (b) layover costs, which
    # depends on how many intermediate hubs you use.
    speed_knots = 485  # Average speed of a Boeing 737 MAX in knots
    city_list = flight_path2city_list(record['flight_path'])
    distance_nm = calc_distance_new(city_list)
    flight_time = distance_nm / speed_knots
    operational_cost = 5757 * flight_time
    # now that we have operational cost, we add something due to
    # layover time
    n_stops = len(city_list) - 2
    layover_time_hr = 1.5 * n_stops  # from typical averages
    layover_cost_per_hour = 150  # Maintenance cost per hour
    layover_cost = (layover_time_hr * layover_cost_per_hour)
    # total cost comes from adding operational and layover
    total_cost = operational_cost + layover_cost
    return total_cost

def accommodate_passengers(profitable, eliminated, replacement_dict):
    """Accommodates passengers from eliminated flights to their replacement flights.
    If the sum of passengers from the eliminated and replacement flights exceeds 204, 
    the number of accommodated passengers is capped at 204.
    """
    # Create a dictionary to keep track of updated passenger counts
    updated_passengers = {}

    for dead_record in eliminated:
        replacement_record = replacement_dict[dead_record['flight_path']]
        # Calculate the total number of passengers to accommodate
        accommodated_passengers = int(dead_record['passengers']) + int(replacement_record['passengers'])
        
        if accommodated_passengers > 204:
            accommodated_passengers = 204  # Cap at 204 if it exceeds
        
        # Store the updated passenger count
        updated_passengers[replacement_record['flight_path']] = accommodated_passengers
    
    # Update the passenger counts in the profitable flights list
    for record in profitable:
        if record['flight_path'] in updated_passengers:
            record['passengers'] = updated_passengers[record['flight_path']]
    
    return profitable 

def calc_income(record):
    """Looks at the number of passengers, take a typical ticket price, and
    return the income."""
    avg_ticket_price = 384.85
    income = avg_ticket_price * int(record['passengers'])
    return income
   
def main_previous(scoring_method='average') -> None:
    # flight_collection = load_flights_new('sample_paths.txt')
    sorted_flights_newstyle = 'sorted_file_new.txt'
    flight_collection = load_flights_new(sorted_flights_newstyle)
    pprint.pprint(flight_collection, profitable)
    
if __name__ == "__main__":
    main()
