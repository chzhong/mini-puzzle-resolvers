import matplotlib.pyplot as plt
import numpy as np

# ================= 配置中文字体 =================
# 防止 matplotlib 显示中文时出现方块乱码
plt.rcParams["font.sans-serif"] = [
    "SimHei",
    "PingFang SC",
    "Microsoft YaHei",
    "Arial Unicode MS",
]
plt.rcParams["axes.unicode_minus"] = False


# ================= 游戏1：抛硬币模拟 =================
def simulate_coin_toss(balance=100, bet=10, p_head=0.5, rounds=10000, num_players=10):
    """
    模拟抛硬币游戏
    """
    # 初始化玩家资金和记录数组
    balances = np.full(num_players, balance, dtype=float)
    history = np.zeros((rounds + 1, num_players))
    history[0] = balances

    initial_total = balance * num_players

    for r in range(1, rounds + 1):
        # 判断哪些玩家还有足够资金继续游戏
        active = balances >= bet

        if not np.any(active):
            # 如果所有人都破产，提前结束
            history[r:] = balances
            break

        # 生成抛硬币结果 (True 为 head, False 为 tail)
        results = np.random.rand(num_players) < p_head

        # 更新资金
        # 赢 (head): 获得 2*bet，即净赚 bet
        win_mask = active & results
        balances[win_mask] += bet

        # 输 (tail): 获得 0，即净亏 bet
        lose_mask = active & ~results
        balances[lose_mask] -= bet

        history[r] = balances

    # 计算庄家净资金 (玩家总亏损 = 初始总资金 - 当前总资金)
    dealer_history = initial_total - np.sum(history, axis=1)

    return history, dealer_history


# ================= 游戏2：轮盘模拟 =================
def simulate_roulette(p_zero=1 / 49, bet=10, rounds=10000, initial_balance=10000):
    """
    模拟 0-48 轮盘游戏
    """
    # 1. 定义所有可能的压法 (投注选项) 及其赔率 (净收益倍数)
    options = []
    payouts = []
    winning_numbers = []  # 每个选项对应的中奖数字列表

    numbers = np.arange(49)

    # 外部投注 (Even Money) - 赔率 1:1，中0庄家赢
    even_money_bets = {
        "红": [x for x in numbers if x % 2 != 0 and x != 0],
        "黑": [x for x in numbers if x % 2 == 0 and x != 0],
        "单": [x for x in numbers if x % 2 != 0 and x != 0],
        "双": [x for x in numbers if x % 2 == 0 and x != 0],
        "小(1-24)": list(range(1, 25)),
        "大(25-48)": list(range(25, 49)),
    }
    for name, nums in even_money_bets.items():
        options.append(name)
        payouts.append(1)
        winning_numbers.append(nums)

    # 打注 (Dozens) - 赔率 2:1，中0庄家赢
    dozens_bets = {
        "打1(1-16)": list(range(1, 17)),
        "打2(17-32)": list(range(17, 33)),
        "打3(33-48)": list(range(33, 49)),
    }
    for name, nums in dozens_bets.items():
        options.append(name)
        payouts.append(2)
        winning_numbers.append(nums)

    # 列注 (Columns) - 赔率 2:1，中0庄家赢
    columns_bets = {
        "列1": [x for x in numbers if x % 3 == 1],
        "列2": [x for x in numbers if x % 3 == 2],
        "列3": [x for x in numbers if x % 3 == 0 and x != 0],
    }
    for name, nums in columns_bets.items():
        options.append(name)
        payouts.append(2)
        winning_numbers.append(nums)

    # 直注 (Straight Up) - 赔率 48:1
    for i in range(49):
        options.append(f"直注-{i}")
        payouts.append(48)
        winning_numbers.append([i])

    num_players = len(options)
    payouts = np.array(payouts)

    # 2. 构建中奖矩阵 (num_players x 49)
    win_matrix = np.zeros((num_players, 49), dtype=bool)
    for i, nums in enumerate(winning_numbers):
        win_matrix[i, nums] = True

    # 3. 初始化资金
    balances = np.full(num_players, initial_balance, dtype=float)
    history = np.zeros((rounds + 1, num_players))
    history[0] = balances
    initial_total = initial_balance * num_players

    # 4. 生成轮盘概率分布
    probs = np.full(49, (1 - p_zero) / 48)
    probs[0] = p_zero

    # 5. 开始模拟
    for r in range(1, rounds + 1):
        active = balances >= bet
        if not np.any(active):
            history[r:] = balances
            break

        # 生成开奖数字
        result_num = np.random.choice(49, p=probs)

        # 判断中奖情况
        wins = win_matrix[:, result_num]

        # 更新资金
        win_mask = active & wins
        lose_mask = active & ~wins

        balances[win_mask] += bet * payouts[win_mask]
        balances[lose_mask] -= bet

        history[r] = balances

    dealer_history = initial_total - np.sum(history, axis=1)

    return history, dealer_history, options, payouts


