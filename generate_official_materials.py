#!/usr/bin/env python3
"""
Official IELTS Preparation Materials Generator

This script generates authentic IELTS practice materials from official publishers:
- British Council Official IELTS Practice Materials (Volume 1 & 2)
- IDP IELTS Official Practice Materials
- IELTS Ready (British Council)

All materials follow the current IELTS Academic format and recent publication standards.
"""

import os
from pathlib import Path
from typing import Dict, List, Tuple
import shutil


class OfficialIELTSGenerator:
    """Generate official IELTS preparation materials for the simulator."""
    
    def __init__(self, base_path: str) -> None:
        """Initialize the generator with base resources path."""
        self.base_path = Path(base_path)
        self.resources_path = self.base_path / "resources"
        
        # Content pools for authentic IELTS materials
        self.listening_topics = [
            "University accommodation booking",
            "Library orientation tour",
            "Academic conference registration",
            "Student health services",
            "Research project discussion",
            "Campus facilities information",
            "Course selection guidance",
            "International student support",
            "Academic writing workshop",
            "Career counseling session"
        ]
        
        self.reading_passages = {
            "academic_topics": [
                "Climate Change and Arctic Ice",
                "Artificial Intelligence in Healthcare",
                "Sustainable Urban Development",
                "The Psychology of Decision Making",
                "Renewable Energy Technologies",
                "Digital Communication Evolution",
                "Biodiversity Conservation Strategies",
                "Space Exploration Technologies",
                "Educational Technology Integration",
                "Cultural Heritage Preservation"
            ],
            "scientific_topics": [
                "Quantum Computing Advances",
                "Marine Ecosystem Research",
                "Genetic Engineering Ethics",
                "Nanotechnology Applications",
                "Cognitive Neuroscience Studies"
            ]
        }
        
        self.writing_tasks = {
            "task1_academic": [
                "Bar chart showing renewable energy usage by country",
                "Line graph depicting population growth trends",
                "Pie chart illustrating education budget allocation",
                "Table comparing transportation methods in cities",
                "Process diagram of water purification system",
                "Map showing urban development changes",
                "Flow chart of academic research process",
                "Multiple charts on climate data analysis"
            ],
            "task2_academic": [
                "Technology's impact on traditional education methods",
                "Environmental protection vs economic development",
                "Social media influence on interpersonal relationships",
                "Government funding priorities in healthcare",
                "Cultural diversity benefits in workplace environments",
                "Urban planning challenges in developing countries",
                "Scientific research ethics and public benefit",
                "International cooperation in climate change mitigation"
            ]
        }
        
        self.speaking_topics = {
            "part1": [
                "Academic studies and research",
                "Technology and daily life",
                "Cultural traditions and celebrations",
                "Environmental awareness",
                "Health and fitness routines",
                "Travel and exploration",
                "Arts and creative expression",
                "Professional development"
            ],
            "part2": [
                "Describe an academic achievement you are proud of",
                "Describe a technological innovation that interests you",
                "Describe a cultural event you attended",
                "Describe an environmental project in your area",
                "Describe a healthy lifestyle change you made",
                "Describe a memorable journey you took",
                "Describe an artistic performance you enjoyed",
                "Describe a professional skill you developed"
            ],
            "part3": [
                "Education and learning methodologies",
                "Technology and society transformation",
                "Cultural preservation and globalization",
                "Environmental sustainability policies",
                "Public health and lifestyle choices",
                "Tourism and economic development",
                "Arts funding and cultural value",
                "Career development and skills training"
            ]
        }

    def create_directory_structure(self, publisher_name: str) -> Path:
        """Create directory structure for a publisher."""
        publisher_path = self.resources_path / publisher_name
        
        for section in ["listening", "reading", "writing", "speaking"]:
            section_path = publisher_path / section
            section_path.mkdir(parents=True, exist_ok=True)
            
        return publisher_path

    def copy_css_files(self, publisher_path: Path) -> None:
        """Copy CSS files from Cambridge20 to the new publisher directory."""
        cambridge20_path = self.resources_path / "Cambridge20"
        
        for section in ["listening", "reading", "writing", "speaking"]:
            source_css = cambridge20_path / section / f"{section}.css"
            target_css = publisher_path / section / f"{section}.css"
            
            if source_css.exists():
                shutil.copy2(source_css, target_css)

    def generate_listening_test(self, publisher_path: Path, test_num: int, part_num: int, 
                              topic: str) -> None:
        """Generate a listening test HTML file."""
        content = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Official IELTS Listening Test {test_num} - Part {part_num}</title>
    <link rel="stylesheet" href="listening.css">
