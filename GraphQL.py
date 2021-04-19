import requests


def _graphql_request(query: str, variables: dict = {}):
    """GraphQL queries all look alike, this is a generic function to facilitate a GraphQL Request.

    Arguments:
        query {str} -- A GraphQL Query

    Keyword Arguments:
        variables {dict} -- Optional Variables for the GraphQL Query (default: {{}})

    Raises:
        Exception: Raises an exception if the response is anything other than 200.
    
    Returns:
        dict -- Returns the JSON Response as a Dict.
    """
    # Strip all the whitespace and replace with spaces
    query = " ".join(query.split())
    payload = {'query': query}
    if variables:
        payload = {**payload, 'variables': variables}

    headers = {"Accept": "application/json"}
    response = requests.post("https://graphql.minaexplorer.com",
                             json=payload,
                             headers=headers)
    resp_json = response.json()
    if response.status_code == 200 and "errors" not in resp_json:
        return resp_json
    else:
        print(response.text)
        raise Exception("Query failed -- returned code {}. {}".format(
            response.status_code, query))


def getStakingLedger(variables):
    """Return the staking ledger."""
    query = '''query($delegate: String!, $ledgerHash: String!){
  stakes(query: {delegate: $delegate, ledgerHash: $ledgerHash}, limit: 1000) {
    public_key
    balance
    chainId
    timing {
      cliff_amount
      cliff_time
      initial_minimum_balance
      timed_epoch_end
      timed_in_epoch
      timed_weighting
      untimed_slot
      vesting_increment
      vesting_period
    }
  }
}
'''

    return _graphql_request(query, variables)


def getBlocks(variables):
    """Returns all blocks the pool won."""
    query = """query($creator: String!, $epoch: Int, $blockHeightMin: Int, $blockHeightMax: Int, $dateTimeMin: DateTime, $dateTimeMax: DateTime){
  blocks(query: {creator: $creator, protocolState: {consensusState: {epoch: $epoch}}, canonical: true, blockHeight_gte: $blockHeightMin, blockHeight_lte: $blockHeightMax, dateTime_gte:$dateTimeMin, dateTime_lte:$dateTimeMax, transactions: {userCommands: {from_ne: $creator}}, snarkJobs: {prover_ne: $creator}}, sortBy: DATETIME_DESC) {
    blockHeight
    canonical
    creator
    dateTime
    txFees
    snarkFees
    receivedTime
    stateHash
    stateHashField
    protocolState {
      consensusState {
        blockHeight
        epoch
        slotSinceGenesis
      }
    }
    transactions {
      coinbase
      coinbaseReceiverAccount {
        publicKey
      }
      feeTransfer {
        fee
        recipient
        type
      }
    }
  }
}
"""
    return _graphql_request(query, variables)


def getLedgerHash(epoch: int) -> dict:
    query = """query ($epoch: Int) {
  blocks(query: {canonical: true, protocolState: {consensusState: {epoch: $epoch}}}, limit: 1) {
    protocolState {
      consensusState {
        stakingEpochData {
          ledger {
            hash
          }
        }
        epoch
      }
    }
  }
}"""
    variables = {
        "epoch": epoch
    }
    return _graphql_request(query, variables)


def getLatestHeight():
    query = """{
  blocks(query: {canonical: true}, sortBy: DATETIME_DESC, limit: 1) {
    blockHeight
  }
}"""
    return _graphql_request(query)
