BTCeArbitrage
=============

A tool for detecting cross-currency arbitrage oportunities within the BTC-e bitcoin exchange

This tool uses the python api from https://github.com/alanmcintyre/btce-api.git

    usage: BTCeArbitrage.py [-h] [-i INPUT] [-o OUTPUT] [-v VOL] [-t INTERVAL]
                            [-l LOG]
    
    optional arguments:
      -h, --help            show this help message and exit
      -i INPUT, --input INPUT
                            Input file for BTCe price map
      -o OUTPUT, --output OUTPUT
                            Output file for BTCe price map
      -v VOL, --vol VOL     Starting volume for trades
      -t INTERVAL, --interval INTERVAL
                            Number of seconds between updates
      -l LOG, --log LOG     Log file

Check the log file for more information on what trade paths are computed and how the pricing and oportunities are evaluated.  An example of what you might see:

    $ ./BTCeArbitrage.py 
    2013-10-30 16:46:38,920 INFO: Downloading BTC-e fee map
    2013-10-30 16:46:50,727 INFO: Downloading BTC-e price map
    2013-10-30 16:47:06,443 INFO: Saving updated BTC-e price map to BTCeArbitrage.dat
    2013-10-30 16:47:06,492 INFO: Constructing possible trade loops
    2013-10-30 16:47:06,656 INFO: 404 possible trade loops detected
    2013-10-30 16:47:06,656 INFO: Calculating viable trade paths based on volume
    2013-10-30 16:47:06,817 INFO: Determining arbitrage oportunities
    2013-10-30 16:47:06,817 INFO: No arbitrage opotunities detected :-(
    ...
    2013-10-30 17:04:07,575 INFO: Downloading BTC-e price map
    2013-10-30 17:04:44,493 INFO: Saving BTC-e price map to BTCeArbitrage.dat
    2013-10-30 17:04:44,541 INFO: Calculating viable trade paths based on volume
    2013-10-30 17:04:44,698 INFO: Determining arbitrage oportunities
    2013-10-30 17:04:44,698 INFO: Arbitrage oportunities detected :-D !!!
    2013-10-30 17:04:44,698 INFO: ========================================
    2013-10-30 17:04:44,698 INFO: usd -> ltc -> btc -> usd
    2013-10-30 17:04:44,698 INFO:   1.000000 usd -> ltc @ 0.459833 * 0.9980
    2013-10-30 17:04:44,698 INFO:   0.458913 ltc -> btc @ 0.011290 * 0.9980
    2013-10-30 17:04:44,698 INFO:   0.005171 btc -> usd @ 194.000000 * 0.9980
    2013-10-30 17:04:44,698 INFO:   1.001123 usd
    2013-10-30 17:04:44,698 INFO: 
    2013-10-30 17:04:44,698 INFO: ltc -> btc -> usd -> ltc
    2013-10-30 17:04:44,699 INFO:   1.000000 ltc -> btc @ 0.011290 * 0.9980
    2013-10-30 17:04:44,699 INFO:   0.011267 btc -> usd @ 194.000000 * 0.9980
    2013-10-30 17:04:44,699 INFO:   2.181508 usd -> ltc @ 0.459826 * 0.9980
    2013-10-30 17:04:44,699 INFO:   1.001107 ltc
    2013-10-30 17:04:44,699 INFO: 
    2013-10-30 17:05:06,725 INFO: 
    2013-10-30 17:05:06,725 INFO: Downloading BTC-e price map
    2013-10-30 17:05:43,804 INFO: Saving BTC-e price map to BTCeArbitrage.dat
    2013-10-30 17:05:43,852 INFO: Calculating viable trade paths based on volume
    2013-10-30 17:05:44,008 INFO: Determining arbitrage oportunities
    2013-10-30 17:05:44,008 INFO: No arbitrage opotunities detected :-(

If you like this tool and happen to think it's useful, donations are always welcome :-)

    BTC 1cjmB1YMsm8BqXjUKjBtJu5BprnCdy71K

Also, I'm always open to features or pull requests :-)