# ================= 绘图函数 =================
def plot_coin_toss(history, dealer_history):
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))

    # 图1：10个赌徒资金变化
    for i in range(history.shape[1]):
        ax1.plot(history[:, i], label=f"玩家 {i + 1}", alpha=0.8)
    ax1.axhline(y=100, color="r", linestyle="--", label="初始资金 (100)")
    ax1.set_title("抛硬币游戏：10位赌徒资金变化曲线")
    ax1.set_xlabel("模拟轮次")
    ax1.set_ylabel("资金")
    ax1.legend(loc="upper right", ncol=2)
    ax1.grid(True, alpha=0.3)

    # 图2：庄家净资金变化
    ax2.plot(dealer_history, color="green", linewidth=2, label="庄家净资金")
    ax2.axhline(y=0, color="r", linestyle="--", label="初始资金 (0)")
    ax2.set_title("抛硬币游戏：庄家净资金变化曲线")
    ax2.set_xlabel("模拟轮次")
    ax2.set_ylabel("庄家净资金")
    ax2.legend()
    ax2.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.show()


def plot_roulette(history, dealer_history, options, payouts):
    fig, axs = plt.subplots(4, 1, figsize=(14, 16))

    # 分类索引
    even_money_idx = list(range(6))
    dozens_cols_idx = list(range(6, 12))
    straight_idx = list(range(12, 61))

    # 图1：外部投注 (Even Money)
    for i in even_money_idx:
        axs[0].plot(history[:, i], label=options[i], linewidth=1.5)
    axs[0].set_title("轮盘游戏：外部投注 (1:1) 资金变化")
    axs[0].set_ylabel("资金")
    axs[0].legend(loc="upper right")
    axs[0].grid(True, alpha=0.3)

    # 图2：打和列 (Dozens & Columns)
    for i in dozens_cols_idx:
        axs[1].plot(history[:, i], label=options[i], linewidth=1.5)
    axs[1].set_title("轮盘游戏：打注与列注 (2:1) 资金变化")
    axs[1].set_ylabel("资金")
    axs[1].legend(loc="upper right")
    axs[1].grid(True, alpha=0.3)

    # 图3：直注 (Straight Up) - 因为数量多，使用半透明细线
    for i in straight_idx:
        axs[2].plot(history[:, i], color="blue", alpha=0.3, linewidth=0.5)
    # 高亮显示几个代表性的直注 (0, 1, 24, 48)
    for highlight in [12, 13, 36, 60]:  # 对应直注-0, 直注-1, 直注-24, 直注-48
        axs[2].plot(
            history[:, highlight], color="red", linewidth=1.5, label=options[highlight]
        )
    axs[2].set_title("轮盘游戏：直注 (48:1) 资金变化 (共49种，红线为代表)")
    axs[2].set_ylabel("资金")
    axs[2].legend(loc="upper right")
    axs[2].grid(True, alpha=0.3)

    # 图4：庄家净资金
    axs[3].plot(dealer_history, color="darkgreen", linewidth=2, label="庄家净资金")
    axs[3].set_title("轮盘游戏：庄家总净资金变化")
    axs[3].set_xlabel("模拟轮次")
    axs[3].set_ylabel("庄家净资金")
    axs[3].legend()
    axs[3].grid(True, alpha=0.3)

    plt.tight_layout()
    plt.show()


# ================= 主程序 =================
if __name__ == "__main__":
    print("开始模拟抛硬币游戏...")
    # 游戏1参数
    coin_balance = 100
    coin_bet = 10
    coin_p_head = 0.5
    coin_rounds = 10000
    coin_num_players = 10

    coin_history, coin_dealer = simulate_coin_toss(
        balance=coin_balance,
        bet=coin_bet,
        p_head=coin_p_head,
        rounds=coin_rounds,
        num_players=coin_num_players,
    )
    plot_coin_toss(coin_history, coin_dealer)

    print("开始模拟轮盘游戏...")
    # 游戏2参数
    roulette_p_zero = 1 / 49
    roulette_bet = 10
    roulette_rounds = 10000
    roulette_initial_balance = 10000  # 直注波动大，给足初始资金

    roulette_history, roulette_dealer, roulette_options, roulette_payouts = (
        simulate_roulette(
            p_zero=roulette_p_zero,
            bet=roulette_bet,
            rounds=roulette_rounds,
            initial_balance=roulette_initial_balance,
        )
    )
    plot_roulette(roulette_history, roulette_dealer, roulette_options, roulette_payouts)

    print("模拟完成！")
