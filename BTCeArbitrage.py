#!/usr/bin/env python

########################################################################
# Copyright (c) 2013 Chuck Atkins
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
########################################################################
# 
# A tool for detecting cross-currency arbitrage oportunities within the BTC-e
# bitcoin exchange
#
########################################################################


import sys
import re
import argparse
import pickle
import logging
import time
import datetime
import httplib
import socket

import btceapi

log = logging.getLogger()

fee_map = {}
price_map = {}
btce_conn = btceapi.common.BTCEConnection()

def deep_clone_dict_dict(d):
    '''Perform a deep copy of a dictionary of dicionaries of lists of tuples'''
    result = {}
    for src, dst_map in d.items():
        result[src] = {}
        for dst, depth in dst_map.items():
            result[src][dst] = [(p,v) for (p,v) in depth]
    return result


def traverse(src):
    '''Traverse the trade graph and locate all possible cycles for src node'''
    all_paths = []
    traverse_helper(src, src, [], price_map, all_paths)
    return all_paths


def traverse_helper(src0, src, path, price_map, all_paths):
    '''Helper function to recursively traverse the trading graph

        src0        The root node of the path
        src         The current node we're visiting
        path        The path that has been traversed so far
        price_map   A map of all pricing / node connections
        all_paths   Output list of all detected cycles
    '''
    path.append(src)

    # Determine if we have arrived home and the cycle is complete
    if len(path) > 1 and src == src0:
        log.debug(' -> '.join(path))
        all_paths.append(path)
        return

    # Deep copy the price map so we can modify at will
    price_map_no_src = deep_clone_dict_dict(price_map)

    # Make sure this node is no longer afailable as a src
    del price_map_no_src[src]

    # Make sure this node is no longer available as a dst
    if src != src0:
        for s0 in price_map_no_src.keys():
            if src in price_map_no_src[s0]:
                del price_map_no_src[s0][src]

    # Walk all adjacent verticies
    for dst in price_map[src].keys():
        traverse_helper(src0, dst, list(path), price_map_no_src, all_paths)


def compute_path_results(trade_paths, starting_vol):
    '''Execute the sequence of trades across all specified paths

        trade_paths     Collection of all viable trade paths
        starting_vol    The volume to start trading with
        fee             Transaction fee %
    '''
    path_results = []
    for src, src_paths in trade_paths.items():
        for path in src_paths:
            vol = execute_trade_path(path, starting_vol)

            # volume < 0 means thatpath was unable to be traversed
            if vol >= 0:
                path_results.append((path, vol))
            else:
                log.debug('Skipping %s due to volume constraints' % ' -> '.join(path))
    return path_results


def execute_trade_path(path, starting_vol):
    '''Execute the sequence of trades and determine the result

        path            Sequence of nodes to create a trade path
        starting_vol    The volume to start trading with
    '''
    log.debug(' -> '.join(path))
    vol = starting_vol
    for i in range(0, len(path)-1):
        src = path[i]
        dst = path[i+1]
        fs = 1.0-fee_map[src][dst]

        # Filter out any trades for which the current order book does not have
        # sufficient volume for
        depth = [(p,v) for (p,v) in price_map[src][dst] if v >= vol*fs]
        if not depth:
            return -1

        # Execute the trade
        price = depth[0][0]
        log.debug('  %8f %s -> %s @ %8f * %4f' % (vol,src,dst,price,fs))
        vol *= price*fs
    log.debug('  %f %s' % (vol, dst))
    return vol


def print_trade_path(path, starting_vol):
    '''Display the sequence of trades for a given path

        path            Sequence of nodes to create a trade path
        starting_vol    The volume to start trading with
    '''
    log.info(' -> '.join(path))
    vol = starting_vol
    for i in range(0, len(path)-1):
        src = path[i]
        dst = path[i+1]
        fs = 1.0-fee_map[src][dst]
        depth = [(p,v) for (p,v) in price_map[src][dst] if v >= vol*fs]
        if not depth:
            return
        price = depth[0][0]
        log.info('  %8f %s -> %s @ %8f * %4.4f' % (vol,src,dst,price,fs))
        vol *= price*fs
    log.info('  %f %s' % (vol, dst))


def get_trade_fee_retry(pair, retries=10):
    '''Call the getTradeFee call using a persistent connection'''
    global btce_conn
    while retries > 0:
        try:
            return btceapi.public.getTradeFee(pair, btce_conn)
        except (httplib.BadStatusLine,socket.gaierror):
            retries -= 1
            log.debug('getTradeFee failed.  Reconnecting with %d tries remaining.' % retries)
            btce_conn = btceapi.common.BTCEConnection()
    return -1


