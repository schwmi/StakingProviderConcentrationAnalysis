# Rated.networds

## Supported Networks

### Polygon (ETH-dependent)
Polygon relies on Ethereum for settlement and ecosystem liquidity, while operating its own validator set for scalability. From a staking perspective, it inherits Ethereum alignment but introduces additional validator and bridge trust assumptions.

### Ethereum (Base Layer)
Ethereum has the largest and most decentralized PoS validator set, with high economic security driven by ETH staking. It acts as the primary security and settlement layer that many other networks and protocols depend on.

### Solana (ETH-independent)
Solana runs a single high-performance validator set optimized for throughput and low latency. Validator participation is hardware-intensive, leading to higher operational concentration compared to modular PoS systems.

### Avalanche (ETH-independent)
Avalanche uses a flexible validator model where subnets can define their own staking and validation rules. This enables tailored security models but fragments stake and validator attention across subnetworks.

### EigenLayer (ETH-dependent)
EigenLayer directly depends on Ethereum validators by allowing restaked ETH to secure additional services. It increases capital efficiency but creates correlated slashing and concentration risks tied to Ethereum’s validator set.

### Polkadot (ETH-independent)
Polkadot centralizes validation at the relay chain, with nominators delegating stake to a limited validator set. This pooled security model reduces bootstrapping risk but concentrates validation power at the relay layer.

### Cosmos Hub (ETH-independent)
Cosmos Hub operates a sovereign PoS validator set and does not provide shared security by default. Validator concentration varies significantly across Cosmos chains, making security highly heterogeneous.

### Cardano (ETH-independent)
Cardano emphasizes stake pool decentralization through protocol incentives that cap rewards per operator. This leads to a broad validator distribution but slower parameter and governance changes.

### Babylon (ETH-independent, BTC-anchored)
Babylon introduces Bitcoin-backed security guarantees into PoS systems without wrapping BTC. It shifts staking security assumptions from native tokens toward Bitcoin finality and time-lock economics.

### Celestia (ETH-independent)
Celestia provides consensus and data availability with a minimal validator role focused on sampling and verification. This lowers validator complexity while enabling many rollups to share a single security layer.

## Interesting endpoints:

### Host distributions:

Information on which serivce providers the validator nodes are hosted: /v1/eth/hostDistributions

