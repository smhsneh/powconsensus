import streamlit as st
import requests
import time

st.set_page_config(
    page_title="blockchain pow demo",
    layout="wide"
)

st.title("blockchain — proof of work consensus")
st.caption("a live demo of pow mining and consensus across multiple nodes")

NODES = {
    "node 1": "http://localhost:5001",
    "node 2": "http://localhost:5002",
    "node 3": "http://localhost:5003",
}


# ── helpers ──────────────────────────────────────────────────

def get_chain(node_url):
    try:
        r = requests.get(f"{node_url}/chain", timeout=3)
        if r.status_code == 200:
            return r.json()
    except requests.exceptions.RequestException:
        pass
    return None


def mine_block(node_url):
    try:
        r = requests.get(f"{node_url}/mine", timeout=30)
        return r.json(), r.status_code
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}, 500


def add_transaction(node_url, transaction):
    try:
        r = requests.post(
            f"{node_url}/transactions/new",
            json={"transaction": transaction},
            timeout=3
        )
        return r.json(), r.status_code
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}, 500


def register_peers(node_url, peers):
    try:
        r = requests.post(
            f"{node_url}/nodes/register",
            json={"nodes": peers},
            timeout=3
        )
        return r.json(), r.status_code
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}, 500


def resolve_consensus(node_url):
    try:
        r = requests.get(f"{node_url}/nodes/resolve", timeout=10)
        return r.json(), r.status_code
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}, 500


# ── sidebar ──────────────────────────────────────────────────

with st.sidebar:
    st.header("controls")

    st.subheader("register peers")
    if st.button("register all nodes with each other", use_container_width=True):
        for name, url in NODES.items():
            peers = [
                addr.replace("http://", "")
                for n, addr in NODES.items()
                if n != name
            ]
            result, code = register_peers(url, peers)
            if code == 201:
                st.success(f"{name}: peers registered")
            else:
                st.error(f"{name}: {result.get('error', 'failed')}")

    st.divider()

    st.subheader("add transaction")
    selected_node = st.selectbox("send to node", list(NODES.keys()))
    tx_input = st.text_input("transaction", placeholder="alice sends 10 to bob")
    if st.button("add transaction", use_container_width=True):
        if tx_input:
            result, code = add_transaction(NODES[selected_node], tx_input)
            if code == 201:
                st.success("transaction added to pending pool")
            else:
                st.error(result.get("error", "failed"))
        else:
            st.warning("enter a transaction first")

    st.divider()

    st.subheader("consensus")
    if st.button("run consensus on all nodes", use_container_width=True):
        for name, url in NODES.items():
            result, code = resolve_consensus(url)
            if code == 200:
                st.info(f"{name}: {result.get('message', '')}")
            else:
                st.error(f"{name}: failed")

    st.divider()

    auto_refresh = st.toggle("auto refresh (5s)", value=False)


# ── node status row ───────────────────────────────────────────

st.subheader("node status")
cols = st.columns(3)

for i, (name, url) in enumerate(NODES.items()):
    with cols[i]:
        data = get_chain(url)

        if data is None:
            st.error(f"{name} — offline")
            st.caption(url)
            continue

        chain_len = data.get("length", 0)
        is_valid = data.get("is_valid", False)
        pending = data.get("pending_transactions", [])

        status_color = "normal" if is_valid else "inverse"

        st.metric(
            label=f"{name} — {url.split('localhost:')[1]}",
            value=f"{chain_len} blocks",
            delta="valid chain" if is_valid else "invalid chain",
            delta_color="normal" if is_valid else "inverse"
        )

        st.caption(f"pending transactions: {len(pending)}")

        if pending:
            with st.expander("view pending"):
                for tx in pending:
                    st.text(f"• {tx}")

        if st.button(f"mine block on {name}", key=f"mine_{name}", use_container_width=True):
            with st.spinner(f"mining on {name}... this may take a moment"):
                result, code = mine_block(url)
            if code == 200:
                block = result.get("block", {})
                st.success(f"block mined! nonce: {block.get('nonce', '?')}")
                st.code(f"hash: {block.get('hash', '')[:32]}...", language=None)
                st.rerun()
            else:
                st.error(result.get("message", "mining failed"))


# ── block explorer ────────────────────────────────────────────

st.divider()
st.subheader("block explorer")

explorer_node = st.selectbox(
    "view chain from",
    list(NODES.keys()),
    key="explorer_select"
)

chain_data = get_chain(NODES[explorer_node])

if chain_data is None:
    st.error(f"cannot connect to {explorer_node}")
else:
    chain = chain_data.get("chain", [])
    is_valid = chain_data.get("is_valid", True)

    if not is_valid:
        st.error("chain integrity check failed — tampered block detected")
    else:
        st.success("chain is valid")

    for block in reversed(chain):
        index = block.get("index", "?")
        nonce = block.get("nonce", "?")
        bhash = block.get("hash", "")
        prev_hash = block.get("previous_hash", "")
        transactions = block.get("transactions", [])
        timestamp = block.get("timestamp", 0)

        valid_block = bhash.startswith("0" * 4)
        border_color = "green" if valid_block else "red"

        with st.container(border=True):
            c1, c2 = st.columns([1, 3])

            with c1:
                st.markdown(f"### block {index}")
                st.caption(f"nonce: `{nonce}`")
                st.caption(
                    f"mined: {time.strftime('%H:%M:%S', time.localtime(timestamp))}"
                )

            with c2:
                st.code(f"hash:      {bhash}", language=None)
                st.code(f"prev hash: {prev_hash}", language=None)
                with st.expander("transactions"):
                    for tx in transactions:
                        st.text(f"• {tx}")


# ── auto refresh ─────────────────────────────────────────────

if auto_refresh:
    time.sleep(5)
    st.rerun()