from web3 import Web3
from web3.middleware import ExtraDataToPOAMiddleware  # Necessary for POA chains
import json

def connect_to(chain):
    if chain == 'source':  # Avalanche Fuji
        api_url = "https://api.avax-test.network/ext/bc/C/rpc"
    elif chain == 'destination':  # BSC Testnet
        api_url = "https://data-seed-prebsc-1-s1.binance.org:8545/"
    else:
        raise ValueError(f"Invalid chain: {chain}")

    w3 = Web3(Web3.HTTPProvider(api_url))
    w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)
    return w3

def get_contract_info(chain, contract_info):
    with open(contract_info, 'r') as f:
        contracts = json.load(f)
    return contracts[chain]

def scan_blocks(chain, contract_info="contract_info.json"):
    if chain not in ['source', 'destination']:
        print(f"Invalid chain: {chain}")
        return

    w3 = connect_to(chain)
    current_block = w3.eth.get_block_number()
    start_block = max(0, current_block - 5)
    end_block = current_block

    info = get_contract_info(chain, contract_info)
    contract_address = Web3.to_checksum_address(info["address"])
    abi = info["abi"]

    contract = w3.eth.contract(address=contract_address, abi=abi)

    if chain == 'source':
        event = contract.events.Deposit
    else:
        event = contract.events.Unwrap

    try:
        logs = event.create_filter(fromBlock=start_block, toBlock=end_block).get_all_entries()
    except Exception as e:
        print(f"Error scanning {chain} logs: {e}")
        return

    for evt in logs:
        if chain == 'source':
            token = evt.args['token']
            recipient = evt.args['recipient']
            amount = evt.args['amount']

            print(f"Forwarding to wrap on destination: {token}, {recipient}, {amount}")
            destination = connect_to('destination')
            dest_info = get_contract_info('destination', contract_info)
            dest_contract = destination.eth.contract(
                address=Web3.to_checksum_address(dest_info["address"]),
                abi=dest_info["abi"]
            )

            warden_pk = get_contract_info("warden", contract_info)["private_key"]
            acct = destination.eth.account.from_key(warden_pk)

            tx = dest_contract.functions.wrap(token, recipient, amount).build_transaction({
                'from': acct.address,
                'nonce': destination.eth.get_transaction_count(acct.address),
                'gas': 800000,
                'gasPrice': destination.eth.gas_price,
                'chainId': destination.eth.chain_id
            })
            signed = acct.sign_transaction(tx)
            tx_hash = destination.eth.send_raw_transaction(signed.rawTransaction)
            print("Wrap tx hash:", tx_hash.hex())

        elif chain == 'destination':
            underlying_token = evt.args['underlying_token']
            recipient = evt.args['to']
            amount = evt.args['amount']

            print(f"Forwarding to withdraw on source: {underlying_token}, {recipient}, {amount}")
            source = connect_to('source')
            src_info = get_contract_info('source', contract_info)
            src_contract = source.eth.contract(
                address=Web3.to_checksum_address(src_info["address"]),
                abi=src_info["abi"]
            )

            warden_pk = get_contract_info("warden", contract_info)["private_key"]
            acct = source.eth.account.from_key(warden_pk)

            tx = src_contract.functions.withdraw(underlying_token, recipient, amount).build_transaction({
                'from': acct.address,
                'nonce': source.eth.get_transaction_count(acct.address),
                'gas': 800000,
                'gasPrice': source.eth.gas_price,
                'chainId': source.eth.chain_id
            })
            signed = acct.sign_transaction(tx)
            tx_hash = source.eth.send_raw_transaction(signed.rawTransaction)
            print("Withdraw tx hash:", tx_hash.hex())


