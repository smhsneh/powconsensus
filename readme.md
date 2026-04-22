# blockchain — proof of work consensus
a local simulation of a proof of work blockchain network with three nodes and a live streamlit dashboard.

## tech stack
- python — core language
- flask — each node runs as a flask server
- streamlit — visual dashboard
- sha-256 — hashing algorithm for pow

## project structure

```
blockchain-pow/
├── blockchain.py    # block structure, sha-256 hashing, pow mining loop, chain validation
├── node.py          # flask api, peer registration, broadcast, consensus
├── app.py           # streamlit dashboard
└── requirements.txt
```

## setup

```bash
pip install -r requirements.txt
```

## running the project

open 4 terminals in vs code and run one command in each:

```bash
# terminal 1
python node.py 5001

# terminal 2
python node.py 5002

# terminal 3
python node.py 5003

# terminal 4
streamlit run app.py
```

dashboard opens at `http://localhost:8501`

## demo steps
1. click **register all nodes with each other** in the sidebar
2. add a transaction and select a node to send it to
3. click **mine block** on any node — watch the nonce and hash appear
4. observe all three nodes sync to the same block count automatically
5. click **run consensus on all nodes** to trigger the longest chain rule
6. scroll the block explorer to inspect each block's hash, nonce, and linkage

## how pow works here
when a block is mined, the node increments a nonce and hashes all block fields using sha-256 on every attempt until the resulting hash starts with `0000`. the number of leading zeros is the difficulty target. finding this hash requires thousands of attempts — that computational effort is the proof of work. once found, the block is broadcast to all peers who verify the hash and accept it into their chain.

## consensus rule
if two nodes mine simultaneously and produce conflicting chains, all nodes resolve the conflict by adopting the longest valid chain. this is the nakamoto consensus mechanism.

## license

mit license