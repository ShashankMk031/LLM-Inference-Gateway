from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from math import inf

@dataclass
class ProviderMetrics:
    name : str
    healthy: bool
    avg_latency_ms : float
    cost_per_1k : float

class ModelRouter:
    # Pure provider selection logic

    LATENCY_WEIGHT = 0.6 # 60% latency priority
    COST_WEIGHT = 0.4    # 40% cost priority

    def __init__(self, providers: List[ProviderMetrics]):
        self.providers = providers 
    
    def select_provider(
        self,
        auto: bool = False,
        preferred: Optional[str] = None
    ) -> str:
        # select best provider by scoring

        # Preferred model 
        if preferred:
            healthy_pref = next((p for p in self.providers if p.name == preferred and p.healthy), None)
            if healthy_pref:
                return preferred
        
        if not auto: 
            raise ValueError("Must specify model or auto = True")

        # Auto: score healthy providers
        candidates = [p for p in self.providers if p.healthy] 
        if not candidates:
            raise ValueError("No healthy providers available")
        
        # Weighted score : Lower = better
        scored = [] 
        for p in candidates:
            # Normalize : latency / 100 + cost * 1000 ( relative scales)
            latency_score = p.avg_latency_ms / 100.0
            cost_score = p.cost_per_1k * 1000.0
            total_score = (latency_score * self.LATENCY_WEIGHT + cost_score * self.COST_WEIGHT)
            scored.append((total_score, p.name))

        scored.sort() # Lowest score first
        return scored[0][1] # Best provider name
# Global singleton (config driven) 
PROVIDER_METRICS = [ 
    ProviderMetrics("openai", True, 250, 0.375),
    ProviderMetrics("gemini", True, 180, 0.1875),
    ProviderMetrics("mock", True, 200, 0.0),
]

router = ModelRouter(PROVIDER_METRICS)