from web3 import Web3
from abi import uniswapabi_v3, weth_abi, factory_abi, sellAbi
from web3.middleware import geth_poa_middleware
import requests

#Goerli
node_url = "https://goerli.infura.io/v3/6d8840e461f042bd9336386934959ca1"
price_url = "https://api.etherscan.io/api?module=proxy&action=eth_gasPrice&apikey=6EH8TRA3CSJAD6P2N1FIZ5VBC4NT8II935"
weth = "0xB4FBF271143F4FBf7B91A5ded31805e42b2208d6"
web3 = Web3(Web3.HTTPProvider(node_url))

#mumbai
# price_url="https://api-testnet.polygonscan.com/api?module=proxy&action=eth_gasPrice&apikey=UBX1M7KF12INF2QPHUEUDNS2W2M5CRFB29"
# node_url="https://polygon-mumbai.infura.io/v3/6d8840e461f042bd9336386934959ca1"
# weth="0x9c3C9283D3e44854697Cd22D3Faa240Cfb032889" 
# web3 = Web3(Web3.HTTPProvider(node_url))
# web3.middleware_onion.inject(geth_poa_middleware, layer=0)

#OP
# node_url = "https://optimism-mainnet.infura.io/v3/6d8840e461f042bd9336386934959ca1"
# price_url = "https://api-optimistic.etherscan.io/api?module=proxy&action=eth_gasPrice&apikey=PTGTTND83AXNXGS85CYSTA552CHNJ2TABX"
# weth = "0x4200000000000000000000000000000000000006"
# web3 = Web3(Web3.HTTPProvider(node_url))

#Base
# node_url = "https://base-mainnet.g.alchemy.com/v2/h9Gm149OCB8B4Zw5nKOxhhnKEdzUhynp"
# price_url = "https://api.basescan.org/api?module=proxy&action=eth_gasPrice&apikey=KY46C1ERYQ78VJRB127D3QVX22ZA88MQ3I"
# weth = "0x4200000000000000000000000000000000000006"
# web3 = Web3(Web3.HTTPProvider(node_url))

uniswap_router_address = '0x68b3465833fb72A70ecDF485E0e4C7bD8665Fc45' 
# uniswap_router_address = "0xE592427A0AEce92De3Edee1F18E0157C05861564"
factory_address = "0x1F98431c8aD98523631AE4a59f267346ea31F984"

uniswap_router = web3.eth.contract(address=uniswap_router_address, abi=uniswapabi_v3)
weth_contract = web3.eth.contract(address = weth, abi = weth_abi)

def isConnected():
    if web3.is_connected():
        print("Connection Successful")
        return True
    else:
        print("Connection Failed")
        return False

def feeAmount():
    fee = {
    "LOWEST":100,
    "LOW" :500,
    "MEDIUM" :3000,
    "HIGH" : 10000
    }
    return fee

def checkPair(token1, token2, fee):
    factory_contract = web3.eth.contract(address = factory_address, abi = factory_abi)
    pair_address = factory_contract.functions.getPool(token1, token2, fee).call()
    if pair_address != "0x0000000000000000000000000000000000000000":
        return True
    else:
        return False

def send_transaction(txn, private_key):
    signed_txn = web3.eth.account.sign_transaction(txn, private_key)
    raw_tx = web3.eth.send_raw_transaction(signed_txn.rawTransaction)
    txHash = str(web3.to_hex(raw_tx))
    tx_receipt = web3.eth.wait_for_transaction_receipt(txHash, timeout=10000000)
    if tx_receipt.status == 1:
        return txHash

