## MinaExplorer Payout Script

This implementation relies on data from Minaexplorer.com. A more generally applicable version that takes in a staking ledger and uses the archive node is available here https://github.com/jrwashburn/mina-pool-payout and is strongly recommended.

This is a proof of concept implementation of this [staking calculation](https://docs.minaexplorer.com/minaexplorer/calculating-payments). 

To run, change the settings to your requirements in `payout.py` specifying at least a public key and ledger hash. It uses a fee of 5% but update if yours is different.

```
pip3 install -r requirements.txt
python3 payout.py
```

Will output:

```
This script will payout from blocks 0 to 379
The pool total staking balance is: 66000
There are 1 delegates in the pool
We won these blocks: [354, 320]
We are paying out 1443471280000 nanomina in this window.
That is 1443.471280000 mina
Our fee is is 72.173564000 mina
+---------------------------------------------------------+-----------------+----------------+
|                        PublicKey                        | Payout nanomina |  Payout mina   |
+---------------------------------------------------------+-----------------+----------------+
| B62qp2K4i6oSoNtKk34nothCJcjCwwjjdfjQhnmt6xuduAfj7EnahVy |  1371297716000  | 1371.297716000 |
+---------------------------------------------------------+-----------------+----------------+
[{'publicKey': 'B62qp2K4i6oSoNtKk34nothCJcjCwwjjdfjQhnmt6xuduAfj7EnahVy', 'total': 1371297716000}]
```

Take the output to a different machine to sign - see `sign.ts` for an example.
