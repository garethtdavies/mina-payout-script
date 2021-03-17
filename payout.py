################################################################
# This is a testnet implementation of the payout system listed at
# https://docs.minaexplorer.com/minaexplorer/calculating-payments
# It is not meant for production use. This will output or store the
# payments which must then be processed seperately e.g. by signing
# the tx using coda sdk and then broadcasting.
################################################################

from tabulate import tabulate
import Currency
import GraphQL
import Mongo

client = Mongo.Mongo()

################################################################
# Define the payout calculation here
################################################################
public_key = "B62qpge4uMq4Vv5Rvc8Gw9qSquUYd6xoW1pz7HQkMSHm6h1o7pvLPAN"  # Public key of the block producer
ledger_hash = "jwkHcod9dcnhGfYx7t6yabSfckrKVwD6TJECs6oPSL8teYQE37Y"  # The ledger hash to use for calculations
staking_epoch = 0  # To ensure we only get blocks from the current staking epoch as the ledger may be different
fee = 0.05  # The fee percentage to charge
min_height = 1  # This can be the last known payout or this could vary the query to be a starting date
confirmations = 0  # Can set this to any value for min confirmations up to `k`

# Get the latest block height from MinaExplorer
latest_block = GraphQL.getLatestHeight()

if not latest_block:
    exit("Issue getting the latest height")

assert latest_block["data"]["blocks"][0]["blockHeight"] > 1

# Only ever pay out confirmed blocks
max_height = latest_block["data"]["blocks"][0]["blockHeight"] - confirmations

assert max_height <= latest_block["data"]["blocks"][0]["blockHeight"]

print(f"This script will payout from blocks {min_height} to {max_height}")

# Initialize variables
total_staking_balance = 0
payouts = []
all_blocks_total_rewards = 0
all_blocks_total_fees = 0
blocks_included = []

# Get the staking ledger for an epoch
try:
    staking_ledger = GraphQL.getStakingLedger({
        "delegate": public_key,
        "ledgerHash": ledger_hash,
    })
except Exception as e:
    print(e)
    exit("Issue getting staking ledger from GraphQL")

if not staking_ledger["data"]["stakes"]:
    exit("We have no stakers")

for s in staking_ledger["data"]["stakes"]:
    
    # Clean up timed weighting if no timing info
    if not s["timing"] or not s["timing"]["timed_weighting"]:
        timed_weighting = 1
    else:
        timed_weighting = s["timing"]["timed_weighting"]
    
    # skip if delegated balance == 0
    if float(s["balance"]) == 0:
        print(f'Skipping {s["public_key"]} since balance is {s["balance"]}')
        continue
    
    payouts.append({
        "publicKey":
        s["public_key"],
        "total":
        0,
        "staking_balance":
        s["balance"],
        "timed_weighting": timed_weighting
    })
    total_staking_balance += s["balance"]

# DEBUG
# print(payouts)

# We now know the total pool staking balance with total_staking_balance
print(f"The pool total staking balance is: {total_staking_balance}")

# Who are we going to pay?
print(f"There are {len(payouts)} delegates in the pool")

try:
    blocks = GraphQL.getBlocks({
        "creator": public_key,
        "epoch": staking_epoch,
        "blockHeightMin": min_height,
        "blockHeightMax": max_height,
    })
except Exception as e:
    print(e)
    exit("Issue getting blocks from GraphQL")

#DEBUG
# print(blocks)

if not blocks["data"]["blocks"]:
    exit("Nothing to payout as we didn't win anything")