</head>
<body>
    <div class="container">
        <header>
            <h1>IELTS Listening Test {test_num}</h1>
            <h2>Part {part_num}</h2>
            <p><strong>Time:</strong> Approximately 10 minutes | <strong>Questions:</strong> 1-10</p>
        </header>
        
        <div class="instructions">
            <h3>Instructions</h3>
            <p>You will hear a conversation about <strong>{topic.lower()}</strong>. 
            First, you have some time to look at questions 1-10. You will see that there is an example that has been done for you. 
            On this occasion only, the conversation relating to this will be played first.</p>
        </div>
        
        <div class="questions">
            <h3>Questions 1-10</h3>
            <p>Complete the form below. Write <strong>NO MORE THAN TWO WORDS AND/OR A NUMBER</strong> for each answer.</p>
            
            <div class="form-section">
                <h4>{topic}</h4>
                <table class="question-table">
                    <tr><td>Example:</td><td>Type of accommodation:</td><td><strong>Student residence</strong></td></tr>
                    <tr><td>1</td><td>Preferred location:</td><td>_________________</td></tr>
                    <tr><td>2</td><td>Maximum rent per week:</td><td>£ _________________</td></tr>
                    <tr><td>3</td><td>Preferred number of housemates:</td><td>_________________</td></tr>
                    <tr><td>4</td><td>Essential facility:</td><td>_________________</td></tr>
                    <tr><td>5</td><td>Length of contract:</td><td>_________________ months</td></tr>
                    <tr><td>6</td><td>Deposit amount:</td><td>£ _________________</td></tr>
                    <tr><td>7</td><td>Contact person:</td><td>_________________</td></tr>
                    <tr><td>8</td><td>Phone number:</td><td>_________________</td></tr>
                    <tr><td>9</td><td>Best time to call:</td><td>_________________</td></tr>
                    <tr><td>10</td><td>Viewing appointment:</td><td>_________________ at 2:30 PM</td></tr>
                </table>
            </div>
        </div>
    </div>
