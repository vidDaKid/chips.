*This page contains example formats for each of the different JSON requests accepted by the
server*

### Ordering 
#### Start Ordering
```json
{"type":"ORDER"}
```

#### Count me in the order
```json
{"type":"COUNT"}
```
---

### Voting
#### Start Vote
```json
{"type":"START_VOTE"}
```

#### Cast Vote
```json
{"type":"VOTE", "voting_param":<ur_vote:bool>}
```
---

### Play
#### Play bet (a check is equal to a bet with `bet_size==0`)
```json
{"type":"PLAY", "play":"bet", "bet_size":<bet_size:int>}
```

### Play fold
```json
{"type":"PLAY", "play":"fold"}
```
