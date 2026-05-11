# Core Source Snapshot

Target project directory:

```text
C:\Users\illa9\Downloads\mock_firewall_project\mock_firewall_project
```


# FILE: src\main.py

Target path:

```text
C:\Users\illa9\Downloads\mock_firewall_project\mock_firewall_project\src\main.py
```

```python
from firewall import Firewall
from packet import Packet
from logger import FirewallLogger


def main():
    logger = FirewallLogger("logs/firewall.log")
    firewall = Firewall(rule_file="rules/rules.json", logger=logger)

    packets = [
        Packet(src_ip="10.0.0.2", dst_ip="192.168.1.10", protocol="TCP", src_port=51522, dst_port=80),
        Packet(src_ip="10.0.0.3", dst_ip="192.168.1.10", protocol="TCP", src_port=51523, dst_port=22),
        Packet(src_ip="10.0.0.13", dst_ip="192.168.1.10", protocol="UDP", src_port=53000, dst_port=53),
        Packet(src_ip="10.0.0.4", dst_ip="192.168.1.10", protocol="UDP", src_port=53001, dst_port=53),
    ]

    for packet in packets:
        decision = firewall.inspect(packet)
        print(f"{decision.action}: {packet}")


if __name__ == "__main__":
    main()

```

# FILE: src\firewall.py

Target path:

```text
C:\Users\illa9\Downloads\mock_firewall_project\mock_firewall_project\src\firewall.py
```

```python
from rule_engine import RuleEngine


class Firewall:
    def __init__(self, rule_file, logger):
        self.rule_engine = RuleEngine(rule_file)
        self.logger = logger

    def inspect(self, packet):
        decision = self.rule_engine.evaluate(packet)
        self.logger.log(packet, decision)
        return decision

```

# FILE: src\packet.py

Target path:

```text
C:\Users\illa9\Downloads\mock_firewall_project\mock_firewall_project\src\packet.py
```

```python
from dataclasses import dataclass


@dataclass
class Packet:
    src_ip: str
    dst_ip: str
    protocol: str
    src_port: int
    dst_port: int

    def __str__(self):
        return (
            f"{self.protocol} "
            f"{self.src_ip}:{self.src_port} -> "
            f"{self.dst_ip}:{self.dst_port}"
        )

```

# FILE: src\rule_engine.py

Target path:

```text
C:\Users\illa9\Downloads\mock_firewall_project\mock_firewall_project\src\rule_engine.py
```

```python
import json
from decision import Decision


class RuleEngine:
    def __init__(self, rule_file):
        self.rules = self._load_rules(rule_file)

    def _load_rules(self, rule_file):
        with open(rule_file, "r", encoding="utf-8") as file:
            return json.load(file)

    def evaluate(self, packet):
        for rule in self.rules:
            if self._matches(rule, packet):
                return Decision(
                    action=rule["action"],
                    reason=rule.get("reason", "Matched rule"),
                )

        return Decision(action="ALLOW", reason="No matching rule")

    def _matches(self, rule, packet):
        if "src_ip" in rule and rule["src_ip"] != packet.src_ip:
            return False

        if "dst_ip" in rule and rule["dst_ip"] != packet.dst_ip:
            return False

        if "protocol" in rule and rule["protocol"] != packet.protocol:
            return False

        if "src_port" in rule and rule["src_port"] != packet.src_port:
            return False

        if "dst_port" in rule and rule["dst_port"] != packet.dst_port:
            return False

        return True

```

# FILE: src\logger.py

Target path:

```text
C:\Users\illa9\Downloads\mock_firewall_project\mock_firewall_project\src\logger.py
```

```python
from pathlib import Path
from datetime import datetime


class FirewallLogger:
    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def log(self, packet, decision):
        line = (
            f"{datetime.utcnow().isoformat()}Z "
            f"{decision.action} "
            f"{packet} "
            f"reason={decision.reason}\n"
        )

        with self.path.open("a", encoding="utf-8") as file:
            file.write(line)

```

# FILE: rules\rules.json

Target path:

```text
C:\Users\illa9\Downloads\mock_firewall_project\mock_firewall_project\rules\rules.json
```

```json
[
  {
    "action": "DROP",
    "protocol": "TCP",
    "dst_port": 22,
    "reason": "Block SSH traffic"
  },
  {
    "action": "DROP",
    "src_ip": "10.0.0.13",
    "reason": "Blocked suspicious host"
  },
  {
    "action": "ALLOW",
    "protocol": "TCP",
    "dst_port": 80,
    "reason": "Allow HTTP traffic"
  }
]

```

# FILE: README.md

Target path:

```text
C:\Users\illa9\Downloads\mock_firewall_project\mock_firewall_project\README.md
```

```markdown
# Mock Firewall Project

This is a tiny mock firewall project for testing your agent.

## Run

```bash
python src/main.py
```

## What it does

- Loads rules from `rules/rules.json`
- Creates a few mock packets
- Applies firewall rules
- Prints ALLOW or DROP decisions
- Writes logs to `logs/firewall.log`

## Project flow

```text
src/main.py
→ src/firewall.py
→ src/packet.py
→ src/rule_engine.py
→ src/logger.py
```

```