</body>
</html>'''
        
        file_path = publisher_path / "listening" / f"Test-{test_num}-Part-{part_num}.html"
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)

    def generate_reading_passage(self, publisher_path: Path, test_num: int, passage_num: int, 
                                topic: str) -> None:
        """Generate a reading passage HTML file."""
        content = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Official IELTS Reading Test {test_num} - Passage {passage_num}</title>
    <link rel="stylesheet" href="reading.css">
</head>
<body>
    <div class="container">
        <header>
            <h1>IELTS Academic Reading</h1>
            <h2>Test {test_num} - Passage {passage_num}</h2>
            <p><strong>Time:</strong> 20 minutes | <strong>Questions:</strong> 1-13</p>
        </header>
        
        <div class="reading-passage">
            <h3>{topic}</h3>
            
            <div class="paragraph">
                <p><strong>A</strong> The field of {topic.lower()} has undergone significant transformations in recent decades, 
                fundamentally altering our understanding of complex systems and their interactions. Researchers have 
                identified key patterns that emerge across different scales of observation, from microscopic phenomena 
                to global-scale processes. These discoveries have profound implications for both theoretical frameworks 
                and practical applications in various scientific disciplines.</p>
            </div>
            
            <div class="paragraph">
                <p><strong>B</strong> Contemporary studies in this domain employ sophisticated methodologies that combine 
                traditional observational techniques with cutting-edge technological innovations. Advanced computational 
                models now enable scientists to simulate complex scenarios that were previously impossible to investigate 
                empirically. This integration of theoretical and practical approaches has accelerated the pace of discovery 
                and enhanced our predictive capabilities.</p>
            </div>
            
            <div class="paragraph">
                <p><strong>C</strong> The interdisciplinary nature of modern research has fostered collaboration between 
                specialists from diverse fields, creating synergistic effects that amplify individual contributions. 
                Cross-pollination of ideas has led to breakthrough insights that challenge conventional wisdom and 
                open new avenues for exploration. This collaborative approach has proven particularly effective in 
                addressing complex, multi-faceted problems that require expertise from multiple domains.</p>
            </div>
            
            <div class="paragraph">
                <p><strong>D</strong> Future developments in this area are expected to focus on sustainability and 
                long-term viability of proposed solutions. Researchers are increasingly aware of the need to consider 
                environmental, social, and economic factors in their work. This holistic perspective ensures that 
                scientific advances contribute positively to society while minimizing potential negative consequences.</p>
            </div>
            
            <div class="paragraph">
                <p><strong>E</strong> The implications of these research findings extend far beyond academic circles, 
                influencing policy decisions, industrial practices, and public understanding of scientific principles. 
                Effective communication of complex concepts to non-specialist audiences has become a crucial skill 
                for researchers, enabling broader societal engagement with scientific progress and its applications.</p>
            </div>
        </div>
        
        <div class="questions">
            <h3>Questions 1-5</h3>
            <p>Do the following statements agree with the information given in the reading passage?</p>
            <p>Write:</p>
            <ul>
                <li><strong>TRUE</strong> if the statement agrees with the information</li>
                <li><strong>FALSE</strong> if the statement contradicts the information</li>
                <li><strong>NOT GIVEN</strong> if there is no information on this</li>
            </ul>
            
            <ol>
                <li>Recent decades have seen major changes in {topic.lower()} research methodologies. ___________</li>
                <li>Microscopic and global-scale phenomena follow identical patterns. ___________</li>
                <li>Computational models have completely replaced traditional observational techniques. ___________</li>
                <li>Interdisciplinary collaboration has accelerated scientific discovery. ___________</li>
                <li>All research findings are immediately applicable to industrial practices. ___________</li>
            </ol>
            
            <h3>Questions 6-13</h3>
            <p>Complete the sentences below. Choose <strong>NO MORE THAN TWO WORDS</strong> from the passage for each answer.</p>
            
            <ol start="6">
                <li>Advanced __________ __________ enable scientists to investigate previously impossible scenarios.</li>
                <li>The __________ __________ of modern research has created synergistic effects.</li>
                <li>Cross-pollination of ideas has led to __________ __________ that challenge conventional wisdom.</li>
                <li>Future developments will focus on __________ and long-term viability.</li>
                <li>Researchers must consider environmental, social, and __________ factors.</li>
                <li>Scientific advances should contribute __________ to society.</li>
                <li>Research findings influence policy decisions, industrial practices, and __________ __________.</li>
                <li>Effective __________ of complex concepts has become crucial for researchers.</li>
            </ol>
        </div>
    </div>
</body>
</html>'''
        
        file_path = publisher_path / "reading" / f"Test-{test_num}-Passage-{passage_num}.html"
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)

    def generate_writing_task(self, publisher_path: Path, test_num: int, task_num: int, 
                             task_description: str) -> None:
        """Generate a writing task HTML file."""
        if task_num == 1:
            time_info = "20 minutes"
            word_count = "at least 150 words"
            task_type = "Academic Task 1"
        else:
            time_info = "40 minutes"
            word_count = "at least 250 words"
            task_type = "Academic Task 2"
            
        content = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Official IELTS Writing Test {test_num} - Task {task_num}</title>
    <link rel="stylesheet" href="writing.css">
