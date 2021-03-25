################################################################
# This is a POC implementation of the payout system listed at
# https://docs.minaexplorer.com/minaexplorer/calculating-payments
# It is not meant for production use. This will output or store the
# payments which must then be processed seperately e.g. by signing
# the tx using coda sdk and then broadcasting. A better implementation is
# at https://github.com/jrwashburn/mina-pool-payout and recommended
################################################################

from tabulate import tabulate
import Currency
import GraphQL
import Mongo
import os
import math

client = Mongo.Mongo()

################################################################
# Define the payout calculation here
################################################################
public_key = "B62qpge4uMq4Vv5Rvc8Gw9qSquUYd6xoW1pz7HQkMSHm6h1o7pvLPAN"  # Public key of the block producer
ledger_hash = "jx7buQVWFLsXTtzRgSxbYcT8EYLS8KCZbLrfDcJxMtyy4thw2Ee"  # The ledger hash to use for calculations
staking_epoch = 0  # To ensure we only get blocks from the current staking epoch as the ledger may be different
fee = 0.05  # The fee percentage to charge
min_height = 0  # This can be the last known payout or this could vary the query to be a starting date
confirmations = 12  # Can set this to any value for min confirmations up to `k`
store = False  # Do we want to store this
foundation_delegations = [
    "B62qmsYXFNNE565yv7bEMPsPnpRCsMErf7J2v5jMnuKQ1jgwZS8BzXS",
    "B62qn71s63yywMUCcFhP4iCata7HpgyrvmGjpKa1D9544vGW6FBZ6a1",
    "B62qqEV4oP7w2jLQGckvZzdWjfdLKySKHJ3tNU5niRjpPD7beYumWTB",
    "B62qmQAFPta1Q3c7wXHxXRKnE3uWyBYZCLb8frdHEgavi3BbBVkpeC1"
]  # Could determine this from an API / predefined list but hardcoded for development
coinbase = 720000000000  # Later we can set this dynamically - this is because we don't care about supercharged for Foundation

# Get the latest block height
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
total_staking_balance_foundation = 0
payouts = []
all_blocks_total_rewards = 0
all_blocks_total_fees = 0
blocks_included = []
store_payout = []

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

    # Clean up timed weighting if no timing info as then they are untimed
    if not s["timing"]:
        timed_weighting = 1
    else:
        timed_weighting = s["timing"]["timed_weighting"]

    # Is this a Foundation address
    if s["public_key"] in foundation_delegations:
        foundation_delegation = True
        total_staking_balance_foundation += s["balance"]
    else:
        foundation_delegation = False

    payouts.append({
        "publicKey": s["public_key"],
        "total": 0,
        "staking_balance": s["balance"],
        "timed_weighting": timed_weighting,
        "foundation_delegation": foundation_delegation
    })

    # Sum the total of the pool
    total_staking_balance += s["balance"]

# DEBUG
# print(payouts)

assert (total_staking_balance_foundation <= total_staking_balance)

# We now know the total pool staking balance with total_staking_balance
print(f"The pool total staking balance is: {total_staking_balance}")

