"""
Unit Tests for Smart Task Analyzer

Tests the scoring algorithm and edge case handling.
"""

from django.test import TestCase
from datetime import date, timedelta
from .scoring import TaskScorer


class TaskScorerTests(TestCase):
    """Test cases for the TaskScorer class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.scorer = TaskScorer(strategy='smart_balance')
        self.today = date.today()
    
    # Test 1: Urgency Calculation
    def test_overdue_task_gets_maximum_urgency(self):
        """Test that overdue tasks receive maximum urgency score"""
        past_date = (self.today - timedelta(days=5)).strftime('%Y-%m-%d')
        score = self.scorer.calculate_urgency_score(past_date)
        self.assertGreaterEqual(score, 10.0, "Overdue task should have urgency >= 10")
    
    def test_task_due_today_high_urgency(self):
        """Test that tasks due today get high urgency"""
        today_str = self.today.strftime('%Y-%m-%d')
        score = self.scorer.calculate_urgency_score(today_str)
        self.assertGreaterEqual(score, 9.0, "Task due today should have urgency >= 9")
    
    def test_future_task_lower_urgency(self):
        """Test that tasks far in future have lower urgency"""
        future_date = (self.today + timedelta(days=60)).strftime('%Y-%m-%d')
        score = self.scorer.calculate_urgency_score(future_date)
        self.assertLess(score, 5.0, "Task 2 months away should have low urgency")
    
    # Test 2: Effort Calculation
    def test_low_effort_task_high_score(self):
        """Test that low-effort tasks get high effort scores (quick wins)"""
        score = self.scorer.calculate_effort_score(0.5)
        self.assertGreaterEqual(score, 9.0, "30-minute task should have high effort score")
    
    def test_high_effort_task_low_score(self):
        """Test that high-effort tasks get lower scores"""
        score = self.scorer.calculate_effort_score(20)
        self.assertLessEqual(score, 2.0, "20-hour task should have low effort score")
    
    def test_negative_effort_handled(self):
        """Test that negative effort is handled gracefully"""
        score = self.scorer.calculate_effort_score(-5)
        self.assertGreaterEqual(score, 0, "Negative effort should not crash")
    
    # Test 3: Importance Calculation
    def test_importance_within_range(self):
        """Test that importance scores stay within valid range"""
        for importance in [1, 5, 10]:
            score = self.scorer.calculate_importance_score(importance)
            self.assertGreaterEqual(score, 1.0)
            self.assertLessEqual(score, 10.0)
    
    def test_importance_handles_invalid_input(self):
        """Test that invalid importance returns default value"""
        score = self.scorer.calculate_importance_score("invalid")
        self.assertEqual(score, 5.0, "Invalid importance should return default 5.0")
    
    # Test 4: Dependency Calculation
    def test_task_with_dependents_scores_higher(self):
        """Test that tasks with dependents get higher scores"""
        tasks = [
            {'id': 1, 'dependencies': [2]},
            {'id': 2, 'dependencies': []},
            {'id': 3, 'dependencies': [2]}
        ]
        score = self.scorer.calculate_dependency_score(2, tasks)
        self.assertGreater(score, 0, "Task with dependents should score > 0")
    
    def test_task_without_dependents_scores_zero(self):
        """Test that tasks with no dependents get zero dependency score"""
        tasks = [
            {'id': 1, 'dependencies': []},
            {'id': 2, 'dependencies': []}
        ]
        score = self.scorer.calculate_dependency_score(1, tasks)
        self.assertEqual(score, 0.0, "Task with no dependents should score 0")
    
    # Test 5: Complete Task Scoring
    def test_complete_task_scoring(self):
        """Test that a complete task can be scored without errors"""
        task = {
            'id': 1,
            'title': 'Test Task',
            'due_date': self.today.strftime('%Y-%m-%d'),
            'estimated_hours': 2,
            'importance': 8,
            'dependencies': []
        }
        result = self.scorer.score_task(task, [task])
        
        self.assertIn('score', result)
        self.assertIn('components', result)
        self.assertGreater(result['score'], 0)
    
    def test_task_with_missing_fields_scores_without_crash(self):
        """Test that tasks with missing fields don't crash the scorer"""
        incomplete_task = {
            'id': 1,
            'title': 'Incomplete Task'
            # Missing due_date, estimated_hours, importance
        }
        result = self.scorer.score_task(incomplete_task, [incomplete_task])
        
        self.assertIn('score', result)
        self.assertGreaterEqual(result['score'], 0)
    
    # Test 6: Circular Dependency Detection
    def test_detect_simple_circular_dependency(self):
        """Test detection of simple circular dependencies"""
        tasks = [
            {'id': 1, 'dependencies': [2]},
            {'id': 2, 'dependencies': [1]}
        ]
        cycles = self.scorer.detect_circular_dependencies(tasks)
        self.assertGreater(len(cycles), 0, "Should detect circular dependency")
    
    def test_detect_no_circular_dependencies(self):
        """Test that linear dependencies don't trigger false positives"""
        tasks = [
            {'id': 1, 'dependencies': []},
            {'id': 2, 'dependencies': [1]},
            {'id': 3, 'dependencies': [2]}
        ]
        cycles = self.scorer.detect_circular_dependencies(tasks)
        self.assertEqual(len(cycles), 0, "Should not detect cycles in linear chain")
    
    # Test 7: Different Strategies
    def test_fastest_wins_strategy(self):
        """Test that 'fastest_wins' strategy prioritizes low-effort tasks"""
        scorer = TaskScorer(strategy='fastest_wins')
        self.assertGreater(scorer.weights['effort'], 0.4, 
                          "Fastest wins should weight effort highly")
    
    def test_high_impact_strategy(self):
        """Test that 'high_impact' strategy prioritizes importance"""
        scorer = TaskScorer(strategy='high_impact')
        self.assertGreater(scorer.weights['importance'], 0.5,
                          "High impact should weight importance highly")
    
    def test_deadline_driven_strategy(self):
        """Test that 'deadline_driven' strategy prioritizes urgency"""
        scorer = TaskScorer(strategy='deadline_driven')
        self.assertGreater(scorer.weights['urgency'], 0.6,
                          "Deadline driven should weight urgency highly")
    
    # Test 8: Edge Cases
    def test_empty_task_list(self):
        """Test scoring works with empty task list"""
        task = {
            'id': 1,
            'title': 'Solo Task',
            'due_date': self.today.strftime('%Y-%m-%d'),
            'estimated_hours': 1,
            'importance': 5,
            'dependencies': []
        }
        result = self.scorer.score_task(task, [])
        self.assertIn('score', result)
    
    def test_task_with_invalid_date_format(self):
        """Test that invalid date format is handled gracefully"""
        score = self.scorer.calculate_urgency_score("invalid-date")
        self.assertEqual(score, 5.0, "Invalid date should return default score")
    
    def test_explanation_generation(self):
        """Test that explanations are generated for scored tasks"""
        task = {
            'id': 1,
            'title': 'Test',
            'due_date': self.today.strftime('%Y-%m-%d'),
            'estimated_hours': 1,
            'importance': 9,
            'dependencies': []
        }
        score_data = self.scorer.score_task(task, [task])
        explanation = self.scorer.generate_explanation(task, score_data)
        
        self.assertIsInstance(explanation, str)
        self.assertGreater(len(explanation), 0, "Explanation should not be empty")
    
    # Test 9: Score Boundaries
    def test_scores_within_valid_range(self):
        """Test that final scores stay within reasonable range (0-10)"""
        tasks = [
            {
                'id': i,
                'title': f'Task {i}',
                'due_date': (self.today + timedelta(days=i)).strftime('%Y-%m-%d'),
                'estimated_hours': i,
                'importance': min(10, i),
                'dependencies': []
            }
            for i in range(1, 11)
        ]
        
        for task in tasks:
            result = self.scorer.score_task(task, tasks)
            self.assertGreaterEqual(result['score'], 0)
            self.assertLessEqual(result['score'], 11, 
                                "Score should not exceed reasonable maximum")
    
    # Test 10: Complex Dependency Chains
    def test_complex_dependency_chain(self):
        """Test scoring with complex dependency relationships"""
        tasks = [
            {'id': 1, 'dependencies': []},
            {'id': 2, 'dependencies': [1]},
            {'id': 3, 'dependencies': [1]},
            {'id': 4, 'dependencies': [2, 3]},
            {'id': 5, 'dependencies': [4]}
        ]
        
        # Task 1 blocks the most tasks (transitively)
        score_1 = self.scorer.calculate_dependency_score(1, tasks)
        score_5 = self.scorer.calculate_dependency_score(5, tasks)
        
        self.assertGreater(score_1, score_5, 
                          "Task blocking more tasks should score higher")


