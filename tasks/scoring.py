"""
Smart Task Analyzer - Priority Scoring Algorithm

This module implements the core priority scoring logic for task analysis.
It supports multiple strategies and handles edge cases robustly.
"""

from datetime import datetime, date
from typing import List, Dict, Any, Set


class TaskScorer:
    """
    Calculates priority scores for tasks based on multiple factors.
    Supports different scoring strategies for flexible prioritization.
    """
    
    def __init__(self, strategy: str = 'smart_balance'):
        """
        Initialize the scorer with a specific strategy.
        
        Args:
            strategy: One of 'smart_balance', 'fastest_wins', 'high_impact', 'deadline_driven'
        """
        self.strategy = strategy
        self.weights = self._get_weights(strategy)
    
    def _get_weights(self, strategy: str) -> Dict[str, float]:
        """
        Get weight distribution for different scoring strategies.
        
        Returns:
            Dictionary with weights for urgency, importance, effort, and dependencies
        """
        strategies = {
            'smart_balance': {
                'urgency': 0.35,
                'importance': 0.30,
                'effort': 0.10,
                'dependencies': 0.25
            },
            'fastest_wins': {
                'urgency': 0.20,
                'importance': 0.20,
                'effort': 0.50,
                'dependencies': 0.10
            },
            'high_impact': {
                'urgency': 0.15,
                'importance': 0.60,
                'effort': 0.05,
                'dependencies': 0.20
            },
            'deadline_driven': {
                'urgency': 0.70,
                'importance': 0.15,
                'effort': 0.05,
                'dependencies': 0.10
            }
        }
        return strategies.get(strategy, strategies['smart_balance'])
    
    def calculate_urgency_score(self, due_date: Any) -> float:
        """
        Calculate urgency score (0-10) based on days until due date.
        
        Args:
            due_date: Date string (YYYY-MM-DD) or date object
            
        Returns:
            Urgency score from 0 (not urgent) to 10 (overdue/very urgent)
        """
        try:
            today = date.today()
            
            # Handle string dates
            if isinstance(due_date, str):
                due_date = datetime.strptime(due_date, '%Y-%m-%d').date()
            
            days_until = (due_date - today).days
            
            # Overdue tasks get maximum urgency
            if days_until < 0:
                # More overdue = higher score (capped at 10)
                return min(10, 10 + abs(days_until) * 0.1)
            elif days_until == 0:  # Due today
                return 9.5
            elif days_until == 1:  # Due tomorrow
                return 9.0
            elif days_until <= 3:  # Due within 3 days
                return 8.0
            elif days_until <= 7:  # Due within a week
                return 6.0
            elif days_until <= 14:  # Due within 2 weeks
                return 4.0
            elif days_until <= 30:  # Due within a month
                return 2.0
            else:  # More than a month away
                return max(0, 2 - (days_until - 30) / 30)
                
        except (ValueError, TypeError, AttributeError) as e:
            # Invalid or missing date - assign medium urgency
            return 5.0
    
    def calculate_importance_score(self, importance: Any) -> float:
        """
        Normalize importance score to 0-10 scale.
        
        Args:
            importance: Integer from 1-10
            
        Returns:
            Normalized importance score
        """
        try:
            importance = float(importance)
            # Clamp between 1 and 10
            return max(1.0, min(10.0, importance))
        except (ValueError, TypeError):
            # Missing or invalid importance - assign medium value
            return 5.0
    
    def calculate_effort_score(self, estimated_hours: Any) -> float:
        """
        Calculate effort score where lower effort = higher score (quick wins).
        
        Args:
            estimated_hours: Hours estimated to complete task
            
        Returns:
            Effort score from 0-10 (higher = less effort required)
        """
        try:
            hours = float(estimated_hours)
            
            # Ensure non-negative
            if hours < 0:
                hours = 0
            
            # Score based on effort brackets
            if hours <= 0.5:  # < 30 minutes
                return 10.0
            elif hours <= 1:  # 30min - 1hr
                return 9.0
            elif hours <= 2:  # 1-2 hours
                return 8.0
            elif hours <= 4:  # 2-4 hours
                return 6.0
            elif hours <= 8:  # 4-8 hours (full day)
                return 4.0
            elif hours <= 16:  # 1-2 days
                return 2.0
            else:  # More than 2 days
                return max(0, 2 - (hours - 16) / 8)
                
        except (ValueError, TypeError):
            # Missing or invalid effort - assign medium value
            return 5.0
    
    def calculate_dependency_score(self, task_id: Any, all_tasks: List[Dict]) -> float:
        """
        Calculate dependency score based on how many tasks depend on this one.
        Tasks that block others should be prioritized.
        
        Args:
            task_id: ID of the current task
            all_tasks: List of all tasks
            
        Returns:
            Dependency score from 0-10
        """
        try:
            # Count how many tasks list this task as a dependency
            dependent_count = 0
            for task in all_tasks:
                dependencies = task.get('dependencies', [])
                if task_id in dependencies:
                    dependent_count += 1
            
            # Score based on number of dependent tasks
            # Each dependent task adds points (capped at 10)
            if dependent_count == 0:
                return 0.0
            elif dependent_count == 1:
                return 4.0
            elif dependent_count == 2:
                return 7.0
            else:
                return min(10.0, 7.0 + (dependent_count - 2) * 1.5)
                
        except Exception:
            return 0.0
    
    def score_task(self, task: Dict[str, Any], all_tasks: List[Dict]) -> Dict[str, Any]:
        """
        Calculate the final priority score for a task.
        
        Args:
            task: Task dictionary with title, due_date, estimated_hours, importance, dependencies
            all_tasks: List of all tasks (needed for dependency calculation)
            
        Returns:
            Dictionary with score components and final score
        """
        try:
            # Calculate individual component scores
            urgency = self.calculate_urgency_score(task.get('due_date'))
            importance = self.calculate_importance_score(task.get('importance'))
            effort = self.calculate_effort_score(task.get('estimated_hours'))
            dependencies = self.calculate_dependency_score(
                task.get('id', task.get('title')), 
                all_tasks
            )
            
            # Calculate weighted final score
            final_score = (
                self.weights['urgency'] * urgency +
                self.weights['importance'] * importance +
                self.weights['effort'] * effort +
                self.weights['dependencies'] * dependencies
            )
            
            return {
                'score': round(final_score, 2),
                'components': {
                    'urgency': round(urgency, 2),
                    'importance': round(importance, 2),
                    'effort': round(effort, 2),
                    'dependencies': round(dependencies, 2)
                }
            }
            
        except Exception as e:
            # If anything fails, return a default low score
            return {
                'score': 0.0,
                'components': {
                    'urgency': 0.0,
                    'importance': 0.0,
                    'effort': 0.0,
                    'dependencies': 0.0
                },
                'error': str(e)
            }
    
    def detect_circular_dependencies(self, tasks: List[Dict]) -> List[Set[Any]]:
        """
        Detect circular dependencies in task list using depth-first search.
        
        Args:
            tasks: List of tasks with dependencies
            
        Returns:
            List of sets containing task IDs in circular dependency chains
        """
        # Build adjacency list
        graph = {}
        for task in tasks:
            task_id = task.get('id', task.get('title'))
            graph[task_id] = task.get('dependencies', [])
        
        visited = set()
        rec_stack = set()
        cycles = []
        
        def dfs(node: Any, path: List[Any]) -> None:
            """Depth-first search to detect cycles"""
            visited.add(node)
            rec_stack.add(node)
            path.append(node)
            
            for neighbor in graph.get(node, []):
                if neighbor not in visited:
                    dfs(neighbor, path.copy())
                elif neighbor in rec_stack:
                    # Found a cycle
                    cycle_start = path.index(neighbor)
                    cycle = set(path[cycle_start:] + [neighbor])
                    if cycle not in cycles:
                        cycles.append(cycle)
            
            rec_stack.remove(node)
        
        # Check all nodes
        for task in tasks:
            task_id = task.get('id', task.get('title'))
            if task_id not in visited:
                dfs(task_id, [])
        
        return cycles
    
    def generate_explanation(self, task: Dict, score_data: Dict) -> str:
        """
        Generate human-readable explanation for task priority.
        
        Args:
            task: Task dictionary
            score_data: Score data with components
            
        Returns:
            Explanation string
        """
        components = score_data.get('components', {})
        reasons = []
        
        # Check urgency
        if components.get('urgency', 0) >= 8:
            reasons.append("⚠️ Due very soon or overdue")
        elif components.get('urgency', 0) >= 6:
            reasons.append("📅 Due within a week")
        
        # Check importance
        if components.get('importance', 0) >= 8:
            reasons.append("⭐ High importance")
        elif components.get('importance', 0) >= 6:
            reasons.append("🔹 Medium-high importance")
        
        # Check effort
        if components.get('effort', 0) >= 8:
            reasons.append("⚡ Quick win (low effort)")
        
        # Check dependencies
        if components.get('dependencies', 0) >= 7:
            reasons.append("🔗 Multiple tasks depend on this")
        elif components.get('dependencies', 0) >= 4:
            reasons.append("🔗 Blocks other tasks")
        
        # Strategy-specific reasons
        if self.strategy == 'fastest_wins' and components.get('effort', 0) >= 7:
            reasons.append("🎯 Prioritized as quick win")
        elif self.strategy == 'high_impact' and components.get('importance', 0) >= 7:
            reasons.append("🎯 Prioritized for high impact")
        elif self.strategy == 'deadline_driven' and components.get('urgency', 0) >= 7:
            reasons.append("🎯 Prioritized by deadline")
        
        if not reasons:
            return "📊 Balanced priority across all factors"
        
        return " • ".join(reasons)
