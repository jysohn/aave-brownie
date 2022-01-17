from brownie import config, network, interface
from scripts.helpful_scripts import get_account
from scripts.get_weth import get_weth, withdraw_eth
from decimal import Decimal
from web3 import Web3

unit = 0.01
amount = Web3.toWei(unit, "ether")

def main():
    print(f"Current active network is: {network.show_active()}\n")
    account = get_account()
    print(f"Current account get: {account.address}")
    erc20_address = config["networks"][network.show_active()]["weth_token"]
    
    # get_weth()
    get_weth(account, unit)

    # ABI
    # Address
    lending_pool = get_lending_pool()
    print("Found AAVE lending pool!\n")
    print("Checking if the lending pool is paused...\n")
    if (lending_pool.paused()):
        print("Lending pool is paused; exiting now.")
        exit()
    print("Lending pool is live, carrying on...\n")

    print("Initial borrow data...\n")
    get_borrowable_data(lending_pool, account)
    
    # approve ERC20
    approve_erc20(amount, lending_pool.address, erc20_address, account)
    print("Depositing 0.01 ETH...\n")
    tx = lending_pool.deposit(erc20_address, amount, account.address, 0, {"from": account})
    tx.wait(1)
    print("Deposited 0.01 ETH!\n")
    borrowable_eth, total_debt, total_collateral_eth = get_borrowable_data(lending_pool, account)
    # find amount to borrow, at 5% to max
    print("Fetching DAI/ETH price...\n")
    dai_eth_price = get_asset_data(config["networks"][network.show_active()]["dai_eth_pair"])
    print(f"Current DAI/ETH price is {dai_eth_price}.\n")
    amount_to_borrow = (1/dai_eth_price) * borrowable_eth * 0.50
    print(f"Now borrowing 50% of max allowed, {amount_to_borrow} DAI...\n")

    dai_token = config["networks"][network.show_active()]["dai_token"]
    borrow_tx = lending_pool.borrow(
        dai_token, 
        Web3.toWei(amount_to_borrow, "ether"),
        1,
        0,
        account.address,
        {"from": account},
        )
    borrow_tx.wait(1)
    print(f"Borrowed {amount_to_borrow} DAI!\n")

    #Update new lending data
    borrowable_eth, total_debt, total_collateral_eth = get_borrowable_data(lending_pool, account)
    dai_eth_price = get_asset_data(config["networks"][network.show_active()]["dai_eth_pair"])
    total_debt_in_dai = (1/dai_eth_price) * total_debt
    
    print("Now repaying the debt...\n")

    #Choose to repay all or repay a certain amount
    #repay_amount(amount_to_borrow, lending_pool, account)
    repay_all(total_debt_in_dai, lending_pool, account)


    print(f"Repaid all DAI!\n")

    print("This is current status...\n")
    borrowable_eth, total_debt, total_collateral_eth = get_borrowable_data(lending_pool, account)

    print("Now withdrawing WETH back...\n")
    withdraw_all(lending_pool, total_collateral_eth, account)
    print(f"Done withdrawing all deposited WETH...\n")

    print("This is final status...\n")
    get_borrowable_data(lending_pool, account)

    print("Finishing up by converting 0.01 WETH back to ETH...")
    withdraw_eth(account, unit)

    print("All finished, bye!\n")

def withdraw_all(lending_pool, withdraw_amount, account):
    # no need to approve_erc20 since you're the spender

    withdraw_tx = lending_pool.withdraw(
        config["networks"][network.show_active()]["weth_token"],
        #Web3.toWei(Decimal(str(withdraw_amount)), "ether"),
        Web3.toWei(0.001, "ether"),
        account.address,
        {"from": account}
    )
    withdraw_tx.wait(1)

def repay_amount(amount, lending_pool, account):
    approve_erc20(
        Web3.toWei(amount, "ether"),
        lending_pool.address,
        config["networks"][network.show_active()]["dai_token"],
        account,
    )
    repay_tx = lending_pool.repay(
        config["networks"][network.show_active()]["dai_token"],
        Web3.toWei(amount, "ether"),
        1,
        account.address,
        {"from": account},
    )
    repay_tx.wait(1)
    print(f"Repaid partial debt amount: {amount}")

def repay_all(amount, lending_pool, account):
    approve_erc20(
        Web3.toWei(amount, "ether"),
        lending_pool.address,
        config["networks"][network.show_active()]["dai_token"],
        account,
    )
    repay_tx = lending_pool.repay(
        config["networks"][network.show_active()]["dai_token"],
        Web3.toWei(amount, "ether"),
        1,
        account.address,
        {"from": account},
    )
    repay_tx.wait(1)
    print("Done repaying all debt!\n")

def get_asset_data(price_feed_address):
    dai_eth_price_feed = interface.AggregatorV3Interface(price_feed_address)
    latest_price = dai_eth_price_feed.latestRoundData()[1]
    converted_latest_price = Web3.fromWei(latest_price, "ether")
    return float(converted_latest_price)

def get_borrowable_data(lending_pool, account):
    (total_collateral_eth, 
    total_debt_eth, 
    available_borrow_eth, 
    current_liquidation_threshold, 
    ltv, 
    health_factor) = lending_pool.getUserAccountData(account.address)

    available_borrow_eth = Web3.fromWei(available_borrow_eth, "ether")
    total_debt_eth = Web3.fromWei(total_debt_eth, "ether")
    total_collateral_eth = Web3.fromWei(total_collateral_eth, "ether")

    print(f"You have {total_collateral_eth} worth of ETH deposited.")
    print(f"You have {total_debt_eth} worth of ETH borrowed.")
    print(f"You can borrow {available_borrow_eth} worth of ETH.\n")
    return (float(available_borrow_eth), float(total_debt_eth), float(total_collateral_eth))

def approve_erc20(amount, spender, erc20_address, account):
    # ABI
    # Address
    print("Approving ERC20 token...\n")
    erc20 = interface.IERC20(erc20_address)
    tx = erc20.approve(spender, amount, {"from": account})
    tx.wait(1)
    print("Approved!\n")
    return tx

def get_lending_pool():
    # ABI - comes from interface
    # Address - can find in docs
    lending_pool_addresses_provider = interface.ILendingPoolAddressesProvider(
        config["networks"][network.show_active()]["lending_pool_addresses_provider"]
    )
    lending_pool_address = lending_pool_addresses_provider.getLendingPool()
    lending_pool = interface.ILendingPool(
        lending_pool_address
    )
    return lending_pool
