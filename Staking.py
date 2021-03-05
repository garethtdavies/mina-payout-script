# These functions are not used but indicate how the values retrieved from the API are determined

def timed_weighting(ledger, global_slot_start, slots_per_epoch):
    """Takes in a staking ledger and determines the timed factor for the account"""
    if not ledger["timing"]:
        # Untimed for full epoch so we have the maximum weighting of 1
        return 1
    else:
        # This is timed at the end of the epoch so we always return 0
        if ledger["timing"]["timed_epoch_end"]:
            return 0
        else:
            # This must be timed for only a portion of the epoch
            timed_end = ledger["timing"]["untimed_slot"]
            global_slot_end = global_slot_start + slots_per_epoch

            return ((global_slot_end - timed_end) / slots_per_epoch)


def calculate_end_slot_timed_balance(timing):

    if timing["vesting_period"] == 0 or timing["vesting_increment"] == 0:
        # Then everything vests at once and just cliff time?
        vested_height_global_slot = int(timing["cliff_time"])
    else:
        vested_height_global_slot = int(timing["cliff_time"]) + (
            (int(timing["initial_minimum_balance"]) -
             int(timing["cliff_amount"])) /
            int(timing["vesting_increment"])) * int(timing["vesting_period"])

    return int(vested_height_global_slot)