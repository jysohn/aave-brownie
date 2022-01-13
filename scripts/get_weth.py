from scripts.helpful_scripts import get_account, config, network
from brownie import interface

def main():
    account = get_account()
    #get_weth(account, 0.01)
    withdraw_eth(account, 0.35)

def get_weth(account, amount):
    """
    Mints WETH by depositing ETH.
    """
    # ABI
    # Address
    weth = interface.IWeth(config["networks"][network.show_active()]["weth_token"])
    tx = weth.deposit({"from": account, "value": amount * 10 ** 18})
    tx.wait(1)
    print(f"Received {amount} WETH.\n")
    return tx

def withdraw_eth(account, amount):
    """
    Mints ETH by depositing back WETH.
    """
    wad = amount * 10 ** 18
    weth = interface.IWeth(config["networks"][network.show_active()]["weth_token"])
    tx = weth.withdraw(wad, {"from": account})
    tx.wait(1)
    print(f"Received back {amount} ETH.\n")