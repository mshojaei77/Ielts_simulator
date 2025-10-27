"""Grading system for IELTS test sections."""

import json
import os
from typing import Dict, List, Tuple, Any, Optional


class IELTSGrader:
    """Orchestrate the grading process for IELTS test sections."""
    
    def __init__(self, resources_path: str) -> None:
        """Initialize the grader with the resources directory path.
        
        Args:
            resources_path: Path to the resources directory containing answer keys.
        """
        self.resources_path = resources_path
        self.answer_keys: Dict[str, Any] = {}
    
    def load_answer_keys(self, book_name: str) -> bool:
        """Load answer keys for a specific book from JSON file.
        
        Args:
            book_name: Name of the book (e.g., 'BritishCouncil', 'CambridgeIELTS').
            
        Returns:
            True if answer keys loaded successfully, False otherwise.
        """
        answer_key_path = os.path.join(self.resources_path, book_name, "answer_keys.json")
        
        try:
            with open(answer_key_path, 'r', encoding='utf-8') as file:
                self.answer_keys = json.load(file)
            return True
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Error loading answer keys for {book_name}: {e}")
            return False
    
    def grade_listening_section(self, user_answers: Dict[str, str], 
                              test_name: str = "test_1") -> Dict[str, Any]:
        """Grade listening section answers against answer keys.
        
        Args:
            user_answers: Dictionary mapping question numbers to user answers.
            test_name: Name of the test (default: "test_1").
            
        Returns:
            Dictionary with correct count, total questions, percentage, and detailed results.
        """
        if "listening" not in self.answer_keys or test_name not in self.answer_keys["listening"]:
            return {"correct": 0, "total": 0, "percentage": 0.0, "details": []}
        
        test_answers = self.answer_keys["listening"][test_name]
        detailed_results = []
        correct_count = 0
        total_questions = 0
        
        for section_name, section_answers in test_answers.items():
            for answer_item in section_answers:
                question_num = str(answer_item["question"])
                correct_answer = answer_item["answer"].strip().lower()
                user_answer = user_answers.get(question_num, "").strip().lower()
                
                is_correct = self._compare_answers(user_answer, correct_answer, answer_item["type"])
                
                detailed_results.append({
                    "question": answer_item["question"],
                    "section": section_name,
                    "user_answer": user_answers.get(question_num, ""),
                    "correct_answer": answer_item["answer"],
                    "is_correct": is_correct,
                    "type": answer_item["type"]
                })
                
                if is_correct:
                    correct_count += 1
                total_questions += 1
        
        percentage = (correct_count / total_questions * 100) if total_questions > 0 else 0.0
        
        return {
            "correct": correct_count,
            "total": total_questions,
            "percentage": percentage,
            "details": detailed_results
        }
    
    def grade_reading_section(self, user_answers: Dict[str, str], 
                            test_name: str = "test_1") -> Dict[str, Any]:
        """Grade reading section answers against answer keys.
        
        Args:
            user_answers: Dictionary mapping question numbers to user answers.
            test_name: Name of the test (default: "test_1").
            
        Returns:
            Dictionary with correct count, total questions, percentage, and detailed results.
        """
        if "reading" not in self.answer_keys or test_name not in self.answer_keys["reading"]:
            return {"correct": 0, "total": 0, "percentage": 0.0, "details": []}
        
        test_answers = self.answer_keys["reading"][test_name]
        detailed_results = []
        correct_count = 0
        total_questions = 0
        
        for passage_name, passage_answers in test_answers.items():
            for answer_item in passage_answers:
                question_num = str(answer_item["question"])
                correct_answer = answer_item["answer"].strip().lower()
                user_answer = user_answers.get(question_num, "").strip().lower()
                
                is_correct = self._compare_answers(user_answer, correct_answer, answer_item["type"])
                
                detailed_results.append({
                    "question": answer_item["question"],
                    "passage": passage_name,
                    "user_answer": user_answers.get(question_num, ""),
                    "correct_answer": answer_item["answer"],
                    "is_correct": is_correct,
                    "type": answer_item["type"]
                })
                
                if is_correct:
                    correct_count += 1
                total_questions += 1
        
        percentage = (correct_count / total_questions * 100) if total_questions > 0 else 0.0
        
        return {
            "correct": correct_count,
            "total": total_questions,
            "percentage": percentage,
            "details": detailed_results
        }
    
    def _compare_answers(self, user_answer: str, correct_answer: str, question_type: str) -> bool:
        """Compare user answer with correct answer based on question type.
        
        Args:
            user_answer: User's answer (normalized to lowercase).
            correct_answer: Correct answer (normalized to lowercase).
            question_type: Type of question (text, multiple_choice, etc.).
            
        Returns:
            True if answers match, False otherwise.
        """
        if question_type == "multiple_choice":
            return user_answer == correct_answer
        elif question_type in ["true_false_not_given", "yes_no_not_given"]:
            return user_answer == correct_answer
        elif question_type == "text":
            # For text answers, allow for minor variations
            return self._text_answer_match(user_answer, correct_answer)
        else:
            return user_answer == correct_answer
    
    def _text_answer_match(self, user_answer: str, correct_answer: str) -> bool:
        """Check if text answers match with some flexibility.
        
        Args:
            user_answer: User's text answer.
            correct_answer: Correct text answer.
            
        Returns:
            True if answers are considered equivalent.
        """
        # Remove common punctuation and extra spaces
        user_clean = user_answer.replace(".", "").replace(",", "").strip()
        correct_clean = correct_answer.replace(".", "").replace(",", "").strip()
        
        # Exact match
        if user_clean == correct_clean:
            return True
        
        # Check if user answer contains the correct answer (for partial credit)
        if correct_clean in user_clean or user_clean in correct_clean:
            return True
        
        return False
    
    def calculate_band_score(self, correct_count: int, total_questions: int, 
                           section_type: str) -> float:
        """Calculate IELTS band score based on correct answers.
        
        Args:
            correct_count: Number of correct answers.
            total_questions: Total number of questions.
            section_type: Type of section ('listening' or 'reading').
            
        Returns:
            Band score as a float (0.0 to 9.0).
        """
        if total_questions == 0:
            return 0.0
        
        percentage = (correct_count / total_questions) * 100
        
        # IELTS band score conversion (approximate)
        if percentage >= 97:
            return 9.0
        elif percentage >= 89:
            return 8.5
        elif percentage >= 80:
            return 8.0
        elif percentage >= 71:
            return 7.5
        elif percentage >= 60:
            return 7.0
        elif percentage >= 50:
            return 6.5
        elif percentage >= 40:
            return 6.0
        elif percentage >= 30:
            return 5.5
        elif percentage >= 23:
            return 5.0
        elif percentage >= 16:
            return 4.5
        elif percentage >= 10:
            return 4.0
        elif percentage >= 6:
            return 3.5
        elif percentage >= 3:
            return 3.0
        else:
            return 2.5
    
    def generate_grading_report(self, section_type: str, result: Dict[str, Any]) -> str:
        """Generate a comprehensive grading report.
        
        Args:
            section_type: Type of section ('listening' or 'reading').
            result: Dictionary containing correct count, total questions, and detailed results.
            
        Returns:
            Formatted grading report as a string.
        """
        correct_count = result["correct"]
        total_questions = result["total"]
        detailed_results = result["details"]
        
        band_score = self.calculate_band_score(correct_count, total_questions, section_type)
        percentage = result["percentage"]
        
        report = f"""
{section_type.upper()} SECTION RESULTS
{'=' * 40}

Overall Score: {correct_count}/{total_questions} ({percentage:.1f}%)
Band Score: {band_score}

Detailed Results:
{'-' * 20}
"""
        
        # Group results by section/passage
        if section_type == "listening":
            sections = {}
            for result in detailed_results:
                section = result["section"]
                if section not in sections:
                    sections[section] = []
                sections[section].append(result)
            
            for section_name, section_results in sections.items():
                section_correct = sum(1 for r in section_results if r["is_correct"])
                section_total = len(section_results)
                report += f"\n{section_name.upper()}: {section_correct}/{section_total}\n"
                
                for result in section_results:
                    status = "✓" if result["is_correct"] else "✗"
                    report += f"  Q{result['question']}: {status} {result['user_answer']} (Correct: {result['correct_answer']})\n"
        
        elif section_type == "reading":
            passages = {}
            for result in detailed_results:
                passage = result["passage"]
                if passage not in passages:
                    passages[passage] = []
                passages[passage].append(result)
            
            for passage_name, passage_results in passages.items():
                passage_correct = sum(1 for r in passage_results if r["is_correct"])
                passage_total = len(passage_results)
                report += f"\n{passage_name.upper()}: {passage_correct}/{passage_total}\n"
                
                for result in passage_results:
                    status = "✓" if result["is_correct"] else "✗"
                    report += f"  Q{result['question']}: {status} {result['user_answer']} (Correct: {result['correct_answer']})\n"
        
        return report


if __name__ == "__main__":
    # Example usage for testing
    grader = IELTSGrader("resources")
    
    # Test with sample answers
    sample_listening_answers = {
        "1": "Smith",
        "2": "07734 892156",
        "3": "Monday",
        "4": "swimming",
        "5": "tennis"
    }
    
    if grader.load_answer_keys("BritishCouncil"):
        result = grader.grade_listening_section(sample_listening_answers)
        report = grader.generate_grading_report("listening", result)
        print(report)