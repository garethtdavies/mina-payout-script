## MinaExplorer Payout Script

This implementation relies on data from minaexplorer.com. A more generally applicable version that takes in a staking ledger and uses the archive node is available here https://github.com/jrwashburn/mina-pool-payout and is **strongly** recommended. The algorithms slightly differ so the outputs from both scripts may not be exactly equal but should be close enough to compare.

THIS WILL NOT CALCULATE THE FOUNDATION SHARE CORRECTLY IF YOU HAVE A FEE DIFFERENT THAN 5%

This is a proof of concept implementation of this [staking calculation](https://docs.minaexplorer.com/minaexplorer/calculating-payments).

To run, change the settings to your requirements in `payout.py` specifying at least a public key and ledger hash. It will only work for one epoch at a time. It uses a fee of 5% but update if yours is different.

```
pip3 install -r requirements.txt
python3 payout.py
```

Will output:

```
python3 payout.py
Using ledger hash: jwAAZcXndLYxb8w4LTU2d4K1qT3dL8Ck2jKzVEf9t9GAyXweQRG
This script will payout from blocks 0 to 10464 in epoch 2
The pool total staking balance is: 12552133.472978499
The Foundation delegation balance is: 3721473.60745647
There are 147 delegates in the pool
We won these 6 blocks:
+-------------+------------------------+--------------+------------------------+---------------------+------------------------+
| BlockHeight | Supercharged Weighting |   Coinbase   | Producer Fee Transfers | Snark Fee Transfers | Coinbase Fee Transfers |
+-------------+------------------------+--------------+------------------------+---------------------+------------------------+
|    10409    |   1.9994836001399277   | 720000000000 |       372000000        |          0          |           0            |
|    10292    |   1.9999805559336348   | 720000000000 |        14000000        |          0          |           0            |
|    10282    |   1.9999666677777408   | 720000000000 |        24000000        |          0          |           0            |
|    10220    |   1.9999833336111064   | 720000000000 |        12000000        |          0          |           0            |
|    10199    |   1.9999833336111064   | 720000000000 |        12000000        |          0          |           0            |
|    10147    |   1.9999666677777408   | 720000000000 |        24000000        |          0          |           0            |
+-------------+------------------------+--------------+------------------------+---------------------+------------------------+
We are paying out 4320458000000 nanomina in this window.
That is 4320.458000000 mina
Our fee is 216.022900000 mina
+---------------------------------------------------------+-------------------+-----------------+---------------+------------+
|                        PublicKey                        |  Staking Balance  | Payout nanomina |  Payout mina  | Foundation |
+---------------------------------------------------------+-------------------+-----------------+---------------+------------+
| B62qkbdgRRJJfqcyVd23s9tgCkNYuGMCmZHKijnJGqYgs9N3UdjcRtR |  6697.563753375   |   2189165541    |  2.189165541  |   False    |
| B62qqMo7X8i2NnMxrtKf3PAWfbEADk4V1ojWhGeH6Gvye9hrMjBiZjM |  32558.703045112  |   10642136981   | 10.642136981  |   False    |
| B62qqomhidaLc7wbYPeaHkGkzXVNA9z7pqf8nL7UjiSZKmLmVT1mPEB |  32558.990000000  |   10642230776   | 10.642230776  |   False    |
| B62qkrhfb1e3fV2HCsFxvnjKp1Yu4UyVpytucWDW16Ri3rzG9Ew2cF4 |  7029.917345033   |   2297798630    |  2.297798630  |   False    |
| B62qraStik5h6MHyJdB39Qd2gY2pPHaKsZFLWVNEv2h3F85T4DmtjC7 |  19282.059003548  |   6302533392    |  6.302533392  |   False    |
| B62qqrn3yzWRDJrUni6cRva4t51AcnY1o1pM4xpB78MfHUH3ajZu1Ko |  65329.909092470  |   21353732694   | 21.353732694  |   False    |
| B62qoB8RRURcit5keJXvq7uXzYkgN4Lsz5GFaVpGYdA9vAiASy3iBcD |  66000.471816426  |   21572912812   | 21.572912812  |   False    |
| B62qowpMhZ2Ww7b8xQxcK7rrpfsL5Nt5Yz5uxaizUBKqpeZUqBETa31 |  66282.077824773  |   21664958545   | 21.664958545  |   False    |
| B62qrdiTDeX3AP6aHn62WUsQ3dT7mH7zA6YUGmJ5R9FJDTac4j6DmPA |  66282.077824773  |   21664958545   | 21.664958545  |   False    |
| B62qrJb5c4yaeL5fDCrEU5tGsmJWbcfnkdW1pMQbGT1rAnnA2JjAP6h |  66282.077824773  |   21664958545   | 21.664958545  |   False    |
| B62qrR8VjjKrijdZ9HgUg5D33CrNCWhDdJr8gvmdFFCizCGgaeANhXT |  66282.077824773  |   21664958545   | 21.664958545  |   False    |
| B62qrAJ7wiP6sJwjM3RsZX3Xzp21BpfkF3yXA49TxPNBHAKrjPLbx4J |  66282.077824773  |   21664958545   | 21.664958545  |   False    |
| B62qj5TbymjFWUsjHnCDNfzbFbacKzXwnHdgDJDoAZwcs5GD2sacGMc |  66282.077824773  |   21664958545   | 21.664958545  |   False    |
| B62qrYkGp44a78p3t6uifiBq2wwctJw3k8u88sKLLAgdAZFK1G8UGcH |  66282.077824773  |   21664958545   | 21.664958545  |   False    |
| B62qmQAFPta1Q3c7wXHxXRKnE3uWyBYZCLb8frdHEgavi3BbBVkpeC1 | 504926.523573708  |  165088943418   | 165.088943418 |    True    |
| B62qn71s63yywMUCcFhP4iCata7HpgyrvmGjpKa1D9544vGW6FBZ6a1 | 904824.004033700  |  295837972128   | 295.837972128 |    True    |
| B62qqEV4oP7w2jLQGckvZzdWjfdLKySKHJ3tNU5niRjpPD7beYumWTB | 610502.785413452  |  199607774784   | 199.607774784 |    True    |
| B62qmsYXFNNE565yv7bEMPsPnpRCsMErf7J2v5jMnuKQ1jgwZS8BzXS | 1701220.294435610 |  556224812568   | 556.224812568 |    True    |
+---------------------------------------------------------+-------------------+-----------------+---------------+------------+
```

Take the output to a different machine to sign - see `sign.ts` for an example.
