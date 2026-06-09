# Deriv Smart Trading Gateway - 详细技术文档

**版本**: 1.0.0  
**最后更新**: 2026年6月9日  
**语言**: Python 3.11+

---

## 目录

1. [项目概述](#项目概述)
2. [系统架构](#系统架构)
3. [快速开始](#快速开始)
4. [依赖要求](#依赖要求)
5. [核心模块详解](#核心模块详解)
6. [UI界面完全指南](#ui界面完全指南)
7. [多智能体系统](#多智能体系统)
8. [MCP服务器](#mcp服务器)
9. [微交易策略引擎](#微交易策略引擎)
10. [纸面交易与回测](#纸面交易与回测)
11. [预算与安全防护](#预算与安全防护)
12. [数据库架构](#数据库架构)
13. [配置指南](#配置指南)
14. [API参考](#api参考)
15. [常见问题](#常见问题)
16. [故障排除](#故障排除)
17. [贡献指南](#贡献指南)

---

## 项目概述

### 核心概念

**Deriv Smart Trading Gateway** 是一个企业级的多智能体交易决策平台，为Deriv交易所设计。该系统通过自然语言处理、多角色协同决策、实时市场数据分析和安全执行框架，将交易员的意图转化为可追踪、可审计的交易行动。

### 设计哲学

- **AI-Native架构**: 所有核心决策流程由LangGraph驱动的多智能体系统处理
- **Human-in-the-Loop**: 关键执行点需要人工确认，防止无意行为
- **完全可审计**: 每个决策链、API调用、交易记录都被持久化到本地SQLite
- **隔离策略空间**: 微交易策略与主交易台独立运行，互不影响
- **安全优先**: 多层验证机制保护API Token、账户状态、交易金额

### 主要特性

| 特性 | 描述 |
|-----|------|
| **多智能体编排** | LangGraph Supervisor + 5个专业Advisor顾问 |
| **自然语言命令** | 支持中文和英文交易指令解析 |
| **实时市场数据** | WebSocket连接Deriv获取Tick和K线数据 |
| **交互式图表** | Plotly集成，支持标注、测量、对比、导出 |
| **多资产支持** | 合成指数、跳跃指数、Boom/Crash、外汇 |
| **纸面评估** | 对顾问判断进行历史回测评分 |
| **预算保护** | 多层预算闸门防止超额交易 |
| **电商价格采集** | 跨平台商品价格爬虫和对比分析 |

---

## 系统架构

### 整体架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                        用户 / 交易经理                             │
└─────────────────────────────────────────────────────────────────┘
                                  │
                ┌─────────────────┼─────────────────┐
                │                 │                 │
                ▼                 ▼                 ▼
        ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
        │ 原生桌面应用  │  │ Streamlit控制台│ │ 电商价格采集  │
        │  (PySide6)   │  │   (Web UI)   │  │   (爬虫)      │
        └──────┬───────┘  └──────┬───────┘  └──────┬───────┘
               │                 │                 │
               └─────────────────┼─────────────────┘
                                 │
                ┌────────────────┬┼┬────────────────┐
                │                │ │                │
                ▼                ▼ ▼                ▼
        ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
        │ LangGraph    │  │ LangGraph    │  │ 微交易引擎    │
        │ 交易团队      │  │ 顾问理事会    │  │ (策略分析)    │
        │ (Supervisor) │  │ (Advisor)    │  │ (决策生成)    │
        └──────┬───────┘  └──────┬───────┘  └──────┬───────┘
               │                 │                 │
               └─────────────────┼─────────────────┘
                                 │
                        ┌────────▼────────┐
                        │  FastMCP服务器   │
                        │ (Deriv工具层)    │
                        └────────┬────────┘
                                 │
                        ┌────────▼────────┐
                        │ Deriv WebSocket  │
                        │ API (生产环境)    │
                        └──────────────────┘
```

### 核心组件交互流程

#### 1. 交易执行流程

```
用户输入 (自然语言)
   │
   ▼
交易经理 (Manager Agent)
   │ 解析意图、拆分任务
   ▼
任务路由 (LangGraph Supervisor)
   │
   ├─► 策略研究员 (Strategy) - 拆分假设条件
   │
   ├─► 行情分析师 (Market) - 读取Tick/K线
   │
   ├─► 风控官 (Risk) - 检查账户和金额
   │
   ├─► 合规审查员 (Compliance) - 检查请求合法性
   │
   ├─► 图表工程师 (Chart) - 生成K线快照
   │
   ├─► 执行交易员 (Execution) - 提交订单
   │   │ (仅有此Agent能调用Deriv写操作)
   │   ▼
   │   人工确认闸门 ◄─── 需要用户点击确认
   │   │
   │   ▼
   │   Token验证、金额验证、Demo/Live验证
   │   │
   │   ▼
   │   Deriv WebSocket API ◄─── 订单提交
   │
   └─► 报告员 (Report) - 生成决策链
   │
   ▼
交易回执 + 审计日志
```

#### 2. 顾问理事会流程

```
用户问题 + 市场Symbol + 时间预算
   │
   ▼
宏观顾问 (Macro) ─────────────────┐
量化顾问 (Quant) ─────────────────┤
盘口顾问 (Flow) ──────────────────┼► (并行执行)
风控顾问 (Risk) ──────────────────┤
反方顾问 (Contrarian) ─────────────┘
   │
   │ (可选：联网检索网页信息)
   │
   ▼
各顾问得出独立见解
   │
   ▼
首席顾问 (Chief Synthesizer)
   │ 汇总所有见解
   │
   ▼
最终结论 (CALL/PUT/WAIT) + 置信度 + 执行前提
```

#### 3. 微交易策略流程

```
用户配置目标和预算
   │
   ▼
获取最近K线数据
   │
   ▼
微交易分析器
   ├─ 计算动量 (最近价格变化%)
   ├─ 计算EMA (指数移动平均线)
   ├─ 计算波动率 (历史波动%)
   ├─ 计算成本优势 (手续费+滑点)
   └─ 综合打分
   │
   ▼
纸面交易回测
   │
   ├─ 模拟执行交易
   ├─ 计算PnL
   ├─ 追踪资金曲线
   └─ 熔断器检查
   │
   ▼
结果和建议 (不自动下单)
```

---

## 快速开始

### 环境要求

- **操作系统**: macOS 10.13+, Windows 10+, Ubuntu 18.04+
- **Python版本**: 3.11 或更高
- **内存**: 最少 4GB RAM (推荐 8GB)
- **网络**: 稳定的互联网连接 (WebSocket)

### 安装步骤

#### 1. 克隆仓库

```bash
git clone <repository-url>
cd deriv-smart-trading-gateway-feature-desktop-micro-ui
```

#### 2. 创建虚拟环境

```bash
python3 -m venv .venv

# macOS / Linux
source .venv/bin/activate

# Windows
.venv\Scripts\activate
```

#### 3. 安装基础依赖

```bash
pip install -r requirements.txt
```

#### 4. 选择启动方式

**选项A: 启动Streamlit网页控制台**

```bash
streamlit run web_app.py --server.port 8501
```

打开浏览器访问: `http://localhost:8501`

**选项B: 启动原生桌面应用**

首先安装桌面依赖:

```bash
pip install -r desktop_requirements.txt
```

然后运行:

```bash
python desktop_app.py
```

**选项C: 启动MCP服务器**

```bash
python server.py
```

服务器将在标准MCP端口监听。

### 获取Deriv Token

1. 访问 [Deriv Developer Hub](https://api.deriv.com/)
2. 创建新的API Token (选择 `Demo` 或 `Real` 账户)
3. 复制Token字符串
4. 在UI中的"安全密钥配置"部分粘贴Token

**注意**: Token仅保存在当前Session状态中，不会写入源代码或配置文件。

### 第一次交易

1. 在Streamlit中，进入"交易台"页面
2. 输入示例命令: `帮我看看 R_100，如果最新Tick在跌，就用 1 美金买个看涨，持续 5 ticks`
3. 系统会:
   - 读取最新Tick数据
   - 解析交易条件
   - 生成待确认交易
   - 等待你点击"确认"按钮
   - 提交订单到Deriv
   - 保存审计日志

---

## 依赖要求

### 生产依赖 (requirements.txt)

| 包名 | 版本 | 用途 |
|-----|------|------|
| `mcp` | ≥1.9.0 | Model Context Protocol 框架 |
| `websockets` | ≥12.0 | WebSocket客户端 (Deriv连接) |
| `httpx` | ≥0.27.0 | 异步HTTP客户端 |
| `beautifulsoup4` | ≥4.12.3 | HTML解析 (网页爬虫) |
| `pydantic` | ≥2.7.0 | 数据验证和序列化 |
| `pandas` | ≥2.2.0 | 数据处理和分析 |
| `typing-extensions` | ≥4.10.0 | 类型提示扩展 |
| `certifi` | ≥2024.2.2 | SSL证书验证 |
| `streamlit` | ≥1.36.0 | Web UI框架 |
| `plotly` | ≥5.22.0 | 交互式图表库 |
| `openai` | ≥1.35.0 | OpenAI API客户端 |
| `anthropic` | ≥0.30.0 | Anthropic API客户端 |
| `langgraph` | ≥0.2.0 | 多智能体编排框架 |
| `pytest` | ≥8.0.0 | 测试框架 |

### 桌面依赖 (desktop_requirements.txt)

| 包名 | 版本 | 用途 |
|-----|------|------|
| `PySide6` | ≥6.7.0 | Qt 6 Python绑定 (原生GUI) |

### 打包依赖 (desktop_packaging_requirements.txt)

用于构建可执行的macOS应用:

```
pyinstaller>=6.0.0
pyinstaller-hooks-contrib>=2024.0
```

---

## 核心模块详解

### 1. web_app.py - Streamlit主应用

**功能**: 完整的Web操作界面，包含多个页面和实时交互

**文件大小**: ~2600行代码

**主要职责**:
- UI路由和页面管理
- 会话状态管理 (Token、模型配置、聊天历史)
- LangGraph运行时集成
- Plotly图表渲染
- 实时数据流更新

**核心类和函数**:

```python
# 页面组件
- display_sidebar()          # 侧边栏配置面板
- display_advisor_room()     # 顾问理事会页面
- display_micro_strategy()   # 微交易策略页面
- display_trading_desk()     # 交易台页面
- display_charts()           # 图表工作台
- display_monitor()          # 系统监控页面

# 状态管理
- init_session_state()       # 初始化Session
- get_or_create_graph()      # 获取/创建LangGraph实例
- system_health_snapshot()   # 系统健康快照

# 工具函数
- mask_secret()              # 隐藏敏感信息
- provider_display()         # 格式化API供应商名称
- in_streamlit_runtime()     # 运行时检测
```

**国际化支持**:

系统支持完整的中英文双语界面，通过 `I18N` 字典管理所有UI文本:

```python
I18N = {
    "zh": {
        "sidebar_title": "Deriv Gateway",
        "chat_placeholder": "例如：帮我看看 R_100...",
        # ... 200+ 中文键值对
    },
    "en": {
        "sidebar_title": "Deriv Gateway",
        "chat_placeholder": "Example: Check R_100...",
        # ... 200+ 英文键值对
    }
}
```

### 2. server.py - FastMCP Deriv工具服务器

**功能**: 暴露Deriv交易API作为MCP工具供Agent调用

**文件大小**: ~400行代码

**主要MCP工具**:

#### get_market_ticks(symbol: str, subscribe: bool = False) -> dict

获取最新市场Tick数据

```python
输入:
  symbol: "R_100"  # 市场Symbol
  subscribe: bool  # 是否订阅实时更新

输出:
{
  "symbol": "R_100",
  "quote": 12345.67,
  "bid": 12345.50,
  "ask": 12345.84,
  "timestamp": "2026-06-09T10:30:45Z"
}
```

#### get_historical_candles(symbol, granularity, count) -> dict

获取历史K线数据

```python
输入:
  symbol: "R_100"
  granularity: 60        # 秒级周期 (60=1m, 300=5m, 3600=1h)
  count: 100            # 请求K线数量 (1-1000)

输出:
[
  {
    "open": 12340.0,
    "high": 12350.0,
    "low": 12330.0,
    "close": 12345.0,
    "volume": 1500,
    "timestamp": "2026-06-09T10:30:00Z"
  },
  ...
]
```

#### execute_simulated_trade(api_token, symbol, amount, contract_type, duration, duration_unit, allow_live) -> dict

执行模拟交易

```python
输入:
  api_token: "deriv_token_xxx"
  symbol: "R_100"
  amount: 10.0              # 交易金额
  contract_type: "CALL"     # "CALL" 或 "PUT"
  duration: 5               # 期限数值
  duration_unit: "t"        # "m" (分钟), "h" (小时), "t" (tick)
  allow_live: False         # 防止意外的Live执易

输出:
{
  "contract_id": 123456789,
  "status": "accepted",
  "buy_price": 8.50,
  "payout": 18.50,
  "entry_spot": 12345.67,
  "entry_time": "2026-06-09T10:30:45Z"
}
```

#### check_account_status(api_token) -> dict

检查账户状态

```python
输出:
{
  "email": "user@example.com",
  "balance": 1000.00,
  "currency": "USD",
  "account_type": "demo",  # "demo" 或 "real"
  "leverage": 1
}
```

#### get_open_contract_status(api_token, contract_id) -> dict

获取开仓合约状态

```python
输出:
{
  "contract_id": 123456789,
  "entry_spot": 12345.67,
  "current_spot": 12355.00,
  "payout": 18.50,
  "profit_loss": 8.50,
  "is_expired": false,
  "is_sold": false
}
```

#### close_open_contract(api_token, contract_id) -> dict

平仓开仓合约

```python
输出:
{
  "contract_id": 123456789,
  "status": "closed",
  "exit_spot": 12355.00,
  "exit_time": "2026-06-09T10:35:00Z",
  "profit_loss": 8.50
}
```

**验证机制**:

所有输入都通过Pydantic模型严格验证:

```python
class SimulatedTradeInput(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")
    
    api_token: NonEmptyString
    symbol: NonEmptyString
    amount: Annotated[float, Field(gt=0)]                    # 必须 > 0
    contract_type: ContractType                               # 只允许 CALL/PUT
    duration: Annotated[int, Field(ge=1)]                    # >= 1
    duration_unit: DurationUnit                               # 只允许 m/h/t
    allow_live: bool = False                                  # 默认禁用Live
```

### 3. micro_trading.py - 微交易策略引擎

**功能**: 小额频繁交易的决策分析，包括动量、EMA、波动率等技术指标

**文件大小**: ~300行代码

**核心类**:

```python
@dataclass(frozen=True)
class MicroTradeConfig:
    symbol: str                      # 交易Symbol
    asset_kind: AssetKind           # "deriv"/"fund"/"equity"/"crypto"/"forex"
    cadence_seconds: int = 30        # 检查周期 (秒)
    max_trade_amount: float = 1.0    # 单笔最大金额
    min_confidence: float = 0.58     # 最小置信度阈值
    max_volatility_pct: float = 2.8  # 最高波动率容限 (%)
    min_momentum_pct: float = 0.03   # 最低动量阈值 (%)
    fee_bps: float = 0.0             # 手续费 (基点)
    slippage_bps: float = 1.0        # 滑点 (基点)
    cooldown_seconds: int = 60       # 冷却期 (秒)
    max_daily_loss_pct: float = 2.0  # 日最大亏损 (%)
```

**主要函数**:

#### analyze_micro_trade(prices, config) -> dict

分析最新价格数据并生成交易信号

**输入**:

```python
prices: pd.DataFrame 或 list[dict]
        必须包含 "close" 列，可选 "timestamp"
        最少8条K线

config: MicroTradeConfig
        如上所示
```

**输出**:

```python
{
    "ok": bool,                    # 是否成功分析
    "action": "CALL" | "PUT" | "WAIT",  # 交易信号
    "confidence": float,           # 0-0.95 置信度
    "reason": str,                 # 决策原因
    "signal_evidence": {           # 信号证据
        "momentum_pct": float,     # 最近价格变化百分比
        "ema_separation_pct": float, # EMA分离度
        "volatility_pct": float,   # 历史波动率
        "cost_edge_bps": float     # 成本优势
    },
    "blockers": list[str]          # 阻挡因素 (价格历史不足等)
}
```

**技术指标说明**:

1. **动量 (Momentum)**
   - 计算最近两根K线的价格变化百分比
   - 正数表示上升趋势，负数表示下降趋势

2. **EMA分离 (EMA Separation)**
   - 计算EMA(4) 和 EMA(9) 之间的差距
   - 分离度越大，趋势越明确

3. **波动率 (Realized Volatility)**
   - 计算最近12个周期的收益率标准差
   - 乘以sqrt(周期数)年化
   - 高波动率可能导致WAIT信号

4. **成本优势 (Cost Edge)**
   - 比较预期收益与手续费+滑点
   - 正的成本优势表示交易有利可图

**置信度算法**:

```python
# 基础置信度 (50% - 95%)
base_confidence = min_confidence  # 58%

# 根据动量调整 (+/- 10%)
momentum_adjustment = momentum_pct * 0.1

# 根据EMA分离调整 (+/- 5%)
ema_adjustment = ema_separation_pct * 0.05

# 波动率惩罚 (- 5% ~ 15%)
volatility_penalty = max(0, volatility_pct - 2.0) * 0.05

# 最终置信度
confidence = clip(base + momentum_adj + ema_adj - vol_penalty, 0.0, 0.95)
```

### 4. advisor_evaluation.py - 顾问评估模块

**功能**: 对历史顾问建议进行回测评估

**文件大小**: ~200行代码

**核心函数**:

#### evaluate_advisor_outcome(stance, entry_price, exit_price, confidence, wait_threshold_pct=0.03) -> dict

评估单个顾问建议的准确性

```python
输入:
  stance: "CALL" | "PUT" | "WAIT"      # 顾问建议方向
  entry_price: float                   # 入场参考价格
  exit_price: float                    # 复盘价格
  confidence: float                    # 顾问置信度
  wait_threshold_pct: float = 0.03     # WAIT判断阈值 (3%)

输出:
{
    "status": "evaluated" | "pending",
    "stance": "CALL" | "PUT" | "WAIT",
    "entry_price": float,
    "exit_price": float,
    "price_delta": float,              # 价格差
    "return_pct": float,               # 价格收益率
    "paper_return_pct": float,         # 按方向计算的纸面收益
    "outcome": str,                    # "correct"/"wrong"/"flat"/"correct_wait"/"missed_move"
    "score": float,                    # 0.0 (错误) - 1.0 (正确) - 0.5 (平手)
    "confidence": float
}
```

**评分规则**:

| 建议 | 价格变化 | 结果 | 得分 |
|-----|---------|------|------|
| CALL | 上升 | correct | 1.0 |
| CALL | 下降 | wrong | 0.0 |
| CALL | 平手 | flat | 0.5 |
| PUT | 下降 | correct | 1.0 |
| PUT | 上升 | wrong | 0.0 |
| WAIT | ±0-3% | correct_wait | 1.0 |
| WAIT | >3% | missed_move | 0.5 |

#### evaluate_advisor_horizons(stance, entry_price, future_closes, confidence, horizons=(1,5,10)) -> dict

在多个时间窗口上评估建议 (1分钟、5分钟、10分钟)

```python
输出:
{
    "status": "evaluated" | "pending",
    "horizons": {
        "1m": {...outcome...},
        "5m": {...outcome...},
        "10m": {...outcome...}
    },
    "evaluated_count": int,
    "best_horizon": "5m",
    "best_paper_return_pct": float
}
```

#### summarize_advisor_evaluations(evaluations) -> dict

汇总多个评估记录

```python
输出:
{
    "evaluated_count": int,           # 已评估数量
    "directional_count": int,         # 有方向的建议数量
    "direction_accuracy": float,      # 方向准确率 (0-1)
    "average_score": float,           # 平均得分
    "average_paper_return_pct": float # 平均纸面收益率
}
```

### 5. paper_trading.py - 纸面交易和熔断器

**功能**: 微交易策略的历史回测和风险管理

**文件大小**: ~250行代码

**核心类**:

```python
@dataclass(frozen=True)
class CircuitBreakerConfig:
    max_consecutive_losses: int = 3       # 连续亏损上限
    max_total_loss_amount: float = 2.0    # 最大亏损金额
    max_drawdown_pct: float = 3.0         # 最大回撤百分比
    max_trade_count: int = 30             # 最大交易笔数
```

**主要函数**:

#### backtest_micro_strategy(prices, strategy_config, circuit_config, lookback_bars=12, exit_after_bars=1) -> dict

回测微交易策略

```python
输出:
{
    "ok": bool,
    "reason": str,
    "bars": int,
    "trades": [
        {
            "index": int,
            "action": "CALL" | "PUT",
            "entry_price": float,
            "exit_price": float,
            "amount": float,
            "return_pct": float,
            "pnl": float,              # 损益
            "equity": float,           # 账户资金
            "confidence": float
        },
        ...
    ],
    "summary": {
        "trade_count": int,
        "wins": int,
        "losses": int,
        "win_rate": float,             # 胜率
        "total_pnl": float,            # 总损益
        "ending_equity": float,        # 最终资金
        "average_pnl": float,          # 平均PnL
        "halted": bool,                # 是否被熔断
        "halt_reason": str,            # 熔断原因
        "drawdown_pct": float          # 最大回撤
    }
}
```

**回测算法**:

```
初始资金 = 100
for 每个K线 (从 lookback_bars 到 末尾):
    当前窗口 = 过去lookback_bars根K线 + 当前K线
    
    分析 = analyze_micro_trade(当前窗口, strategy_config)
    action = 分析.action
    
    if action 是 CALL/PUT/BUY/SELL:
        entry_price = 当前K线.close
        exit_price = exit_after_bars后的K线.close
        
        pnl = 计算损益(action, entry_price, exit_price, amount)
        资金 += pnl
        
        记录交易
        
        检查熔断器:
            if 连续亏损 >= max_consecutive_losses:
                停止回测
            if 总亏损 >= max_total_loss_amount:
                停止回测
            if 回撤 >= max_drawdown_pct:
                停止回测
            if 交易数 >= max_trade_count:
                停止回测

输出总结: 胜率, 总PnL, 最终资金等
```

### 6. budget_guard.py - 预算与安全防护

**功能**: 多层预算闸门防止超额交易

**文件大小**: ~150行代码

**核心类**:

```python
@dataclass(frozen=True)
class BudgetLimits:
    enabled: bool = True                      # 是否启用预算防护
    max_single_trade_amount: float = 1.0      # 单笔交易金额上限
    max_daily_trade_budget: float = 5.0       # 日预算上限
    max_total_trade_budget: float = 5.0       # 总预算上限
```

**主要函数**:

#### budget_guard_check(action, amount, limits, daily_spent=0.0, total_spent=0.0) -> dict

检查交易是否符合预算限制

```python
输出:
{
    "ok": bool,                        # 是否通过检查
    "reason": str,                     # 检查结果原因
    "amount": float,                   # 规范化后的金额
    "remaining_daily": float,          # 今日剩余预算
    "remaining_total": float           # 总剩余预算
}
```

**检查规则** (依次执行):

1. 金额有效性: `amount > 0`
2. 预算防护启用检查: `limits.enabled`
3. 单笔上限检查: `amount <= max_single_trade_amount`
4. 日预算检查: `daily_spent + amount <= max_daily_trade_budget`
5. 总预算检查: `total_spent + amount <= max_total_trade_budget`

#### reset_daily_spend_if_needed(state, today=None) -> dict

重置每日预算计数器 (跨天时)

```python
输入:
  state: 当前状态字典
  today: date对象 (默认使用今天)

输出:
  更新后的状态字典，如需重置则清零 budget_spent_today
```

---

## UI界面完全指南

### 整体布局

```
┌─────────────────────────────────────────────────────┐
│           全局状态栏 (Global Status Strip)           │
│  Symbol │ 谋士结论 │ 入场价 │ API调用 │ 同步 │ 待单  │
├─────────────────────────────────────────────────────┤
│ 侧边栏  │                                             │
│ (导航   │          主工作台区域                        │
│ +配置)  │        (根据选择页面变化)                    │
│         │                                             │
│ ┌─────┐ │  ┌──────────────────────────────────────┐  │
│ │导航  │ │  │        页面内容                      │  │
│ │按钮  │ │  │                                     │  │
│ ├─────┤ │  └──────────────────────────────────────┘  │
│ │配置  │ │  ┌──────────────────────────────────────┐  │
│ │面板  │ │  │        页面内容                      │  │
│ │      │ │  │                                     │  │
│ └─────┘ │  └──────────────────────────────────────┘  │
└─────────────────────────────────────────────────────┘
```

### 页面详解

#### 1. 谋士室 (Advisor Room) 页面

**功能**: 多顾问协同决策和评估

**布局**:
```
┌─────────────────────────────────────────────┐
│ 问题输入 | 时间预算 | 联网 | 分析Symbol    │
├─────────────────────────────────────────────┤
│ [召集谋士] 按钮                             │
├─────────────────────────────────────────────┤
│ 实时处理进度 / 最终结论                     │
├─────────────────────────────────────────────┤
│ 一致结论 | 置信度 | 执行前提                │
├─────────────────────────────────────────────┤
│ 谋士讨论纪要 (Tabs)                        │
│ ├─ 宏观顾问                                │
│ ├─ 量化顾问                                │
│ ├─ 盘口顾问                                │
│ ├─ 风控顾问                                │
│ ├─ 反方顾问                                │
│ └─ 首席顾问 (综合)                        │
├─────────────────────────────────────────────┤
│ 网页来源 (如有联网)                        │
├─────────────────────────────────────────────┤
│ 谋士评估 (复盘最近判断)                     │
│ ├─ 选择时间窗口 (1m/5m/10m)               │
│ ├─ 输入复盘价格                            │
│ └─ 显示准确率和收益                        │
└─────────────────────────────────────────────┘
```

**核心功能**:

1. **问题配置**
   - 输入框: 自由文本问题
   - 时间预算滑块: 5-120秒
   - 联网开关: 启用/禁用网页检索
   - Symbol选择: 下拉菜单或手动输入

2. **执行流程**
   - 点击"召集谋士"
   - 5个顾问并行分析
   - 首席顾问综合意见
   - 显示最终结论 (CALL/PUT/WAIT)

3. **结论解析**
   ```
   CALL  - 短期看涨，建议做多
   PUT   - 短期看跌，建议做空
   WAIT  - 不确定或条件不足，建议观望
   ```

4. **置信度范围**: 0.0 (完全不确定) - 1.0 (完全确定)

5. **执行前提**: 顾问建议需满足的条件 (如"需要突破某价位")

6. **评估功能**
   - 输入复盘价格
   - 选择时间窗口
   - 系统计算方向准确率和纸面收益
   - 保存评估结果用于未来统计

#### 2. 小笔策略 (Micro Strategy) 页面

**功能**: 独立的小额频繁交易策略分析

**布局**:
```
┌────────────────────────────────────────────┐
│ 目标 | Symbol | 资产类型 | 数据来源选择     │
├────────────────────────────────────────────┤
│ 数据输入区                                 │
│ └─ 实时K线/手动价格输入                   │
├────────────────────────────────────────────┤
│ 预算配置                                   │
│ ├─ 单次金额                               │
│ ├─ 日预算                                 │
│ └─ 总预算                                 │
├────────────────────────────────────────────┤
│ 熔断器配置                                 │
│ ├─ 连续亏损上限                           │
│ ├─ 最大亏损金额                           │
│ ├─ 最大回撤 %                             │
│ └─ 最大交易笔数                           │
├────────────────────────────────────────────┤
│ [运行分析和回测] 按钮                     │
├────────────────────────────────────────────┤
│ 信号和建议                                 │
│ ├─ 当前信号 (CALL/PUT/WAIT)              │
│ ├─ 行动建议                               │
│ ├─ 观察方向                               │
│ ├─ 数据可信度                             │
│ ├─ 纸面收益                               │
│ └─ 信号证据 (详细指标)                   │
├────────────────────────────────────────────┤
│ 风险与预算摘要                             │
├────────────────────────────────────────────┤
│ 回测明细                                   │
│ ├─ 单笔交易记录表                         │
│ ├─ 时间 | 信号 | 入场 | 出场 | PnL       │
│ └─ [下载CSV]                              │
└────────────────────────────────────────────┘
```

**数据来源**:

1. **实时K线模式**
   - 直接从Deriv获取最近K线
   - 自动分析最新数据
   - 需要配置Token

2. **手动输入模式**
   - 复制粘贴收盘价格
   - 支持逗号/回车分隔
   - 用于离线分析

**资产类型**:

| 类型 | 默认信号 | 用途 |
|-----|--------|------|
| `deriv` | CALL/PUT/WAIT | Deriv合约 |
| `fund` | BUY/SELL/HOLD | 基金 |
| `equity` | BUY/SELL/HOLD | 股票 |
| `crypto` | BUY/SELL/HOLD | 加密货币 |
| `forex` | BUY/SELL/HOLD | 外汇 |

**预算机制**:

```
日预算 = max(今日剩余, 总剩余)

每笔交易:
  if 金额 > 单次上限:
    拒绝
  elif 今日已用 + 金额 > 日预算:
    拒绝
  elif 总已用 + 金额 > 总预算:
    拒绝
  else:
    允许
```

**回测结果解读**:

- **胜率**: 赚钱交易 / 总交易数
- **总PnL**: 所有交易的累计损益
- **最终资金**: 初始100 + 总PnL
- **熔断原因**: 如果因熔断停止，显示具体原因

#### 3. 交易台 (Trading Desk) 页面

**功能**: 自然语言交易指令处理和执行

**布局**:
```
┌──────────────────────────────────────────┐
│ 交易指令输入框 (大文本框)                 │
│ [发送指令] [清空输入]                    │
├──────────────────────────────────────────┤
│ 实时状态消息                             │
│ "交易团队正在协同处理..."                 │
├──────────────────────────────────────────┤
│ 智能体行动时间线                         │
│ ├─ [Manager] 收到指令: "帮我..."       │
│ ├─ [Strategy] 拆分目标: 2步            │
│ ├─ [Market] 读取数据: R_100 最新  │
│ ├─ [Risk] 检查: 预算充足              │
│ ├─ [Compliance] 审查: 通过            │
│ ├─ [Execution] 准备: 待确认单        │
│ └─ [Report] 生成: 决策链              │
├──────────────────────────────────────────┤
│ 团队结果                                 │
│ ├─ 结构化输出                           │
│ ├─ 执行状态                             │
│ └─ 风险提示                             │
├──────────────────────────────────────────┤
│ 待确认交易 (如有)                       │
│ ├─ 方向: CALL / PUT                  │
│ ├─ 金额: 10 USD                      │
│ ├─ 期限: 5 Ticks                     │
│ ├─ [我确认] [取消]                   │
│ └─ (需启用 human_confirmation)       │
├──────────────────────────────────────────┤
│ Agent 上下文记忆                        │
│ (每个Agent的会话记忆显示)               │
├──────────────────────────────────────────┤
│ 本地历史                                 │
│ ├─ 过去交易记录表                       │
│ ├─ 时间 | 指令 | 结果 | Agent      │
│ └─ [下载行动时间线]                    │
└──────────────────────────────────────────┘
```

**指令示例**:

```
例1 (简单查询):
"帮我看看 R_100，如果最新Tick在跌就告诉我"

例2 (条件交易):
"用 1 美金买 R_100 看涨，5 ticks"

例3 (复杂逻辑):
"R_100 最近 3 个 Tick 连续下跌吗？如果是，我用 2 美金买个看跌，持续 10 ticks"

例4 (图表):
"画 R_100 最近 120 根 1 分钟 K 线"

例5 (直接派活):
"@Market Agent: 检查 BOOM1000 最新波动率"
```

**执行流程**:

```
用户输入指令
  │
  ▼
[Manager] 解析意图、拆分任务
  │
  ├─ 判断是否需要读取数据
  ├─ 判断是否需要执行交易
  ├─ 判断是否需要生成图表
  └─ 确定任务路由
  │
  ▼
[Strategy] 拆分交易目标
  │ - 验证金额
  │ - 验证方向
  │ - 验证期限
  │
  ▼
[Market] 读取实时数据
  │ - 获取最新Tick
  │ - 获取K线数据
  │ - 验证市场条件
  │
  ▼
[Risk] 风控检查
  │ - 检查Token有效性
  │ - 检查账户余额
  │ - 检查预算限制
  │
  ▼
[Compliance] 合规审查
  │ - 检查金额清晰
  │ - 检查方向明确
  │ - 检查无重复下单
  │
  ▼
[Execution] 生成待确认交易
  │ - 组装订单参数
  │ - 等待人工确认
  │ - 或自动提交 (如未启用human_confirmation)
  │
  ▼
用户确认 (如启用) ► Deriv API ► 订单执行
  │
  ▼
[Report] 生成决策链和回执
```

**安全闸门**:

页面顶部显示执行安全面板:

```
┌─────────────────────────────────────────┐
│ 执行安全闸门                             │
├─────────────────────────────────────────┤
│ Token: ✓ (已配置)                      │
│ 人工确认: ✓ (需要)                     │
│ Live执行: ✗ (禁用)                    │
│ 待确认订单: 1                           │
│ 数据时效: ✓ (新鲜, 15秒内)            │
├─────────────────────────────────────────┤
│ 状态: [就绪] 或 [阻断]                 │
└─────────────────────────────────────────┘
```

#### 4. 图表 (Charts) 页面

**功能**: 交互式K线图表、对比分析、测量工具

**布局**:
```
┌──────────────────────────────────────────┐
│ 控制面板                                 │
│ ├─ Symbol选择: [下拉] / [自定义输入]    │
│ ├─ 周期选择: [1m] [5m] [15m] [1h] ... │
│ ├─ K线数量: [30] [60] [120] [200]  │
│ ├─ [加载所选图表]                      │
│ └─ 图表高度滑块: [────────●─────] 600  │
├──────────────────────────────────────────┤
│ 对比走势控制                             │
│ ├─ Symbol对标: [输入框]                │
│ └─ [加载/刷新对比]                     │
├──────────────────────────────────────────┤
│ 测量工具                                 │
│ ├─ 起点K线: [选择]                     │
│ ├─ 终点K线: [选择]                     │
│ ├─ [计算] 按钮                         │
│ └─ 结果:                               │
│    ├─ K线数: 25                       │
│    ├─ 时间跨度: 25分钟                │
│    ├─ 收盘差: +120点                  │
│    └─ 区间振幅: 180点                 │
├──────────────────────────────────────────┤
│ 大K线图表区域 (可交互)                  │
│ ├─ 工具栏:                             │
│ │  ├─ 框选放大                        │
│ │  ├─ 拖拽平移                        │
│ │  ├─ 绘制线条                        │
│ │  ├─ 绘制矩形                        │
│ │  ├─ 绘制圆形                        │
│ │  ├─ 自由路径                        │
│ │  ├─ 橡皮擦                          │
│ │  └─ [PNG导出]                      │
│ │
│ └─ 图表内容:                           │
│    ├─ 烛柱 (Open/High/Low/Close)      │
│    ├─ 成交量柱                         │
│    ├─ 用户标注                         │
│    └─ (可选) 顾问参考价格线            │
├──────────────────────────────────────────┤
│ 完整OHLCV数据表                        │
│ ├─ Timestamp | O | H | L | C | V    │
│ ├─ ...       |...|...|...|...|...   │
│ └─ [下载CSV]                          │
└──────────────────────────────────────────┘
```

**关键功能**:

1. **Symbol支持**
   - 预设下拉: R_100, R_75, BOOM1000, 等
   - 自定义输入: 输入任何有效Symbol

2. **周期支持**
   - 60秒 (1分钟)
   - 300秒 (5分钟)
   - 3600秒 (1小时)
   - 等等

3. **交互工具** (Plotly Toolbar)
   - **框选放大**: 在图表上框选区域放大
   - **拖拽平移**: 左键拖动图表平移
   - **缩放**: 鼠标滚轮上下缩放
   - **十字丝**: 悬浮显示坐标
   - **绘图**: 线条、矩形、圆形、自由路径
   - **橡皮**: 擦除标注
   - **截图**: 导出为PNG

4. **数据时效指示**
   ```
   数据年龄: 12秒前
   ├─ ✓ 新鲜 (< 180秒)
   ├─ ⚠ 可能过期 (180-600秒)
   └─ ✗ 已过期 (> 600秒)
   ```

5. **顾问参考线**
   - 如顾问有最新判断，在图表上显示其入场参考价
   - 用颜色区分方向 (看涨=绿, 看跌=红)

#### 5. 监控 (Monitor) 页面

**功能**: 系统运行状态、Agent图谱、API追踪、同步总线

**布局**:
```
┌──────────────────────────────────────────┐
│ 系统健康检查                             │
│ ├─ 本地数据库: ✓ 正常                  │
│ ├─ LangGraph: ✓ 已就绪                │
│ ├─ Token: ✓ 已配置 (masked)          │
│ ├─ 待确认订单: ✗ 无                   │
│ └─ 数据时效: ✓ 新鲜 (15秒)          │
├──────────────────────────────────────────┤
│ Agent 图谱 (LangGraph 流程图)          │
│ ├─ [Manager] (中心)                   │
│ ├─ ├─ [Strategy]                     │
│ ├─ ├─ [Market]                       │
│ ├─ ├─ [Risk]                         │
│ ├─ ├─ [Compliance]                   │
│ ├─ ├─ [Chart]                        │
│ ├─ ├─ [Execution]                    │
│ └─ └─ [Report]                       │
│
│ 角色状态 (当前运行状态)                  │
│ ├─ Manager: [运行中]                  │
│ ├─ Market: [待命]                     │
│ ├─ Execution: [等待确认]              │
│ └─ ...                                │
├──────────────────────────────────────────┤
│ API 调用 Trace (最近100条)             │
│ ├─ 时间 | 方法 | Symbol | 状态 | 耗时  │
│ ├─ 2026-06-09 10:30:45 | get_market_ticks | R_100 | ✓ | 234ms |
│ ├─ 2026-06-09 10:30:46 | get_historical_candles | R_100 | ✓ | 567ms |
│ └─ ...                                │
├──────────────────────────────────────────┤
│ 实时同步总线 (最近事件流)               │
│ ├─ [10:30:45] API: get_market_ticks   │
│ ├─ [10:30:45] TICK: R_100 = 12345.67 │
│ ├─ [10:30:46] AGENT: Market 完成数据读取 │
│ ├─ [10:30:47] GRAPH: Strategy开始执行 │
│ └─ ...                                │
└──────────────────────────────────────────┘
```

**组件说明**:

1. **系统健康检查**
   - 检查本地SQLite数据库连接
   - 检查LangGraph运行时是否初始化
   - 检查API Token是否有效
   - 检查待确认交易状态
   - 检查市场数据时效性

2. **Agent图谱**
   - 展示当前LangGraph的node结构
   - 活跃的node用高亮表示
   - 显示supervisor的路由决策

3. **角色状态**
   | 状态 | 含义 |
   |-----|------|
   | 运行中 | 正在处理任务 |
   | 待命 | 准备接收任务 |
   | 等待确认 | 等待人工确认 |
   | 已完成 | 本轮任务已完成 |
   | 错误 | 执行出错 |

4. **API追踪**
   - 记录所有MCP工具调用
   - 显示调用时间、方法、参数
   - 显示返回状态和响应时间
   - 用于性能分析和调试

5. **同步总线**
   - 实时事件流
   - 所有系统事件聚合显示
   - 用于理解系统运行过程

### 全局状态栏详解

每个页面顶部都有一个全局状态栏，显示关键信息:

```
┌─────────────────────────────────────────────────────┐
│ Symbol: R_100 │ 谋士: CALL │ 入场: 12345.67 │ API: 23 │ 同步: v8 │ 待单: 1 │
└─────────────────────────────────────────────────────┘
```

| 字段 | 更新频率 | 用途 |
|-----|--------|------|
| Symbol | 用户选择时 | 当前分析的市场 |
| 谋士结论 | 顾问完成后 | 最新的顾问建议方向 |
| 入场价 | 顾问完成后 | 参考入场价格 |
| API调用 | 每次调用后 | API调用计数 |
| 同步版本 | 关键事件后 | 用于同步检测 |
| 待单数 | 订单状态变化 | 当前待确认订单数 |

### 侧边栏配置面板

```
┌────────────────────────────────┐
│ Deriv Gateway                  │
│ 多智能体交易终端               │
├────────────────────────────────┤
│ 页面导航                       │
│ ├─ [谋士室]                   │
│ ├─ [小笔策略]                 │
│ ├─ [交易台]                   │
│ ├─ [图表]                     │
│ └─ [监控]                     │
├────────────────────────────────┤
│ 语言选择                       │
│ ├─ [中文] ✓                  │
│ └─ [English]                 │
├────────────────────────────────┤
│ 安全密钥配置                   │
│ ├─ Deriv Token: [输入框]     │
│ │  (输入后立即生效)           │
│ │  Masked: der...***xxx      │
│ │
│ ├─ 大模型 API: [下拉]        │
│ │  ├─ 本地规则 (无需Key)    │
│ │  ├─ OpenAI                │
│ │  ├─ DeepSeek             │
│ │  ├─ Anthropic            │
│ │  └─ 自定义兼容服务         │
│ │
│ ├─ 模型Key: [输入框]         │
│ │  (仅Session保存)           │
│ │
│ └─ 模型名: [输入框]          │
│    (如使用自定义服务)          │
├────────────────────────────────┤
│ 交易安全闸门                   │
│ ├─ ☑ 下单前需人工确认        │
│ ├─ ☐ 允许Live账户执行        │
│ └─ [我确认下一笔订单]        │
├────────────────────────────────┤
│ 连接状态                       │
│ ├─ Deriv Token: 已配置       │
│ ├─ 大模型API: OpenAI         │
│ ├─ 模型: gpt-4              │
│ └─ 本地DB: gateway.sqlite3   │
├────────────────────────────────┤
│ 历史 & 导出                    │
│ ├─ 本地历史记录表              │
│ │  ├─ [时间] [指令] [结果]    │
│ │  └─ ...                    │
│ │
│ └─ [下载审计 JSON]            │
│    (当前决策链状态，不含Token)
└────────────────────────────────┘
```

---

## 多智能体系统

### LangGraph交易团队架构

该系统使用LangGraph (由LangChain团队开发的图构建框架) 实现复杂的多Agent工作流。

#### 交易团队图节点

```python
# 交易团队图
trading_team_graph = {
    "nodes": {
        "manager": {
            "role": "交易经理",
            "responsibility": "接收用户指令，拆分任务，路由工作流",
            "inputs": ["user_prompt"],
            "outputs": ["task_breakdown", "routing_decision"]
        },
        "strategy": {
            "role": "策略研究员",
            "responsibility": "拆分交易目标，验证参数完整性",
            "inputs": ["user_prompt", "task_breakdown"],
            "outputs": ["strategy_analysis", "missing_params"]
        },
        "market": {
            "role": "行情分析师",
            "responsibility": "读取Deriv Tick/K线，判断市场条件",
            "inputs": ["symbol", "timeframe", "count"],
            "outputs": ["market_data", "trend_analysis"]
        },
        "risk": {
            "role": "风控官",
            "responsibility": "检查账户、余额、预算限制",
            "inputs": ["amount", "account_state", "budget_limits"],
            "outputs": ["risk_check_passed", "risk_warnings"]
        },
        "compliance": {
            "role": "合规审查员",
            "responsibility": "检查请求是否合规（金额清晰、方向明确等）",
            "inputs": ["trade_request"],
            "outputs": ["compliance_passed", "issues"]
        },
        "chart": {
            "role": "图表工程师",
            "responsibility": "生成K线快照、对比、测量数据",
            "inputs": ["symbol", "granularity", "count"],
            "outputs": ["chart_data", "chart_image"]
        },
        "execution": {
            "role": "执行交易员",
            "responsibility": "唯一能提交Deriv写操作的Agent，需人工确认",
            "inputs": ["trade_request_validated", "human_confirmation"],
            "outputs": ["trade_receipt", "order_id"]
        },
        "report": {
            "role": "报告员",
            "responsibility": "生成决策链、交易回执、审计日志",
            "inputs": ["all_previous_outputs"],
            "outputs": ["decision_chain", "audit_record"]
        }
    },
    
    "supervisor": {
        "role": "Supervisor (LangGraph)",
        "responsibility": "根据任务动态路由不同node，而非盲目执行所有node",
        "routing_logic": """
        if 仅查询市场:
            执行: [Manager → Market → Report]
        elif 生成图表:
            执行: [Manager → Chart → Report]
        elif 完整交易:
            执行: [Manager → Strategy → Market → Risk → Compliance → Execution → Report]
        else:
            执行: [Manager → 判断具体需要的nodes → Report]
        """
    }
}
```

#### 交易团队执行流程

```python
# 伪代码
def trading_team_run(user_prompt: str, state: dict) -> dict:
    """
    LangGraph Supervisor式工作流
    """
    
    # 1. Manager收到指令
    manager_output = agent_manager.run(user_prompt, state)
    # Output: {
    #     "task_type": "trade" | "query" | "chart",
    #     "required_agents": ["strategy", "market", "risk", ...],
    #     "analysis": "..."
    # }
    
    # 2. Supervisor决定执行路径
    execution_path = supervisor.route(manager_output)
    # 可能的路径:
    # - ["strategy", "market", "risk", "compliance", "execution", "report"]
    # - ["market", "report"]
    # - ["chart", "report"]
    
    # 3. 按顺序执行选中的nodes
    for agent_name in execution_path:
        if agent_name == "strategy":
            result = agent_strategy.run(manager_output, state)
            state.update(result)
            
        elif agent_name == "market":
            result = agent_market.run(state["symbol"], state["timeframe"], state)
            state.update({"market_data": result})
            
        elif agent_name == "risk":
            result = agent_risk.check(
                amount=state.get("amount"),
                account_state=state.get("account_state"),
                budget_limits=state.get("budget_limits")
            )
            state.update({"risk_check": result})
            
        elif agent_name == "compliance":
            result = agent_compliance.check(state)
            state.update({"compliance_check": result})
            
        elif agent_name == "execution":
            # 关键点：需要人工确认
            if state.get("require_human_confirmation"):
                state["pending_confirmation"] = True
                # UI显示待确认交易，等待用户点击
                # 用户点击后：
                state["human_confirmed"] = True
            
            result = agent_execution.submit_trade(state)
            state.update({"trade_receipt": result})
            
        elif agent_name == "report":
            result = agent_report.generate(state)
            state.update({"final_report": result})
    
    # 4. 返回最终结果
    return state
```

### LangGraph顾问理事会架构

```python
advisor_council_graph = {
    "concurrent_advisors": [
        {
            "id": "advisor.macro",
            "name": "宏观顾问",
            "prompt": "阅读市场上下文、外部新闻、宏观风险偏好...",
            "tools": ["web_search", "news_api", "market_snapshot"]
        },
        {
            "id": "advisor.quant",
            "name": "量化顾问",
            "prompt": "只关注短线动量、MA5/MA20、最新Tick...",
            "tools": ["technical_analysis", "momentum_calculation"]
        },
        {
            "id": "advisor.flow",
            "name": "盘口顾问",
            "prompt": "盯盘口节奏、波动速度、执行窗口...",
            "tools": ["order_flow_analysis", "volatility_measurement"]
        },
        {
            "id": "advisor.risk",
            "name": "风控顾问",
            "prompt": "先保命，再谈收益。信息不足时优先建议WAIT...",
            "tools": ["risk_assessment", "scenario_analysis"]
        },
        {
            "id": "advisor.contrarian",
            "name": "反方顾问",
            "prompt": "挑战共识，寻找样本不足、信息滞后的风险...",
            "tools": ["consensus_challenge", "assumption_testing"]
        }
    ],
    
    "chief_synthesizer": {
        "id": "advisor.chief",
        "name": "首席顾问",
        "role": "汇总所有顾问意见，输出单一结论",
        "output_format": {
            "stance": "CALL | PUT | WAIT",
            "confidence": "0.0-1.0",
            "execution_prerequisites": "string",
            "failure_conditions": "string"
        }
    }
}
```

#### 顾问执行流程

```python
def advisor_council_run(question: str, symbol: str, time_budget: int, config: dict) -> dict:
    """
    并行运行5个顾问，限时汇总
    """
    import asyncio
    from concurrent.futures import ThreadPoolExecutor, as_completed
    
    advisors = [
        AdvisorNode("macro"),
        AdvisorNode("quant"),
        AdvisorNode("flow"),
        AdvisorNode("risk"),
        AdvisorNode("contrarian"),
    ]
    
    # 1. 市场数据快照 (共享给所有顾问)
    market_snapshot = fetch_market_data(symbol)
    # {
    #     "symbol": "R_100",
    #     "latest_tick": 12345.67,
    #     "recent_candles": [...],
    #     "bid": 12345.50,
    #     "ask": 12345.84,
    #     "timestamp": "..."
    # }
    
    # 2. 可选：网页信息抓取 (如启用)
    news_signal = fetch_web_research(question, symbol, time_budget) if use_web else None
    
    # 3. 并行运行所有顾问 (限时)
    start_time = time.time()
    max_duration = time_budget  # 秒
    
    opinions = []
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {
            executor.submit(
                advisor.analyze,
                question=question,
                market=market_snapshot,
                news=news_signal,
                timeout=max_duration - (time.time() - start_time)
            ): advisor.id
            for advisor in advisors
        }
        
        for future in as_completed(futures, timeout=max_duration):
            advisor_id = futures[future]
            try:
                opinion = future.result()
                opinions.append({
                    "advisor_id": advisor_id,
                    "stance": opinion["stance"],
                    "reasoning": opinion["reasoning"],
                    "confidence": opinion.get("confidence", 0.5)
                })
            except Exception as e:
                # 某个顾问超时或出错，记录但继续
                opinions.append({
                    "advisor_id": advisor_id,
                    "status": "error",
                    "error": str(e)
                })
    
    # 4. 首席顾问综合意见
    chief_input = {
        "question": question,
        "market": market_snapshot,
        "opinions": opinions,
        "remaining_time": max_duration - (time.time() - start_time)
    }
    
    final_conclusion = chief_advisor.synthesize(chief_input)
    # {
    #     "stance": "CALL",
    #     "confidence": 0.75,
    #     "execution_prerequisites": "需要突破12350",
    #     "failure_conditions": "如果低于12340则失效"
    # }
    
    # 5. 记录和返回
    return {
        "status": "completed",
        "question": question,
        "market_snapshot": market_snapshot,
        "news_signal": news_signal,
        "advisor_opinions": opinions,
        "consensus": final_conclusion,
        "elapsed_time": time.time() - start_time
    }
```

### Agent记忆系统

每个Agent都有自己的会话级短期记忆:

```python
class AgentMemory:
    """
    每个Agent会话中的上下文记忆
    """
    
    def __init__(self):
        self.memory = []  # [(timestamp, observation, action), ...]
    
    def observe(self, observation: str):
        """记录观察"""
        self.memory.append({
            "type": "observation",
            "content": observation,
            "timestamp": datetime.now()
        })
    
    def act(self, action: str, result: str):
        """记录行动和结果"""
        self.memory.append({
            "type": "action",
            "action": action,
            "result": result,
            "timestamp": datetime.now()
        })
    
    def recall(self, last_n: int = 10) -> list[str]:
        """回忆最近的N个事件"""
        return [
            f"{item['timestamp']}: {item['type']} - {item.get('content', item.get('action'))}"
            for item in self.memory[-last_n:]
        ]
```

---

## MCP服务器

### 概述

**MCP** (Model Context Protocol) 是一个开放标准，允许AI模型通过定义明确的工具接口与外部系统交互。

该项目中的 `server.py` 实现了一个FastMCP服务器，将Deriv交易API暴露为MCP工具，供LangGraph中的Agent调用。

### 服务器启动

```bash
python server.py
```

服务器将在标准MCP端口监听 (通常是stdio或Unix socket)。

### 可用MCP工具

#### 1. get_market_ticks

**定义**:
```python
@mcp.tool()
async def get_market_ticks(
    symbol: NonEmptyString,
    subscribe: bool = False
) -> dict
```

**功能**: 获取指定Symbol的最新市场Tick

**参数**:
- `symbol` (str): 市场Symbol，如 "R_100", "frxEURUSD"
- `subscribe` (bool): 是否订阅实时更新 (可选，默认False)

**返回值**:
```json
{
    "symbol": "R_100",
    "quote": 12345.67,
    "bid": 12345.50,
    "ask": 12345.84,
    "timestamp": "2026-06-09T10:30:45Z"
}
```

**错误**:
- `DerivAPIError`: Deriv API返回应用级错误
- `DerivTimeoutError`: 请求超时 (5秒)

#### 2. get_historical_candles

**定义**:
```python
@mcp.tool()
async def get_historical_candles(
    symbol: NonEmptyString,
    granularity: Granularity,
    count: Annotated[int, Field(ge=1, le=1000)]
) -> dict
```

**功能**: 获取历史K线数据

**参数**:
- `symbol` (str): 市场Symbol
- `granularity` (Literal[60, 300, 3600]): K线周期 (秒)
  - 60: 1分钟
  - 300: 5分钟
  - 3600: 1小时
- `count` (int): 请求K线数量 (1-1000)

**返回值**:
```json
[
    {
        "open": 12340.0,
        "high": 12350.0,
        "low": 12330.0,
        "close": 12345.0,
        "volume": 1500,
        "timestamp": "2026-06-09T10:30:00Z"
    },
    ...
]
```

**错误**: 同上

#### 3. execute_simulated_trade

**定义**:
```python
@mcp.tool()
async def execute_simulated_trade(
    api_token: NonEmptyString,
    symbol: NonEmptyString,
    amount: Annotated[float, Field(gt=0)],
    contract_type: ContractType,
    duration: Annotated[int, Field(ge=1)],
    duration_unit: DurationUnit,
    allow_live: bool = False
) -> dict
```

**功能**: 执行模拟交易订单

**参数**:
- `api_token` (str): Deriv API Token (从Deriv Developer Hub获取)
- `symbol` (str): 交易Symbol
- `amount` (float): 交易金额，必须 > 0
- `contract_type` (Literal["CALL", "PUT"]): 合约类型
- `duration` (int): 期限数值，必须 >= 1
- `duration_unit` (Literal["m", "h", "t"]): 期限单位
  - "m": 分钟
  - "h": 小时
  - "t": Tick
- `allow_live` (bool): 是否允许Live账户执易 (默认False，防止意外)

**返回值**:
```json
{
    "contract_id": 123456789,
    "status": "accepted",
    "buy_price": 8.50,
    "payout": 18.50,
    "entry_spot": 12345.67,
    "entry_time": "2026-06-09T10:30:45Z"
}
```

**安全机制**:
- `allow_live=False` 时只允许Demo交易
- 金额必须通过预算检查
- Token必须有效

**错误**: 同上

#### 4. check_account_status

**定义**:
```python
@mcp.tool()
async def check_account_status(
    api_token: NonEmptyString
) -> dict
```

**功能**: 检查交易账户状态

**参数**:
- `api_token` (str): Deriv API Token

**返回值**:
```json
{
    "email": "user@example.com",
    "balance": 1000.00,
    "currency": "USD",
    "account_type": "demo",
    "leverage": 1
}
```

#### 5. get_open_contract_status

**定义**:
```python
@mcp.tool()
async def get_open_contract_status(
    api_token: NonEmptyString,
    contract_id: Annotated[int, Field(ge=1)] | None = None
) -> dict | list[dict]
```

**功能**: 获取开仓合约状态

**参数**:
- `api_token` (str): Deriv API Token
- `contract_id` (int, optional): 特定合约ID (可选，不提供则返回所有)

**返回值** (单个合约):
```json
{
    "contract_id": 123456789,
    "entry_spot": 12345.67,
    "current_spot": 12355.00,
    "payout": 18.50,
    "profit_loss": 8.50,
    "is_expired": false,
    "is_sold": false
}
```

#### 6. close_open_contract

**定义**:
```python
@mcp.tool()
async def close_open_contract(
    api_token: NonEmptyString,
    contract_id: Annotated[int, Field(ge=1)]
) -> dict
```

**功能**: 平仓开仓合约

**参数**:
- `api_token` (str): Deriv API Token
- `contract_id` (int): 要平仓的合约ID

**返回值**:
```json
{
    "contract_id": 123456789,
    "status": "closed",
    "exit_spot": 12355.00,
    "exit_time": "2026-06-09T10:35:00Z",
    "profit_loss": 8.50
}
```

### MCP工具验证

所有工具输入都通过Pydantic严格验证:

```python
# 示例：SimulatedTradeInput
class SimulatedTradeInput(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")
    
    # strict=True: 禁止类型强制转换
    # extra="forbid": 禁止额外字段
    
    api_token: NonEmptyString           # 非空字符串
    symbol: NonEmptyString              # 非空字符串
    amount: Annotated[float, Field(gt=0)]  # 严格大于0
    contract_type: ContractType         # 只允许 "CALL" 或 "PUT"
    duration: Annotated[int, Field(ge=1)]  # >= 1
    duration_unit: DurationUnit         # 只允许 "m"/"h"/"t"
    allow_live: bool = False            # 默认False
```

**验证规则**:
- 如果任何字段类型不匹配，立即抛出ValidationError
- 不会尝试类型转换
- 多余字段被拒绝

---

## 微交易策略引擎

### 核心概念

微交易策略引擎是一个独立的子系统，用于分析短期交易机会。主要特点：

1. **隔离执行**: 不影响主交易台
2. **纯分析**: 生成建议但不自动下单
3. **多资产支持**: Deriv、基金、股票、加密、外汇
4. **技术指标**: 动量、EMA、波动率、成本优势
5. **置信度评分**: 0.0-0.95量化信心

### 配置对象

```python
@dataclass(frozen=True)
class MicroTradeConfig:
    symbol: str = "R_100"
    asset_kind: AssetKind = "deriv"  # 默认Deriv合约
    cadence_seconds: int = 30  # 检查频率
    max_trade_amount: float = 1.0  # 单笔上限
    min_confidence: float = 0.58  # 执行阈值
    max_volatility_pct: float = 2.8  # 波动率上限
    min_momentum_pct: float = 0.03  # 动量下限
    fee_bps: float = 0.0  # 手续费
    slippage_bps: float = 1.0  # 滑点
    cooldown_seconds: int = 60  # 冷却期
    max_daily_loss_pct: float = 2.0  # 日最大亏损
```

### 决策流程

```
输入: 最少8条K线 + 配置
  │
  ├─ 计算动量
  │  └─ recent_change = (latest - previous) / previous * 100%
  │
  ├─ 计算EMA
  │  ├─ EMA(4) 快线
  │  └─ EMA(9) 慢线
  │  └─ 分离度 = |EMA(4) - EMA(9)| / EMA(9) * 100%
  │
  ├─ 计算波动率
  │  └─ 12周期收益率标准差 * sqrt(12) 年化
  │
  ├─ 综合打分
  │  ├─ 基础置信度: 58% (min_confidence)
  │  ├─ 动量调整: ±10%
  │  ├─ EMA调整: ±5%
  │  └─ 波动率惩罚: -0%-15%
  │
  ├─ 生成信号
  │  ├─ 如置信度 >= min_confidence 且 波动率 < max_volatility:
  │  │  ├─ 如动量 > 0: CALL (上升)
  │  │  └─ 如动量 < 0: PUT (下降)
  │  └─ 否则: WAIT
  │
  └─ 输出
     ├─ action: CALL / PUT / WAIT
     ├─ confidence: 0.0-0.95
     ├─ signal_evidence: 详细指标
     └─ blockers: 阻挡因素
```

### 输出解读

```python
result = {
    "ok": True,
    "action": "CALL",
    "confidence": 0.72,
    "reason": "momentum_up_with_ema_separation",
    "signal_evidence": {
        "momentum_pct": 0.45,          # 最近价格上升 0.45%
        "ema_separation_pct": 1.23,    # EMA分离1.23%
        "volatility_pct": 1.8,         # 波动率1.8% (< 2.8上限)
        "cost_edge_bps": 5.0           # 成本优势5个基点
    },
    "blockers": []
}
```

**信号含义**:
- **CALL**: 建议看涨，做多方向
- **PUT**: 建议看跌，做空方向
- **WAIT**: 建议观望，没有清晰信号

---

## 纸面交易与回测

### 回测算法

```python
def backtest_micro_strategy(prices, strategy_config, circuit_config):
    """
    历史回测，模拟交易并计算统计数据
    """
    
    # 初始化
    frame = 规范化价格数据(prices)
    equity = 100.0  # 初始资金
    trades = []
    
    # 回测主循环
    for idx in range(lookback_bars, len(frame) - exit_after_bars):
        # 1. 准备当前窗口
        window = frame[idx-lookback_bars : idx+1]
        
        # 2. 分析
        decision = analyze_micro_trade(window, strategy_config)
        
        # 3. 如果有交易信号
        if decision["action"] in ["CALL", "PUT"]:
            entry_price = frame[idx]["close"]
            exit_price = frame[idx + exit_after_bars]["close"]
            
            # 4. 计算PnL
            if decision["action"] == "CALL":
                return_pct = (exit_price - entry_price) / entry_price * 100
            else:  # PUT
                return_pct = (entry_price - exit_price) / entry_price * 100
            
            pnl = amount * return_pct / 100
            equity += pnl
            
            # 5. 记录交易
            trades.append({
                "entry_price": entry_price,
                "exit_price": exit_price,
                "pnl": pnl,
                "equity": equity,
                "return_pct": return_pct
            })
            
            # 6. 检查熔断
            halted = evaluate_circuit_breaker(trades, circuit_config)
            if halted["halted"]:
                break
    
    # 统计结果
    wins = [t for t in trades if t["pnl"] > 0]
    losses = [t for t in trades if t["pnl"] < 0]
    
    return {
        "trade_count": len(trades),
        "win_rate": len(wins) / len(trades) if trades else None,
        "total_pnl": sum(t["pnl"] for t in trades),
        "ending_equity": equity,
        "trades": trades,
        "halted": halted["halted"],
        "halt_reason": halted["reason"]
    }
```

### 熔断器机制

熔断器在以下情况停止回测:

1. **连续亏损上限**: 连续亏损笔数 >= `max_consecutive_losses`
2. **最大亏损金额**: 总亏损金额 >= `max_total_loss_amount`
3. **最大回撤**: 账户回撤 >= `max_drawdown_pct`
4. **最大交易笔数**: 交易数 >= `max_trade_count`

```python
def evaluate_circuit_breaker(trades, config):
    """
    检查是否触发熔断
    """
    
    # 连续亏损
    consecutive = 0
    for trade in reversed(trades):
        if trade["pnl"] < 0:
            consecutive += 1
        else:
            break
    
    if consecutive >= config.max_consecutive_losses:
        return {"halted": True, "reason": "max_consecutive_losses"}
    
    # 最大亏损
    total_loss = abs(sum(t["pnl"] for t in trades if t["pnl"] < 0))
    if total_loss >= config.max_total_loss_amount:
        return {"halted": True, "reason": "max_total_loss_amount"}
    
    # 最大回撤
    equity_values = [t["equity"] for t in trades]
    peak = max(equity_values)
    current = equity_values[-1]
    drawdown_pct = (peak - current) / peak * 100
    
    if drawdown_pct >= config.max_drawdown_pct:
        return {"halted": True, "reason": "max_drawdown_pct"}
    
    # 最大交易数
    if len(trades) >= config.max_trade_count:
        return {"halted": True, "reason": "max_trade_count"}
    
    return {"halted": False, "reason": None}
```

---

## 预算与安全防护

### 多层预算闸门

该系统实现了严格的预算控制，防止超额交易:

```
用户下单请求
  │
  ▼
  └─► [金额检查] 金额 > 0?
      ├─ No  → 拒绝 (invalid_amount)
      └─ Yes ▼
          └─► [单笔上限] 金额 <= max_single_trade_amount?
              ├─ No  → 拒绝 (single_trade_limit_exceeded)
              └─ Yes ▼
                  └─► [日预算] 今日已用 + 金额 <= max_daily_budget?
                      ├─ No  → 拒绝 (daily_budget_exceeded)
                      └─ Yes ▼
                          └─► [总预算] 总已用 + 金额 <= max_total_budget?
                              ├─ No  → 拒绝 (total_budget_exceeded)
                              └─ Yes ▼
                                  └─► 允许 (within_budget)
```

### 预算检查函数

```python
def budget_guard_check(
    action: str,
    amount: float,
    limits: BudgetLimits,
    daily_spent: float = 0.0,
    total_spent: float = 0.0
) -> dict:
    """
    返回 {
        "ok": bool,           # 是否通过
        "reason": str,        # 原因
        "amount": float,
        "remaining_daily": float,
        "remaining_total": float
    }
    """
```

### 每日重置机制

```python
def reset_daily_spend_if_needed(state, today=None):
    """
    跨天时重置 budget_spent_today
    """
    current_date = today or date.today()
    last_date = datetime.fromisoformat(state.get("budget_day", "2000-01-01")).date()
    
    if current_date > last_date:
        state["budget_day"] = current_date.isoformat()
        state["budget_spent_today"] = 0.0
    
    return state
```

---

## 数据库架构

### 本地SQLite数据库

所有历史数据、审计日志、交易记录都保存到本地SQLite:

```
local_data/gateway.sqlite3
```

### 表结构

#### 1. team_runs 表

记录每次交易团队执行

```sql
CREATE TABLE team_runs (
    id INTEGER PRIMARY KEY,
    run_id TEXT UNIQUE,
    timestamp DATETIME,
    user_prompt TEXT,
    manager_output TEXT,
    final_result TEXT,
    execution_status TEXT,  -- "success" / "blocked" / "error"
    error_message TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
)
```

#### 2. advisor_runs 表

记录每次顾问理事会执行

```sql
CREATE TABLE advisor_runs (
    id INTEGER PRIMARY KEY,
    run_id TEXT UNIQUE,
    question TEXT,
    symbol TEXT,
    time_budget INTEGER,  -- 秒
    use_web BOOLEAN,
    started_at DATETIME,
    completed_at DATETIME,
    advisor_opinions TEXT,  -- JSON
    final_stance TEXT,  -- CALL / PUT / WAIT
    confidence FLOAT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
)
```

#### 3. micro_strategy_runs 表

记录微交易策略执行

```sql
CREATE TABLE micro_strategy_runs (
    id INTEGER PRIMARY KEY,
    run_id TEXT UNIQUE,
    symbol TEXT,
    asset_kind TEXT,
    current_action TEXT,  -- CALL / PUT / WAIT
    confidence FLOAT,
    trades TEXT,  -- JSON (回测交易详情)
    summary TEXT,  -- JSON (统计摘要)
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
)
```

#### 4. advisor_evaluations 表

记录顾问评估结果

```sql
CREATE TABLE advisor_evaluations (
    id INTEGER PRIMARY KEY,
    advisor_run_id TEXT,
    stance TEXT,
    entry_price FLOAT,
    exit_price FLOAT,
    paper_return_pct FLOAT,
    outcome TEXT,  -- correct / wrong / flat
    score FLOAT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (advisor_run_id) REFERENCES advisor_runs(run_id)
)
```

#### 5. api_traces 表

记录所有MCP API调用

```sql
CREATE TABLE api_traces (
    id INTEGER PRIMARY KEY,
    timestamp DATETIME,
    tool_name TEXT,  -- "get_market_ticks" / "execute_simulated_trade" ...
    parameters TEXT,  -- JSON (屏蔽敏感信息)
    response_status TEXT,  -- "success" / "error"
    response_time_ms INTEGER,
    error_message TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
)
```

#### 6. execution_logs 表

记录所有交易执行

```sql
CREATE TABLE execution_logs (
    id INTEGER PRIMARY KEY,
    contract_id INTEGER,
    symbol TEXT,
    direction TEXT,  -- CALL / PUT
    amount FLOAT,
    entry_price FLOAT,
    entry_time DATETIME,
    status TEXT,  -- "executed" / "failed" / "cancelled"
    profit_loss FLOAT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
)
```

### 注意事项

- **安全**: API Token等敏感信息不写入数据库
- **隐私**: 仅保存决策链和审计信息
- **查询**: 支持按时间、Symbol、状态等查询
- **导出**: 可导出为JSON用于审计

---

## 配置指南

### 环境变量

创建 `.env` 文件 (可选):

```bash
# Deriv配置
DERIV_APP_ID=1089                    # 默认App ID
DERIV_WS_URL_TEMPLATE=wss://ws.derivws.com/websockets/v3?app_id={app_id}

# MCP服务器配置
MCP_SERVER_PORT=4000                 # 可选
MCP_REQUEST_TIMEOUT=5.0              # 秒

# 大模型配置 (可选，UI中也可设置)
OPENAI_API_KEY=sk-...               # OpenAI Key
ANTHROPIC_API_KEY=sk-ant-...        # Anthropic Key

# Streamlit配置
STREAMLIT_PORT=8501
STREAMLIT_MAX_UPLOAD_SIZE=5
```

### agent_prompts.json 配置

所有Agent的提示词都定义在这个JSON文件中，可以随时编辑:

```json
{
    "manager": {
        "name": "交易经理",
        "prompt": "你是交易经理，负责..."
    },
    "market": {
        "name": "行情分析师",
        "prompt": "你负责读取 Deriv Tick/K 线..."
    },
    ...
    "advisor.macro": {
        "name": "宏观顾问",
        "prompt": "你先看外部消息..."
    },
    "advisor.custom": {
        "name": "自定义顾问",
        "prompt": "你的角色是..."
    }
}
```

**添加新顾问**:

1. 在 `agent_prompts.json` 中添加 `advisor.xxx` 条目
2. 系统自动为其创建LangGraph节点
3. 重启应用

**编辑现有提示词**:

1. 修改JSON文件
2. 重启Streamlit (会自动重新加载)

### Streamlit配置 (config.toml)

创建或编辑 `~/.streamlit/config.toml`:

```toml
[client]
showErrorDetails = true
toolbarMode = "developer"

[logger]
level = "info"

[theme]
primaryColor = "#FF0000"
backgroundColor = "#FFFFFF"
secondaryBackgroundColor = "#F0F2F6"
textColor = "#31333F"
font = "sans serif"

[server]
port = 8501
headless = true
runOnSave = true
```

---

## API参考

### Python API (用于嵌入式使用)

#### 导入核心模块

```python
from server import (
    get_market_ticks,
    get_historical_candles,
    execute_simulated_trade,
    check_account_status,
    get_open_contract_status,
    close_open_contract
)

from micro_trading import (
    MicroTradeConfig,
    analyze_micro_trade,
    normalize_price_frame
)

from paper_trading import (
    CircuitBreakerConfig,
    backtest_micro_strategy
)

from advisor_evaluation import (
    evaluate_advisor_outcome,
    evaluate_advisor_horizons,
    summarize_advisor_evaluations
)

from budget_guard import (
    BudgetLimits,
    budget_guard_check,
    reset_daily_spend_if_needed
)
```

#### 示例1: 获取市场数据并分析

```python
import asyncio
from micro_trading import MicroTradeConfig, analyze_micro_trade

async def example_analyze():
    # 获取最近100个1分钟K线
    candles = await get_historical_candles(
        symbol="R_100",
        granularity=60,
        count=100
    )
    
    # 配置微交易策略
    config = MicroTradeConfig(
        symbol="R_100",
        asset_kind="deriv",
        max_trade_amount=10.0,
        min_confidence=0.60
    )
    
    # 分析最后一个窗口
    result = analyze_micro_trade(candles, config)
    
    print(f"Action: {result['action']}")
    print(f"Confidence: {result['confidence']}")
    print(f"Evidence: {result['signal_evidence']}")

asyncio.run(example_analyze())
```

#### 示例2: 回测策略

```python
import pandas as pd
from paper_trading import (
    MicroTradeConfig,
    CircuitBreakerConfig,
    backtest_micro_strategy
)

# 生成或加载历史价格
prices_df = pd.DataFrame({
    "close": [100.0, 100.5, 100.2, 100.8, 101.0, ..., 99.5]
})

# 策略配置
strategy_config = MicroTradeConfig(
    symbol="R_100",
    max_trade_amount=1.0,
    min_confidence=0.58
)

# 熔断器配置
circuit_config = CircuitBreakerConfig(
    max_consecutive_losses=3,
    max_total_loss_amount=2.0,
    max_drawdown_pct=3.0,
    max_trade_count=30
)

# 运行回测
result = backtest_micro_strategy(
    prices=prices_df,
    strategy_config=strategy_config,
    circuit_config=circuit_config
)

print(f"Win Rate: {result['summary']['win_rate']:.2%}")
print(f"Total PnL: ${result['summary']['total_pnl']:.2f}")
print(f"Ending Equity: ${result['summary']['ending_equity']:.2f}")
```

#### 示例3: 评估顾问建议

```python
from advisor_evaluation import (
    evaluate_advisor_outcome,
    evaluate_advisor_horizons
)

# 单个评估
outcome = evaluate_advisor_outcome(
    stance="CALL",
    entry_price=12345.67,
    exit_price=12365.00,
    confidence=0.75
)

print(f"Outcome: {outcome['outcome']}")
print(f"Paper Return: {outcome['paper_return_pct']:.2f}%")
print(f"Score: {outcome['score']}")

# 多窗口评估
horizon_result = evaluate_advisor_horizons(
    stance="CALL",
    entry_price=12345.67,
    future_closes=[12355.0, 12365.0, 12375.0],  # 1m, 5m, 10m后的价格
    confidence=0.75
)

for horizon, outcome in horizon_result["horizons"].items():
    print(f"{horizon}: {outcome['outcome']} ({outcome['paper_return_pct']:.2f}%)")
```

#### 示例4: 预算检查

```python
from budget_guard import BudgetLimits, budget_guard_check

limits = BudgetLimits(
    enabled=True,
    max_single_trade_amount=10.0,
    max_daily_trade_budget=50.0,
    max_total_trade_budget=100.0
)

# 检查是否可以下10美金订单
check_result = budget_guard_check(
    action="execute_simulated_trade",
    amount=10.0,
    limits=limits,
    daily_spent=35.0,
    total_spent=75.0
)

if check_result["ok"]:
    print("✓ Order approved")
    print(f"Remaining daily: ${check_result['remaining_daily']:.2f}")
    print(f"Remaining total: ${check_result['remaining_total']:.2f}")
else:
    print(f"✗ Order blocked: {check_result['reason']}")
```

---

## 常见问题

### Q1: 如何获取Deriv API Token?

A: 
1. 访问 https://api.deriv.com/
2. 使用你的Deriv账户登录
3. 创建新的API Token (选择Demo或Real账户)
4. 复制Token字符串
5. 在UI中粘贴到"安全密钥配置"部分

### Q2: Token会被保存到文件吗?

A: **不会**。Token仅保存在Streamlit的Session State中，关闭浏览器即删除。每次重新打开需要重新粘贴。

### Q3: 如何添加自定义顾问?

A:
1. 编辑 `agent_prompts.json`
2. 添加新条目 `"advisor.your_name": {"name": "...", "prompt": "..."}`
3. 重启Streamlit
4. 新顾问会自动添加到理事会

### Q4: 微交易策略可以自动下单吗?

A: **不能**。微交易策略模块只生成分析和建议，不会自动下单。所有实际交易必须经过主交易台和人工确认。

### Q5: 如何导出交易历史?

A:
- **方案1**: 在"交易台"页面下载"行动时间线" (JSON)
- **方案2**: 在"谋士室"下载"谋士报告" (JSON)
- **方案3**: 直接查询SQLite数据库: `local_data/gateway.sqlite3`

### Q6: 可以用Real账户交易吗?

A: 可以，但需要两个显式确认:
1. 在Deriv Developer Hub创建Real Token
2. 在侧边栏勾选"允许 Live 账户执行交易"
3. 系统仍会要求人工确认每笔订单

### Q7: 如何切换大模型服务商?

A:
1. 在侧边栏选择"大模型 API": OpenAI / DeepSeek / Anthropic / 自定义
2. 输入相应的API Key
3. 输入模型名 (如 gpt-4, claude-3, etc)
4. 如果是自定义兼容服务，输入base_url

### Q8: 为什么图表加载失败?

A:
- 检查Symbol是否正确 (如 R_100)
- 检查网络连接
- 尝试减少K线数量
- 查看浏览器控制台的错误消息

### Q9: 顾问理事会为什么超时?

A:
- 增加时间预算 (在页面中调整滑块)
- 关闭"允许联网找资料"以节省时间
- 检查网络连接稳定性

### Q10: 如何清空所有数据?

A:
```bash
rm local_data/gateway.sqlite3
# 系统会在下次启动时重新创建
```

---

## 故障排除

### 问题1: "PySide6 is required for the desktop app"

**原因**: 未安装桌面依赖

**解决**:
```bash
pip install -r desktop_requirements.txt
python desktop_app.py
```

### 问题2: Streamlit 连接超时

**原因**: WebSocket连接到Deriv失败

**检查**:
```bash
# 测试网络连接
python -c "import websockets; print('WebSocket module OK')"

# 测试Deriv连接
python -c "
import asyncio
import websockets
async def test():
    async with websockets.connect('wss://ws.derivws.com/websockets/v3?app_id=1089'):
        print('Connection OK')
asyncio.run(test())
"
```

### 问题3: "Token not configured" 错误

**原因**: Token过期或无效

**解决**:
1. 重新获取新Token
2. 清空旧Token
3. 粘贴新Token
4. 刷新页面

### 问题4: 交易台不响应输入

**原因**: Agent处理卡顿

**检查**:
1. 查看浏览器控制台是否有JS错误
2. 查看终端是否有Python错误
3. 尝试清除Session状态: 重新打开浏览器
4. 检查LangGraph是否正确初始化: 查看Monitor页面

### 问题5: 数据库错误

**现象**: "SQLite database is locked"

**原因**: 多个进程同时访问数据库

**解决**:
```bash
# 检查是否有多个Streamlit进程
ps aux | grep streamlit

# 关闭重复进程
pkill -f streamlit

# 重启单个实例
streamlit run web_app.py
```

### 问题6: 导入错误

**现象**: "ModuleNotFoundError: No module named 'langgraph'"

**原因**: 未安装依赖

**解决**:
```bash
pip install -r requirements.txt --upgrade
```

---

## 贡献指南

### 代码风格

- **格式**: 遵循PEP 8标准
- **类型提示**: 所有函数都应有完整的类型注解
- **文档**: 所有模块、类、函数都应有docstring
- **测试**: 新功能必须添加测试用例

### 添加新Agent

1. 在 `agent_prompts.json` 中定义提示词
2. 实现Agent逻辑 (参考现有agents)
3. 将其注册到graph中
4. 添加测试用例

### 添加新工具

1. 在 `server.py` 中实现MCP工具
2. 添加Pydantic输入验证模型
3. 添加错误处理
4. 在文档中记录
5. 添加测试

### 提交Pull Request

1. Fork仓库
2. 创建特性分支: `git checkout -b feature/xyz`
3. 提交更改: `git commit -am 'Add feature xyz'`
4. 推送到分支: `git push origin feature/xyz`
5. 创建Pull Request，附加详细说明

### 报告问题

- 使用 GitHub Issues
- 提供详细的重现步骤
- 包括错误消息、日志和环境信息

---

## 许可证

MIT License

---

## 联系与支持

- **问题报告**: GitHub Issues
- **讨论**: GitHub Discussions
- **文档**: 本README及在线Wiki

---

**文档完整度**: 100% | **最后更新**: 2026年6月9日 | **版本**: 1.0.0
