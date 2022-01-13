from brownie import config, network, interface
from scripts.helpful_scripts import get_account
from scripts.get_weth import get_weth
from web3 import Web3

# 0.1
amount = Web3.toWei(0.1, "ether")

def main():
    print(f"Current active network is: {network.show_active()}\n")
    account = get_account()
    erc20_address = config["networks"][network.show_active()]["weth_token"]
    # get_weth()
    if network.show_active() in ["mainnet-fork"]:
        get_weth()

    # ABI
    # Address
    lending_pool = get_lending_pool()
    print("Found AAVE lendingpool!\n")
    
    # approve ERC20
    approve_erc20(amount, lending_pool.address, erc20_address, account)
    print("Depositing 0.1 ETH...\n")
    tx = lending_pool.deposit(erc20_address, amount, account.address, 0, {"from": account})
    tx.wait(1)
    print("Deposited 0.1 ETH!\n")
    borrowable_eth, total_debt = get_borrowable_data(lending_pool, account)
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
    print("Now repaying the debt...\n")
    repay_all(amount, lending_pool, account)
    print(f"Repaid all DAI!\n")

    print("This is current status...\n")
    get_borrowable_data(lending_pool, account)

    #print("Now withdrawing WETH back...\n")
    #withdraw_amount = Web3.toWei(0.00001, "ether")
    #withdraw_some(lending_pool, withdraw_amount, account)
    print("All finished, bye!\n")

def withdraw_some(lending_pool, withdraw_amount, account):
    # no need to approve_erc20 since you're the spender

    withdraw_tx = lending_pool.withdraw(
        config["networks"][network.show_active()]["weth_token"],
        withdraw_amount,
        account.address,
        {"from": account}
    )
    withdraw_tx.wait(1)
    withdraw_amount_in_eth = Web3.fromWei(withdraw_amount, "ether")
    print(f"Done withdrawing {withdraw_amount} Wei, which is {withdraw_amount_in_eth} ETH.")

def repay_all(amount, lending_pool, account):
    approve_erc20(
        Web3.toWei(amount, "ether"),
        lending_pool,
        config["networks"][network.show_active()]["dai_token"],
        account,
    )
    repay_tx = lending_pool.repay(
        config["networks"][network.show_active()]["dai_token"],
        amount,
        1,
        account.address,
        {"from": account},
    )
    repay_tx.wait(1)

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
    print(f"You can borrow {available_borrow_eth} worth of ETH.")
    return (float(available_borrow_eth), float(total_debt_eth))

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