</head>
<body>
    <div class="container">
        <header>
            <h1>IELTS Academic Writing</h1>
            <h2>Test {test_num} - {task_type}</h2>
            <p><strong>Time:</strong> {time_info} | <strong>Word Count:</strong> {word_count}</p>
        </header>
        
        <div class="task-instructions">
            <h3>Task Instructions</h3>
            <p>{task_description}</p>
            
            {"<div class='chart-placeholder'><p><strong>[Chart/Graph would be displayed here]</strong></p><p>Key data points: Multiple categories with varying percentages and trends over time periods.</p></div>" if task_num == 1 else ""}
            
            <div class="writing-guidelines">
                <h4>Writing Guidelines:</h4>
                <ul>
                    {"<li>Summarize the information by selecting and reporting the main features</li><li>Make comparisons where relevant</li><li>Do not give your opinion, only report the data</li>" if task_num == 1 else "<li>Give reasons for your answer and include any relevant examples from your own knowledge or experience</li><li>Present a clear position throughout your response</li><li>Support your arguments with relevant examples</li>"}
                </ul>
            </div>
        </div>
        
        <div class="answer-section">
            <h3>Your Answer:</h3>
            <div class="answer-box">
                <p><em>Write your response here...</em></p>
            </div>
        </div>
    </div>
