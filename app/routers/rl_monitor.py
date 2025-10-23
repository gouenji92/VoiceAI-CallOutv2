"""
RL Threshold Tuner - Real-time Monitoring Dashboard
API endpoint để monitor RL state trong production
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List, Optional
from datetime import datetime
import json
from pathlib import Path

from app.services.rl_threshold_tuner import get_tuner

router = APIRouter(tags=["RL Monitoring"])

@router.get("/status")
async def get_rl_status() -> Dict[str, Any]:
    """
    Get current RL tuner status
    
    Returns:
        - epsilon: Current exploration rate
        - total_updates: Total feedback updates received
        - exploration_ratio: Percentage of exploration vs exploitation
        - last_updated: Timestamp of last update
    """
    try:
        tuner = get_tuner()
        
        total_exploration = sum(state.exploration_count for state in tuner.states.values())
        total_exploitation = sum(state.exploitation_count for state in tuner.states.values())
        total_actions = total_exploration + total_exploitation
        
        return {
            "epsilon": round(tuner.epsilon, 4),
            "total_updates": total_actions,
            "exploration_count": total_exploration,
            "exploitation_count": total_exploitation,
            "exploration_ratio": round(total_exploration / max(total_actions, 1), 4),
            "num_intents": len(tuner.states),
            "arms_per_intent": len(tuner.threshold_values),
            "threshold_range": [float(min(tuner.threshold_values)), float(max(tuner.threshold_values))],
            "epsilon_decay": tuner.epsilon_decay,
            "epsilon_min": getattr(tuner, 'min_epsilon', None),
            "last_updated": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting RL status: {str(e)}")

@router.get("/thresholds")
async def get_best_thresholds() -> Dict[str, float]:
    """
    Get current best threshold for each intent
    
    Returns:
        Dict mapping intent -> best threshold value
    """
    tuner = get_tuner()
    return tuner.get_best_thresholds()

@router.get("/intent/{intent_name}")
async def get_intent_details(intent_name: str) -> Dict[str, Any]:
    """
    Get detailed statistics for a specific intent
    
    Args:
        intent_name: Name of the intent (e.g., 'dat_lich')
    
    Returns:
        Detailed arm statistics, best threshold, performance metrics
    """
    tuner = get_tuner()
    
    if intent_name not in tuner.states:
        raise HTTPException(status_code=404, detail=f"Intent '{intent_name}' not found")
    
    state = tuner.states[intent_name]
    
    # Best arm
    best_arm = max(state.arms, key=lambda a: a.total_reward / max(a.pulls, 1))
    
    # All arms sorted by average reward
    arms_data = []
    for arm in sorted(state.arms, key=lambda a: a.threshold):
        avg_reward = arm.total_reward / max(arm.pulls, 1)
        arms_data.append({
            "threshold": round(arm.threshold, 3),
            "pulls": arm.pulls,
            "total_reward": round(arm.total_reward, 2),
            "avg_reward": round(avg_reward, 4),
            "is_best": arm.threshold == best_arm.threshold
        })
    
    return {
        "intent": intent_name,
        "best_threshold": round(best_arm.threshold, 3),
        "best_avg_reward": round(best_arm.total_reward / max(best_arm.pulls, 1), 4),
        "total_pulls": sum(a.pulls for a in state.arms),
        "exploration_count": state.exploration_count,
        "exploitation_count": state.exploitation_count,
        "arms": arms_data
    }

@router.get("/convergence")
async def check_convergence() -> Dict[str, Any]:
    """
    Check if RL system has converged (stable thresholds)
    
    Returns:
        Convergence metrics and recommendations
    """
    tuner = get_tuner()
    
    convergence_data = {}
    for intent, state in tuner.states.items():
        total_pulls = sum(a.pulls for a in state.arms)
        if total_pulls == 0:
            convergence_data[intent] = {
                "converged": False,
                "reason": "No data yet",
                "confidence": 0.0
            }
            continue
        
        # Find best arm
        best_arm = max(state.arms, key=lambda a: a.total_reward / max(a.pulls, 1))
        best_pulls = best_arm.pulls
        
        # Convergence heuristic: best arm has >30% of total pulls
        convergence_ratio = best_pulls / total_pulls
        converged = convergence_ratio > 0.3 and total_pulls > 20
        
        convergence_data[intent] = {
            "converged": converged,
            "best_threshold": round(best_arm.threshold, 3),
            "best_arm_pulls": best_pulls,
            "total_pulls": total_pulls,
            "convergence_ratio": round(convergence_ratio, 4),
            "confidence": round(min(convergence_ratio * 2, 1.0), 4)  # 0-1 scale
        }
    
    overall_converged = sum(1 for v in convergence_data.values() if v.get("converged", False))
    
    return {
        "overall_convergence": round(overall_converged / len(convergence_data), 4),
        "converged_intents": overall_converged,
        "total_intents": len(convergence_data),
        "epsilon": round(tuner.epsilon, 4),
        "recommendation": (
            "RL system has converged - thresholds are stable"
            if overall_converged / len(convergence_data) > 0.7
            else "Continue collecting feedback - more data needed"
        ),
        "intents": convergence_data
    }

@router.get("/performance")
async def get_performance_metrics() -> Dict[str, Any]:
    """
    Get overall RL performance metrics
    
    Returns:
        Average rewards, success rates, exploration stats
    """
    tuner = get_tuner()
    
    metrics = {
        "epsilon": round(tuner.epsilon, 4),
        "intents": {}
    }
    
    for intent, state in tuner.states.items():
        total_pulls = sum(a.pulls for a in state.arms)
        total_reward = sum(a.total_reward for a in state.arms)
        
        if total_pulls > 0:
            avg_reward = total_reward / total_pulls
            best_arm = max(state.arms, key=lambda a: a.total_reward / max(a.pulls, 1))
            worst_arm = min(state.arms, key=lambda a: a.total_reward / max(a.pulls, 1))
            
            metrics["intents"][intent] = {
                "total_pulls": total_pulls,
                "avg_reward": round(avg_reward, 4),
                "best_threshold": round(best_arm.threshold, 3),
                "best_avg_reward": round(best_arm.total_reward / max(best_arm.pulls, 1), 4),
                "worst_threshold": round(worst_arm.threshold, 3),
                "worst_avg_reward": round(worst_arm.total_reward / max(worst_arm.pulls, 1), 4),
                "explored": state.exploration_count,
                "exploited": state.exploitation_count
            }
        else:
            metrics["intents"][intent] = {
                "total_pulls": 0,
                "avg_reward": 0.0,
                "note": "No data yet"
            }
    
    # Overall stats
    all_intents = [m for m in metrics["intents"].values() if "avg_reward" in m and m["total_pulls"] > 0]
    if all_intents:
        metrics["overall"] = {
            "avg_reward": round(sum(m["avg_reward"] for m in all_intents) / len(all_intents), 4),
            "total_pulls": sum(m["total_pulls"] for m in all_intents),
            "avg_exploration_rate": round(
                sum(m["explored"] / max(m["explored"] + m["exploited"], 1) for m in all_intents if "explored" in m) / len(all_intents),
                4
            )
        }
    
    return metrics

@router.get("/export")
async def export_state() -> Dict[str, Any]:
    """
    Export complete RL state for backup/analysis
    
    Returns:
        Full RL tuner state as JSON
    """
    tuner = get_tuner()
    
    state_file = Path("models/rl_threshold_state.json")
    if state_file.exists():
        with open(state_file, 'r', encoding='utf-8') as f:
            state_data = json.load(f)
        return {
            "exported_at": datetime.now().isoformat(),
            "state_file": str(state_file),
            "state": state_data
        }
    else:
        raise HTTPException(status_code=404, detail="RL state file not found")

@router.post("/reset")
async def reset_rl_state(confirm: bool = False) -> Dict[str, str]:
    """
    Reset RL state (DANGEROUS - requires confirmation)
    
    Args:
        confirm: Must be True to execute reset
    
    Returns:
        Status message
    """
    if not confirm:
        raise HTTPException(
            status_code=400,
            detail="Reset requires confirmation. Set confirm=True to proceed."
        )
    
    tuner = get_tuner()
    
    # Backup current state
    backup_file = Path(f"models/rl_state_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
    tuner.save_state(str(backup_file))
    
    # Reset state
    tuner.__init__(
        intents=list(tuner.states.keys()),
        threshold_values=tuner.threshold_values,
        epsilon=0.15,
        epsilon_decay=0.995,
        epsilon_min=0.05
    )
    
    return {
        "status": "RL state reset successfully",
        "backup_saved": str(backup_file),
        "new_epsilon": tuner.epsilon
    }
