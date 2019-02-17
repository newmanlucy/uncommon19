from web3 import Web3
from solc import compile_files
import json

contracts = compile_files(['bets.sol'])
main_contract = contracts.pop("bets.sol:Betting")

# web3.py instance
w3 = Web3(Web3.HTTPProvider("http://127.0.0.1:8545"))

w3.eth.defaultAccount = w3.eth.accounts[1]


def deploy_contract(contract_interface):
    contract = w3.eth.contract(
        abi=contract_interface['abi'],
        bytecode=contract_interface['bin']
    )

    tx_hash = contract.deploy(
        transaction={'from': w3.eth.accounts[1]}
    )

    tx_receipt = w3.eth.getTransactionReceipt(tx_hash)
    return tx_receipt['contractAddress']

def write_contract(filename):
    with open(filename, 'w') as outfile:
        data = {'abi': main_contract["abi"], "contract_address": deploy_contract(main_contract)}
        json.dump(data, outfile, indent=4, sort_keys=True)

def read_contract(filename):
    with open(filename, 'r') as f:
        datastore = json.load(f)
        abi = datastore['abi']
        contract_address = datastore['contract_address']
        return abi, contract_address

abi, contract_address = read_contract('data.json')

def sol_reward_winner(bet_id, temp):
    abi, contract_address = read_contract('data.json')
    bets = w3.eth.contract(address=contract_address, abi=abi)
    winner = bets.functions.rewardWinner(bet_id, temp).transact()

def sol_create_bet(bet_id, creator_id, atleast, stake):
    abi, contract_address = read_contract('data.json')
    bets = w3.eth.contract(address=contract_address, abi=abi)
    tx_hash = bets.functions.createBet(
        bet_id, creator_id,atleast,stake).transact()
    return tx_hash

def sol_take_bet(bet_id, taker_id):
    abi, contract_address = read_contract('data.json')
    bets = w3.eth.contract(address=contract_address, abi=abi)
    tx_hash = bets.functions.takeBet(bet_id, taker_id).transact()
    return tx_hash

if __name__ == '__main__':
    # compile all contract files
    # # figure out how to get address of person
    write_contract("data.json")