class TaskScorerIntegrationTests(TestCase):
    """Integration tests for complete scoring workflow"""
    
    def test_realistic_task_scenario(self):
        """Test scoring a realistic set of tasks"""
        scorer = TaskScorer(strategy='smart_balance')
        today = date.today()
        
        tasks = [
            {
                'id': 1,
                'title': 'Critical Bug Fix',
                'due_date': today.strftime('%Y-%m-%d'),
                'estimated_hours': 2,
                'importance': 10,
                'dependencies': []
            },
            {
                'id': 2,
                'title': 'Documentation Update',
                'due_date': (today + timedelta(days=30)).strftime('%Y-%m-%d'),
                'estimated_hours': 1,
                'importance': 4,
                'dependencies': []
            },
            {
                'id': 3,
                'title': 'Infrastructure Setup',
                'due_date': (today + timedelta(days=7)).strftime('%Y-%m-%d'),
                'estimated_hours': 8,
                'importance': 9,
                'dependencies': []
            }
        ]
        
        scored_tasks = []
        for task in tasks:
            result = scorer.score_task(task, tasks)
            task['score'] = result['score']
            scored_tasks.append(task)
        
        # Sort by score
        sorted_tasks = sorted(scored_tasks, key=lambda x: x['score'], reverse=True)
        
        # Critical bug should be first (high importance, due today, low effort)
        self.assertEqual(sorted_tasks[0]['id'], 1, 
                        "Critical bug due today should be highest priority")