def wethCheckApproval(public_key, private_key,  amount):
    check_allowance = weth_contract.functions.allowance(web3.to_checksum_address(public_key), uniswap_router_address).call()
    approve_max = 115792089237316195423570985008687907853269984665640564039457584007913129639935
    if(check_allowance < web3.to_wei(amount, 'ether')):
        print("In approval")
        price = getPrice()
        approve_tx = weth_contract.functions.approve(web3.to_checksum_address(uniswap_router_address), approve_max).build_transaction({
            'from': web3.to_checksum_address(public_key),
            'gas': 0,
            'gasPrice': price,
            'nonce': web3.eth.get_transaction_count(public_key),
            'value': 0
        })

        gas = web3.eth.estimate_gas(approve_tx)
        approve_tx.update({'gas': gas * 2})

        approve_tx_hash = send_transaction(approve_tx, private_key)
        print(approve_tx_hash)
    else:
        print("Have allowance")
        pass

def checkWethBalance(public_key, private_key, amount):
    weth_balance = weth_contract.functions.balanceOf(public_key).call();
    print("weth_balance", weth_balance)

    if (weth_balance < web3.to_wei(amount, 'ether')):
        print("converting to weth")
        price = getPrice()
        print(price)
        wrap_txn = weth_contract.functions.deposit().build_transaction({
            'from': web3.to_checksum_address(public_key),
            'gas': 0,
            'gasPrice': price ,
            'nonce': web3.eth.get_transaction_count(public_key),
            'value': web3.to_wei(amount, 'ether')
        })
        gas = web3.eth.estimate_gas(wrap_txn)
        wrap_txn.update({'gas': gas * 2})
        print(wrap_txn)
        wrap_tx_hash = send_transaction(wrap_txn, private_key)
        print(wrap_tx_hash)
    else: 
        pass

def getPrice():
    response = requests.get(price_url)
    # print("response", response)
    if response.status_code == 200:
         price_res = response.json()
        #  print("price_res",price_res)
         value = int(int(price_res['result'], 16)/ 10 ** 9)
        #  print("value", value)
         price = web3.to_wei(value, 'gwei')
         return price
    else:
        price = web3.to_wei('20', 'gwei')
        return price

def checkTokenBalance(token_address, public_key, amount):
   token_contract = web3.eth.contract(address=token_address, abi = sellAbi)
   balance = token_contract.functions.balanceOf(web3.to_checksum_address(public_key)).call()
   decimals = token_contract.functions.decimals().call()
   if balance > amount * 10 ** decimals:
       return True, decimals,
   else:
       return False

def getSymbol(token_address):
     token_contract = web3.eth.contract(address=token_address, abi = sellAbi)
     symbol = token_contract.functions.symbol().call()
     return symbol

def tokenCheckApproval(token_address, public_key, private_key, amount):
    token_contract = web3.eth.contract(address=token_address, abi = sellAbi)
    decimals = token_contract.functions.decimals().call()
    check_allowance = token_contract.functions.allowance(web3.to_checksum_address(public_key), uniswap_router_address).call()
    print("allowance", check_allowance)
    approve_max = 115792089237316195423570985008687907853269984665640564039457584007913129639935
    if(check_allowance < amount * 10 ** decimals):
        print("In approval")
        price = getPrice()
        approve_tx = token_contract.functions.approve(web3.to_checksum_address(uniswap_router_address), approve_max).build_transaction({
            'from': web3.to_checksum_address(public_key),
            'gas': 0,
            'gasPrice': price,
            'nonce': web3.eth.get_transaction_count(public_key),
            'value': 0
        })

        gas = web3.eth.estimate_gas(approve_tx)
        approve_tx.update({'gas': gas * 2})

        approve_tx_hash = send_transaction(approve_tx, private_key)
        print(approve_tx_hash)
    else:
        print("Have allowance")
        pass