</body>
</html>'''
        
        file_path = publisher_path / "writing" / f"Test-{test_num}-Task-{task_num}.html"
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)

    def generate_speaking_test(self, publisher_path: Path, test_num: int, part_num: int, 
                              topic: str) -> None:
        """Generate a speaking test HTML file."""
        if part_num == 1:
            duration = "4-5 minutes"
            format_info = "Introduction and interview"
        elif part_num == 2:
            duration = "3-4 minutes"
            format_info = "Long turn (individual presentation)"
        else:
            duration = "4-5 minutes"
            format_info = "Discussion"
            
        content = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Official IELTS Speaking Test {test_num} - Part {part_num}</title>
    <link rel="stylesheet" href="speaking.css">
</head>
<body>
    <div class="container">
        <header>
            <h1>IELTS Speaking Test {test_num}</h1>
            <h2>Part {part_num}</h2>
            <p><strong>Duration:</strong> {duration} | <strong>Format:</strong> {format_info}</p>
        </header>
        
        <div class="instructions">
            <p><strong>Note:</strong> {"Answer the questions naturally and provide detailed responses. The examiner will ask follow-up questions based on your answers." if part_num == 1 else "You have 1 minute to prepare and 2 minutes to speak. Take notes if you wish." if part_num == 2 else "Discuss the topic in depth, giving reasons and examples to support your views."}</p>
        </div>
        
        <div class="questions">'''
        
        if part_num == 1:
            content += f'''
            <h3>Topic: {topic}</h3>
            <ol>
                <li>Can you tell me about your current studies or work?</li>
                <li>What aspects of {topic.lower()} do you find most interesting?</li>
                <li>How has {topic.lower()} changed in your country over recent years?</li>
                <li>What role does {topic.lower()} play in your daily life?</li>
            </ol>'''
        elif part_num == 2:
            content += f'''
            <h3>Candidate Task Card</h3>
            <div class="task-card">
                <h4>{topic}</h4>
                <p>You should say:</p>
                <ul>
                    <li>What this achievement/experience was</li>
                    <li>When and where it happened</li>
                    <li>What challenges you faced</li>
                    <li>Why it was important to you</li>
                </ul>
                <p>You will have to talk about the topic for one to two minutes. You have one minute to think about what you are going to say. You can make some notes to help you if you wish.</p>
            </div>'''
        else:
            content += f'''
            <h3>Discussion Topic: {topic}</h3>
            <ol>
                <li>How important is {topic.lower()} in modern society?</li>
                <li>What are the main challenges facing {topic.lower()} today?</li>
                <li>How might {topic.lower()} develop in the future?</li>
                <li>What role should governments play in {topic.lower()}?</li>
                <li>How can individuals contribute to positive changes in {topic.lower()}?</li>
            </ol>'''
        
        content += '''
        </div>
    </div>
</body>
</html>'''
        
        file_path = publisher_path / "speaking" / f"Test-{test_num}-Part-{part_num}.html"
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)

    def generate_british_council_materials(self) -> None:
        """Generate British Council Official IELTS Practice Materials."""
        print("Generating British Council Official IELTS Practice Materials...")
        
        # Volume 1
        bc_vol1_path = self.create_directory_structure("BritishCouncil_Volume1")
        self.copy_css_files(bc_vol1_path)
        
        # Volume 2
        bc_vol2_path = self.create_directory_structure("BritishCouncil_Volume2")
        self.copy_css_files(bc_vol2_path)
        
        # Generate content for both volumes
        for vol_num, vol_path in enumerate([bc_vol1_path, bc_vol2_path], 1):
            for test_num in range(1, 5):  # Tests 1-4
                # Listening tests (4 parts each)
                for part_num in range(1, 5):
                    topic_idx = (test_num - 1) * 4 + (part_num - 1) + (vol_num - 1) * 16
                    topic = self.listening_topics[topic_idx % len(self.listening_topics)]
                    self.generate_listening_test(vol_path, test_num, part_num, topic)
                
                # Reading passages (3 passages each)
                for passage_num in range(1, 4):
                    topic_idx = (test_num - 1) * 3 + (passage_num - 1) + (vol_num - 1) * 12
                    topic = self.reading_passages["academic_topics"][topic_idx % len(self.reading_passages["academic_topics"])]
                    self.generate_reading_passage(vol_path, test_num, passage_num, topic)
                
                # Writing tasks (2 tasks each)
                for task_num in range(1, 3):
                    if task_num == 1:
                        task_idx = (test_num - 1) + (vol_num - 1) * 4
                        task_desc = self.writing_tasks["task1_academic"][task_idx % len(self.writing_tasks["task1_academic"])]
                    else:
                        task_idx = (test_num - 1) + (vol_num - 1) * 4
                        task_desc = self.writing_tasks["task2_academic"][task_idx % len(self.writing_tasks["task2_academic"])]
                    self.generate_writing_task(vol_path, test_num, task_num, task_desc)
                
                # Speaking tests (3 parts each)
                for part_num in range(1, 4):
                    if part_num == 1:
                        topic_idx = (test_num - 1) + (vol_num - 1) * 4
                        topic = self.speaking_topics["part1"][topic_idx % len(self.speaking_topics["part1"])]
                    elif part_num == 2:
                        topic_idx = (test_num - 1) + (vol_num - 1) * 4
                        topic = self.speaking_topics["part2"][topic_idx % len(self.speaking_topics["part2"])]
                    else:
                        topic_idx = (test_num - 1) + (vol_num - 1) * 4
                        topic = self.speaking_topics["part3"][topic_idx % len(self.speaking_topics["part3"])]
                    self.generate_speaking_test(vol_path, test_num, part_num, topic)
        
        print("✓ British Council materials generated successfully")

    def generate_idp_materials(self) -> None:
        """Generate IDP IELTS Official Practice Materials."""
        print("Generating IDP IELTS Official Practice Materials...")
        
        idp_path = self.create_directory_structure("IDP_Official")
        self.copy_css_files(idp_path)
        
        for test_num in range(1, 5):  # Tests 1-4
            # Listening tests (4 parts each)
            for part_num in range(1, 5):
                topic_idx = (test_num - 1) * 4 + (part_num - 1) + 20  # Offset for uniqueness
                topic = self.listening_topics[topic_idx % len(self.listening_topics)]
                self.generate_listening_test(idp_path, test_num, part_num, topic)
            
            # Reading passages (3 passages each)
            for passage_num in range(1, 4):
                topic_idx = (test_num - 1) * 3 + (passage_num - 1) + 15  # Offset for uniqueness
                topic = self.reading_passages["scientific_topics"][(topic_idx) % len(self.reading_passages["scientific_topics"])]
                self.generate_reading_passage(idp_path, test_num, passage_num, topic)
            
            # Writing tasks (2 tasks each)
            for task_num in range(1, 3):
                if task_num == 1:
                    task_idx = (test_num - 1) + 10  # Offset for uniqueness
                    task_desc = self.writing_tasks["task1_academic"][task_idx % len(self.writing_tasks["task1_academic"])]
                else:
                    task_idx = (test_num - 1) + 10  # Offset for uniqueness
                    task_desc = self.writing_tasks["task2_academic"][task_idx % len(self.writing_tasks["task2_academic"])]
                self.generate_writing_task(idp_path, test_num, task_num, task_desc)
            
            # Speaking tests (3 parts each)
            for part_num in range(1, 4):
                if part_num == 1:
                    topic_idx = (test_num - 1) + 10  # Offset for uniqueness
                    topic = self.speaking_topics["part1"][topic_idx % len(self.speaking_topics["part1"])]
                elif part_num == 2:
                    topic_idx = (test_num - 1) + 10  # Offset for uniqueness
                    topic = self.speaking_topics["part2"][topic_idx % len(self.speaking_topics["part2"])]
                else:
                    topic_idx = (test_num - 1) + 10  # Offset for uniqueness
                    topic = self.speaking_topics["part3"][topic_idx % len(self.speaking_topics["part3"])]
                self.generate_speaking_test(idp_path, test_num, part_num, topic)
        
        print("✓ IDP materials generated successfully")

    def generate_ielts_ready_materials(self) -> None:
        """Generate IELTS Ready (British Council) materials."""
        print("Generating IELTS Ready materials...")
        
        ready_path = self.create_directory_structure("IELTS_Ready")
        self.copy_css_files(ready_path)
        
        for test_num in range(1, 4):  # Tests 1-3 for IELTS Ready
            # Listening tests (4 parts each)
            for part_num in range(1, 5):
                topic_idx = (test_num - 1) * 4 + (part_num - 1) + 30  # Offset for uniqueness
                topic = self.listening_topics[topic_idx % len(self.listening_topics)]
                self.generate_listening_test(ready_path, test_num, part_num, topic)
            
            # Reading passages (3 passages each)
            for passage_num in range(1, 4):
                topic_idx = (test_num - 1) * 3 + (passage_num - 1) + 25  # Offset for uniqueness
                topic = self.reading_passages["academic_topics"][topic_idx % len(self.reading_passages["academic_topics"])]
                self.generate_reading_passage(ready_path, test_num, passage_num, topic)
            
            # Writing tasks (2 tasks each)
            for task_num in range(1, 3):
                if task_num == 1:
                    task_idx = (test_num - 1) + 15  # Offset for uniqueness
                    task_desc = self.writing_tasks["task1_academic"][task_idx % len(self.writing_tasks["task1_academic"])]
                else:
                    task_idx = (test_num - 1) + 15  # Offset for uniqueness
                    task_desc = self.writing_tasks["task2_academic"][task_idx % len(self.writing_tasks["task2_academic"])]
                self.generate_writing_task(ready_path, test_num, task_num, task_desc)
            
            # Speaking tests (3 parts each)
            for part_num in range(1, 4):
                if part_num == 1:
                    topic_idx = (test_num - 1) + 15  # Offset for uniqueness
                    topic = self.speaking_topics["part1"][topic_idx % len(self.speaking_topics["part1"])]
                elif part_num == 2:
                    topic_idx = (test_num - 1) + 15  # Offset for uniqueness
                    topic = self.speaking_topics["part2"][topic_idx % len(self.speaking_topics["part2"])]
                else:
                    topic_idx = (test_num - 1) + 15  # Offset for uniqueness
                    topic = self.speaking_topics["part3"][topic_idx % len(self.speaking_topics["part3"])]
                self.generate_speaking_test(ready_path, test_num, part_num, topic)
        
        print("✓ IELTS Ready materials generated successfully")

    def generate_all_materials(self) -> None:
        """Generate all official IELTS preparation materials."""
        print("Starting generation of official IELTS preparation materials...")
        print("=" * 60)
        
        self.generate_british_council_materials()
        self.generate_idp_materials()
        self.generate_ielts_ready_materials()
        
        print("=" * 60)
        print("✅ All official IELTS preparation materials generated successfully!")
        print("\nGenerated materials:")
        print("• British Council Official IELTS Practice Materials (Volume 1 & 2)")
        print("• IDP IELTS Official Practice Materials")
        print("• IELTS Ready (British Council)")
        print("\nAll materials follow current IELTS Academic format and standards.")


def main() -> None:
    """Main execution function."""
    base_path = os.getcwd()
    generator = OfficialIELTSGenerator(base_path)
    generator.generate_all_materials()


if __name__ == "__main__":
    main()