print(
    f"The Foundation delegation balance is: {total_staking_balance_foundation}"
)

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

    # Keep track of payouts per block
    foundation_payouts = 0
    other_payouts = 0

    # This will always be defined except when it is not...
    if not b["transactions"]["coinbaseReceiverAccount"]:
        print(
            f"{b['blockHeight']} didn't have a coinbase so won it but no rewards."
        )
        break

    coinbase_receiver = b["transactions"]["coinbaseReceiverAccount"][
        "publicKey"]

    # Keep a log of all blocks we processed
    blocks_included.append(b["blockHeight"])

    # This is to keep track of non-Foundation delegates
    sum_effective_pool_stakes = 0
    effective_pool_stakes = {}

    ####################################
    # FEE TRANSFERS
    ####################################
    fee_transfers = list(
        filter(lambda d: d['type'] == "Fee_transfer",
               b["transactions"]["feeTransfer"]))

    fee_transfers_by_coinbase = list(
        filter(lambda d: d['type'] == "Fee_transfer_via_coinbase",
               b["transactions"]["feeTransfer"]))

    total_fee_transfers = sum(int(item['fee']) for item in fee_transfers)
    # Note there can be more than 1 coinbase
    fee_transfer_for_coinbase = sum(
        int(item['fee']) for item in fee_transfers_by_coinbase)

    # Sum all the fee transfers to this account with type of fee_transfer - these are the tx fees
    fee_transfer_to_creator = list(
        filter(lambda d: d['recipient'] == coinbase_receiver, fee_transfers))
    total_fee_transfers_to_creator = sum(
        int(item['fee']) for item in fee_transfer_to_creator)

    # Sum all the fee transfers not to this account with type of fee_transfer - this is snark work for the included tx
    fee_transfer_to_snarkers = total_fee_transfers - total_fee_transfers_to_creator

    # Determine the supercharged weighting for the block

    # New way uses fee transfers so we share the resulting profitability of the tx and take into account the coinbase snark
    supercharged_weighting = 1 + (
        1 / (1 + (int(total_fee_transfers_to_creator) - int(fee_transfer_to_snarkers)) / (int(b["transactions"]["coinbase"]) - int(fee_transfer_for_coinbase))))

    # What are the rewards for the block - this is how we used to calculate it
    # this serves as a sense check currently to check logic
    total_rewards_prev_method = int(b["transactions"]["coinbase"]) + int(
        b["txFees"]) - int(b["snarkFees"])

    # Can also define this via fee transfers
    total_rewards = int(
        b["transactions"]["coinbase"]
    ) + total_fee_transfers_to_creator - fee_transfer_to_snarkers - fee_transfer_for_coinbase

    #print(total_fee_transfers_to_creator,fee_transfer_to_snarkers,fee_transfer_for_coinbase)

    # We calculate rewards multiple ways to sense check
    assert (total_rewards == total_rewards_prev_method)

    total_fees = int(fee * total_rewards)

    all_blocks_total_rewards += total_rewards
    all_blocks_total_fees += total_fees

    #######################################################
    # Determine the amount we need to pay the Foundation
    # This algorithm is according to the published rules
    # We don't need to account for supercharged rewards or
    # share the transaction fees, so this is **good** for the pool
    # as we share all these rewards. We first work out the Foundation
    # payments and then subtract from the total rewards before sharing
    # the remainder among the pool
    #######################################################

    for p in payouts:

        if p["foundation_delegation"]:

            # Only pay foundation a % of the normal coinbase
            # Round down to the nearest nanomina
            foundation_block_total = math.floor(
                (p["staking_balance"] / total_staking_balance) * coinbase *
                (1 - fee))

            p["total"] += foundation_block_total

            store_payout.append({
                "publicKey": p["publicKey"],
                "blockHeight": b["blockHeight"],
                "stateHash": b["stateHash"],
                "totalPoolStakes": total_staking_balance,
                "stakingBalance": p["staking_balance"],
                "dateTime": b["dateTime"],
                "coinbase": int(b["transactions"]["coinbase"]),
                "totalRewards": total_rewards,
                "payout": foundation_block_total,
                "epoch": staking_epoch,
                "ledgerHash": ledger_hash,
                "foundation": True
            })

            # Track all the Foundation payouts
            foundation_payouts += foundation_block_total
        else:
            # This was a non foundation address
            # So calculate this the other way
            supercharged_contribution = (
                (supercharged_weighting - 1) * p["timed_weighting"]) + 1
            effective_stake = p["staking_balance"] * supercharged_contribution
            # This the effective percentage of the pool disregarding the Foundation element
            effective_pool_stakes[p["publicKey"]] = effective_stake
            sum_effective_pool_stakes += effective_stake

    # Check here the balances make sense
    assert (foundation_payouts <= total_rewards)

    assert (sum_effective_pool_stakes <= 2 * total_staking_balance)

    # What are the remaining rewards we can share? This should always be higher than if we don't share.
    block_pool_share = total_rewards - (foundation_payouts / (1 - fee))

    # Determine the effective pool weighting based on sum of effective stakes
    for p in payouts:
        if not p["foundation_delegation"]:
            effective_pool_weighting = effective_pool_stakes[
                p["publicKey"]] / sum_effective_pool_stakes

            #This must be less than 1 or we have a major issue
            assert effective_pool_weighting <= 1

            block_total = math.floor(block_pool_share *
                                     effective_pool_weighting * (1 - fee))
            p["total"] += block_total

            other_payouts += block_total

            # Store this data in a structured format for later querying and for the payment script, handled seperately
            store_payout.append({
                "publicKey":
                p["publicKey"],
                "blockHeight":
                b["blockHeight"],
                "stateHash":
                b["stateHash"],
                "totalPoolStakes":
                total_staking_balance,
                "effectivePoolWeighting":
                effective_pool_weighting,
                "effectivePoolStakes":
                effective_pool_stakes[p["publicKey"]],
                "superchargedContribution":
                supercharged_contribution,
                "stakingBalance":
                p["staking_balance"],
                "sumEffectivePoolStakes":
                sum_effective_pool_stakes,
                "superChargedWeighting":
                supercharged_weighting,
                "dateTime":
                b["dateTime"],
                "coinbase":
                int(b["transactions"]["coinbase"]),
                "totalRewards":
                total_rewards,
                "payout":
                block_total,
                "epoch":
                staking_epoch,
                "ledgerHash":
                ledger_hash
            })

    # Final check
    # These are essentially the same but we allow for a tiny bit of nanomina rounding and worst case we never pay more
    assert (foundation_payouts + other_payouts + total_fees <= total_rewards)

# Store the payouts here so we can generate transactions
if store:

    if not os.getenv('MONGO_URI'):
        exit("No Mongo connection string provided")

    try:
        post_id = client.collection.insert_many(store_payout)
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

print("Our fee is " +
      Currency.Currency(all_blocks_total_fees,
                        format=Currency.CurrencyFormat.NANO).decimal_format() +
      " mina")

payout_table = []
payout_json = []

for p in payouts:
    payout_table.append([
        p["publicKey"],
        Currency.Currency(
            p["staking_balance"],
            format=Currency.CurrencyFormat.WHOLE).decimal_format(), p["total"],
        Currency.Currency(
            p["total"], format=Currency.CurrencyFormat.NANO).decimal_format(),
        p["foundation_delegation"]
    ])

    payout_json.append({"publicKey": p["publicKey"], "total": p["total"]})

print(
    tabulate(payout_table,
             headers=[
                 "PublicKey", "Staking Balance", "Payout nanomina",
                 "Payout mina", "Foundation"
             ],
             tablefmt="pretty"))

# This is the payout json we are taking the the next stage to sign. So store this somewhere.
print(payout_json)