def download_fee_map():
    '''Retrieve the fee schedule for all trading pairs'''
    f_map = {}
    for pair in btceapi.common.all_pairs:
        [src, dst] = pair.split('_')
        if src not in f_map:
            f_map[src] = {}
        if dst not in f_map:
            f_map[dst] = {}

        log.debug('Downloading trade fee for %s' % pair)
        fee = float(get_trade_fee_retry(pair))*0.01
        f_map[src][dst] = fee
        f_map[dst][src] = fee
    return f_map


def get_depth_retry(pair, retries=10):
    '''Call the getDepth call using a persistent connection'''
    global btce_conn
    while retries > 0:
        try:
            return btceapi.public.getDepth(pair, btce_conn)
        except (httplib.BadStatusLine,socket.gaierror):
            retries -= 1
            log.debug('getDepth failed.  Reconnecting with %d tries remaining.' % retries)
            btce_conn = btceapi.common.BTCEConnection()
    return [],[]

def download_price_map():
    '''Retrieve the map of all pricing information from BTCe'''
    p_map = {}
    for pair in btceapi.common.all_pairs:
        [src, dst] = pair.split('_')
        if src not in p_map:
            p_map[src] = {}
        if dst not in p_map:
            p_map[dst] = {}

        log.debug('Downloading order depth for %s' % pair)
        asks, bids = get_depth_retry(pair)
        p_map[src][dst] = [(float(p),float(v)) for (p,v) in bids]
        p_map[dst][src] = [(float(1/p),float(p*v)) for (p,v) in asks]
    return p_map


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--input',  help='Input file for BTCe price map')
    parser.add_argument('-o', '--output', help='Output file for BTCe price map',
                        default='BTCeArbitrage.dat')
    parser.add_argument('-v', '--vol',    help='Starting volume for trades',
                        type=float, default=1.0)
    parser.add_argument('-t', '--interval',
                        help='Number of seconds between updates',
                        type=int, default=60)
    parser.add_argument('-l', '--log',    help='Log file',
                        default='BTCeArbitrage.log')
    args = parser.parse_args()

    # Configure more verbose to a file
    logging.basicConfig(format='%(asctime)s %(levelname)s: %(message)s',
                        level=logging.DEBUG, filename=args.log, filemode='w')
    log_fmt = logging.Formatter('%(asctime)s %(levelname)s: %(message)s')
    log_ch = logging.StreamHandler()
    log_ch.setLevel(logging.INFO)
    log_ch.setFormatter(log_fmt)
    log.addHandler(log_ch)

    # Load the price map from a file
    global price_map
    global fee_map
    if args.input:
        log.info('Loading BTC-e price map from %s' % args.input)
        with open(args.input, 'rb') as pkl_dict:
            (fee_map, price_map) = pickle.load(pkl_dict)

    # Or download if not specified
    else:
        log.info('Downloading BTC-e fee map')
        fee_map = download_fee_map()
        log.info('Downloading BTC-e price map')
        price_map = download_price_map()

    log.info('Constructing possible trade loops')
    all_src = price_map.keys()
    trade_paths = {}
    num_loops = 0
    for src in all_src:
        trade_paths[src] = traverse(src)
        num_loops += len(trade_paths[src])
    log.info('%d possible trade loops detected' % num_loops)
    log.info('')

    tsleep = datetime.timedelta(seconds=args.interval)
    tnext = datetime.datetime.now() + tsleep
    while True:
        log.info('Downloading BTC-e price map')
        price_map = download_price_map()

        log.info('Saving new BTC-e price map to %s' % args.output)
        with open(args.output, 'wb') as pkl_dict:
            pickle.dump((fee_map,price_map), pkl_dict)

        log.info('Calculating viable trade paths based on volume')
        path_results = compute_path_results(trade_paths, args.vol)

        log.info('Determining arbitrage oportunities')
        arbitrage_paths = [p for (p,v) in path_results if v > args.vol]

        if arbitrage_paths:
            log.info('Arbitrage oportunities detected :-D !!!')
            log.info('='*40)
            for path in arbitrage_paths:
                print_trade_path(path, args.vol)
                log.info('')
        else:
            log.info('No arbitrage opotunities detected :-(')
        log.info('')

        while datetime.datetime.now() < tnext:
            time.sleep(1)
        tnext += tsleep

    return 0

if __name__ == '__main__':
    sys.exit(main())