def singleBuySwap(token_address, amount, fee,  public_key, private_key):
    connected = isConnected()
    if connected:
        pair_exist = checkPair(web3.to_checksum_address(weth), web3.to_checksum_address(token_address), fee);
        if pair_exist:
            checkWethBalance(public_key, private_key, amount)
            wethCheckApproval(public_key, private_key, amount)
            print("Swapping token to Buy")
            price = getPrice()
            print(price);
            swap_txn = uniswap_router.functions.exactInputSingle({
                'tokenIn': web3.to_checksum_address(weth),
                'tokenOut': web3.to_checksum_address(token_address),
                'fee': fee,
                'recipient': web3.to_checksum_address(public_key),
                'deadline': web3.eth.get_block('latest')['timestamp'] + 60 * 10,
                'amountIn': web3.to_wei(amount, 'ether'),
                'amountOutMinimum': 0,
                'sqrtPriceLimitX96': 0
            }).build_transaction({
                'from': web3.to_checksum_address(public_key),
                'gas': 250000,
                'gasPrice': price,
                'nonce': web3.eth.get_transaction_count(public_key),
                'value': 0
            })
            # gas = web3.eth.estimate_gas(swap_txn)
            # swap_txn.update({'gas': gas * 2})
            swap_tx_hash = send_transaction(swap_txn, private_key)
            print(swap_tx_hash)
        else:
            print("Cannot swap pair doesn't exist")
            return f"Cannot swap pair doesn't exist"
    else:
        print("Not connected")
        return f"Not connected"

def singleSellSwap(token_address, amount, fee, public_key, private_key):
    connected = isConnected()
    if connected:
        pair_exist = checkPair(web3.to_checksum_address(weth), web3.to_checksum_address(token_address), fee);
        if pair_exist:
            have_balance, decimals, token_symbol = checkTokenBalance(token_address, public_key, amount)
            if have_balance:
                tokenCheckApproval(token_address, public_key, private_key, amount)
                print("Swapping token to Sell")
                price = getPrice()
                swap_txn = uniswap_router.functions.exactInputSingle({
                    'tokenIn': web3.to_checksum_address(token_address),
                    'tokenOut':  web3.to_checksum_address(weth),
                    'fee': fee,
                    'recipient': web3.to_checksum_address(public_key),
                    'deadline': web3.eth.get_block('latest')['timestamp'] + 60 * 10,
                    'amountIn': int(amount * 10 ** decimals),
                    'amountOutMinimum': 0,
                    'sqrtPriceLimitX96': 0
                }).build_transaction({
                    'from': web3.to_checksum_address(public_key),
                    'gas': 250000,
                    'gasPrice': price,
                    'nonce': web3.eth.get_transaction_count(public_key),
                    'value': 0
                })
                swap_tx_hash = send_transaction(swap_txn, private_key)
                print(swap_tx_hash)
            else:
                print("You do not have enough balance")
                return "You do not have enough balance"
        else:
            print("Cannot swap pair doesn't exist")
            return f"Cannot swap pair doesn't exist"
    else:
        print("Not connected")
        return f"Not connected"

#USDC: 0x07865c6E87B9F70255377e024ace6630C1Eaa37F
#UNI: 0x1f9840a85d5aF5bf1D1762F925BDADdC4201F984

#goerli
singleBuySwap("0x07865c6E87B9F70255377e024ace6630C1Eaa37F", 0.001, 10000, "0xE53cb30b74ff99BC3A5e0A2b3eAE8Ffa1fAcda9a", "0x7e7e03897a8fe14f157d12e286123350b57e9f16f0e95941c52ddc8f69c95174")
# singleSellSwap("0x07865c6E87B9F70255377e024ace6630C1Eaa37F", 10000, 10000, "0xE53cb30b74ff99BC3A5e0A2b3eAE8Ffa1fAcda9a", "0x7e7e03897a8fe14f157d12e286123350b57e9f16f0e95941c52ddc8f69c95174")

#mumbai
# singleBuySwap("0x1f9840a85d5aF5bf1D1762F925BDADdC4201F984", 0.0001, 10000, "0xF7003c136E11F8492733541466a35154b522f000", "0x077310428daa583e0aeec339d36f847770edb685376811a38c3029d8957e7c6c")
# singleSellSwap("0x0FA8781a83E46826621b3BC094Ea2A0212e71B23", 100, 10000, "0xE53cb30b74ff99BC3A5e0A2b3eAE8Ffa1fAcda9a", "0x7e7e03897a8fe14f157d12e286123350b57e9f16f0e95941c52ddc8f69c95174")