################################################################
# Start of blocks loop
################################################################
for b in blocks["data"]["blocks"]:

    # Keep a log of all blocks we processed
    blocks_included.append(b["blockHeight"])

    # This will always be defined even if it pays to the creator
    coinbase_receiver = b["transactions"]["coinbaseReceiverAccount"]["publicKey"]

    sum_effective_pool_stakes = 0
    effective_pool_stakes = {}

    # Determine the supercharged weighting for the block
    supercharged_weighting = 1 + (
        1 / (1 + int(b["txFees"]) / int(b["transactions"]["coinbase"])))

    # What are the rewards for the block
    total_rewards = int(b["transactions"]["coinbase"]) + int(
        b["txFees"]) - int(b["snarkFees"])

    total_fees = int(0.05 * total_rewards)

    all_blocks_total_rewards += total_rewards
    all_blocks_total_fees += total_fees

    # Let's run some checks to ensure we don't pay out more than we got, or find bugs ;)
    if "feeTransfer" not in b["transactions"]:
        # Just coinbase
        assert total_rewards == int(b["transactions"]["coinbase"])
    else:
        # There were some fee transfers so let's _really_ make sure we don't pay out more than we received
        fee_transfers = b["transactions"]["feeTransfer"]
        bp_fee_transfers = [d for d in fee_transfers if d['recipient'] == coinbase_receiver]
        sum_bp_fee_transfers = sum(int(item['fee']) for item in bp_fee_transfers)

        # So assert that the value we are paying out is equal to what we received
        total_rewards_fee_transfer = int(b["transactions"]["coinbase"]) + sum_bp_fee_transfers
        # There is an issue here with the type `fee_transfer_via_coinbase` as we actually need to subtract
        # this from the amount to get the amount we received via fee transfers. We can't get this via GraphQL
        # so the best we can do is assert we are playing equal or less than this amount. This will be updated when
        # the fix is landed.
        assert(total_rewards <= total_rewards_fee_transfer)

    # Loop through our list of delegates to determine the weighting per block
    for p in payouts:
        supercharged_contribution = (
            (supercharged_weighting - 1) * p["timed_weighting"]) + 1
        effective_stake = p["staking_balance"] * supercharged_contribution
        effective_pool_stakes[p["publicKey"]] = effective_stake
        sum_effective_pool_stakes += effective_stake

    # Sense check the effective pool stakes must be at least equal to total_staking_balance and less than 2x
    assert total_staking_balance <= sum_effective_pool_stakes <= 2 * total_staking_balance

    # Determine the effective pool weighting based on sum of effective stakes
    for p in payouts:
        effective_pool_weighting = effective_pool_stakes[
            p["publicKey"]] / sum_effective_pool_stakes

        #This must be less than 1 or we have a major issue
        assert effective_pool_weighting <= 1

        block_total = round(
            (total_rewards - total_fees) * effective_pool_weighting)
        p["total"] += block_total

        # Store this data in a structured format for later querying and for the payment script, handled seperately
        store_payout = {
            "publicKey": p["publicKey"],
            "blockHeight": b["blockHeight"],
            "stateHash": b["stateHash"],
            "totalPoolStakes": total_staking_balance,
            "effectivePoolWeighting": effective_pool_weighting,
            "effectivePoolStakes": effective_pool_stakes[p["publicKey"]],
            "stakingBalance": p["staking_balance"],
            "sumEffectivePoolStakes": sum_effective_pool_stakes,
            "superChargedWeighting": supercharged_weighting,
            "dateTime": b["dateTime"],
            "coinbase": int(b["transactions"]["coinbase"]),
            "totalRewards": total_rewards,
            "payout": block_total,
            "epoch": staking_epoch,
            "ledgerHash": ledger_hash
        }

        try:
            #post_id = client.collection.insert_one(store_payout)
            # Store this somewhere I am using Mongo
            pass
        except Exception as e:
            print(e)
            exit("There was an issue storing a payout")

################################################################
# Print some helpful data to the screen
################################################################

print(f"We won these blocks: {blocks_included}")

print(f"We are paying out {all_blocks_total_rewards} nanomina in this window.")

print("That is " +
      Currency.Currency(all_blocks_total_rewards,
                        format=Currency.CurrencyFormat.NANO).decimal_format() +
      " mina")

print(f"Our fee is is " +
      Currency.Currency(all_blocks_total_fees,
                        format=Currency.CurrencyFormat.NANO).decimal_format() +
      " mina")

payout_table = []
payout_json = []

for p in payouts:
    payout_table.append([
        p["publicKey"], p["total"],
        Currency.Currency(
            p["total"], format=Currency.CurrencyFormat.NANO).decimal_format()
    ])

    payout_json.append({"publicKey": p["publicKey"], "total": p["total"]})

print(
    tabulate(payout_table,
             headers=["PublicKey", "Payout nanomina", "Payout mina"],
             tablefmt="pretty"))

# This is the payout json we are taking the the next stage to sign. So store this somewhere.
print(payout_json)
