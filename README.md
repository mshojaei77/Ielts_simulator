# IELTS Test Simulator

A comprehensive desktop application for simulating the computer-based IELTS test experience, including all three main sections: Listening, Reading, and Writing.

## Features

This application aims to replicate the experience of taking the official IELTS computer-based test with the following features:

### General Features
- Clean, minimalist interface that closely resembles the official IELTS computer-based test
- Integrated timer functionality for each section
- Test selection capabilities for different practice materials
- Academic and General Training module support
- Export and print functionality for answers
- Detailed help information for each test section

### Listening Test
- 4 sections with 10 questions each (40 total)
- Audio playback simulation
- Progress tracking for audio playback
- Different question types similar to the real test
- Real-time completion status

### Reading Test
- 3 passages with approximately 13 questions each (39-40 total)
- Split-screen layout with passage on the left and questions on the right
- Different passage types for Academic and General Training
- Tabbed navigation between passages
- Real-time question completion tracking

### Writing Test
- Task 1 with different topics for Academic and General Training
- Task 2 essay writing 
- Word count tracking to meet minimum word requirements
- Time allocation guidance (20 minutes for Task 1, 40 minutes for Task 2)
- Comprehensive text editor with basic functionality

## Requirements

- Python 3.6 or higher
- PyQt5
- PyQt5-multimedia (for audio playback in the Listening test)

## Installation

1. Clone this repository:
```
git clone https://github.com/yourusername/ielts_simulator.git
cd ielts_simulator
```

2. Install the required dependencies:
```
pip install PyQt5 PyQt5-Qt5 PyQt5-sip
```

3. Run the application:
```
python main.py
```

## Usage

1. Launch the application using `python main.py`
2. Use the buttons at the top to switch between test sections (Listening, Reading, Writing)
3. Select a module type (Academic or General Training) where applicable
4. Choose a test from the dropdown menu
5. Click "Start Test" to begin the timer and enable editing
6. Complete the questions/tasks for the selected section
7. When finished, click "End Test" to see your completion summary

## Adding Custom Content

The application loads test content from the `subjects.json` file. You can add your own test materials by editing this file:

- `listening_subjects`: Add topics for listening tests
- `reading_subjects.academic`: Add academic reading passages
- `reading_subjects.general`: Add general training reading passages
- `task1_subjects.academic`: Add academic writing task 1 topics
- `task1_subjects.general`: Add general training writing task 1 topics
- `task2_subjects`: Add writing task 2 topics (shared between academic and general)

## Limitations

This is a simulation tool, and while it aims to replicate the official IELTS computer-based test as closely as possible, it may differ in some aspects from the actual test:

- The audio for the Listening test is simulated
- Reading passages are placeholders and would need real test content
- No official scoring or evaluation is provided

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- This simulator is inspired by the official IELTS computer-based test
- It is intended for educational and practice purposes only
- IELTS is a registered trademark of the British Council, IDP: IELTS Australia, and Cambridge Assessment English
