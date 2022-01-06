from scripts.helpful_scripts import get_account, config, network
from brownie import interface

def main():
    get_weth()

def get_weth():
    """
    Mints WETH by depositing ETH.
    """
    # ABI
    # Address

    account = get_account()
    weth = interface.IWeth(config["networks"][network.show_active()]["weth_token"])
    tx = weth.deposit({"from": account, "value": 0.1 * 10 ** 18})
    print(f"Received 0.1 WETH")
    return tx

def withdraw_eth():

    account = get_account()
    wad = 0.1 * 10 ** 18
    weth = interface.IWeth(config["networks"][network.show_active()]["weth_token"])
    tx = weth.withdraw(wad, {"from": account})
    tx.wait(1)
    print(f"Received back 0.1 ETH.")