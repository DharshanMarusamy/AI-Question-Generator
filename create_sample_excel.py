import pandas as pd

# Create sample data
data = {
    'Description': [
        'What is the main purpose of an operating system?',
        'Explain the concept of process scheduling in OS.',
        'Compare and contrast between threads and processes.',
        'What are the different types of memory management techniques?',
        'Describe the working of virtual memory.',
        'What is deadlock? How can it be prevented?',
        'Explain the concept of file systems in OS.',
        'What are the different types of CPU scheduling algorithms?',
        'Describe the working of paging in memory management.',
        'What is the difference between preemptive and non-preemptive scheduling?'
    ],
    'Type': [
        'Multiple Choice',
        'Short Answer',
        'Essay',
        'Multiple Choice',
        'Long Answer',
        'Short Answer',
        'Essay',
        'Multiple Choice',
        'Long Answer',
        'Short Answer'
    ],
    'Course Outcome': [
        'CO1',
        'CO2',
        'CO3',
        'CO2',
        'CO3',
        'CO4',
        'CO2',
        'CO3',
        'CO4',
        'CO1'
    ],
    "Bloom's Level": [
        'Remember',
        'Understand',
        'Analysis',
        'Apply',
        'Analysis',
        'Evaluate',
        'Understand',
        'Apply',
        'Analysis',
        'Evaluate'
    ],
    'Unit': [
        'Unit 1',
        'Unit 1',
        'Unit 2',
        'Unit 2',
        'Unit 3',
        'Unit 3',
        'Unit 4',
        'Unit 4',
        'Unit 5',
        'Unit 5'
    ]
}


df = pd.DataFrame(data)


df = df.astype(str)


df.to_excel('sample_questions.xlsx', index=False)
print("Sample Excel file 'sample_questions.xlsx' has been created successfully!") 