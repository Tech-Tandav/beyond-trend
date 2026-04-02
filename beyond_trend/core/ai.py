import json
from openai import OpenAI 
from google import genai
from django.conf import settings
from rest_framework import status
from rest_framework.response import Response



def select_ai_model(ai_model_taken, module, task_prompts=None, task_answers=None):
        ai_model = ai_model_taken
        # # Generate test content using your custom AI function
        if ai_model == "openai":
            pass
            # test_content = get_openai_response(module, task_prompts, task_answers)
        elif ai_model == "gemini":
            test_content = get_gemini_response(module, task_prompts, task_answers)
        else:
            return Response({"error":"Select AI model"}, status=status.HTTP_400_BAD_REQUEST)
        return test_content
    
    
####################   #########################################################################################
#################   ############################################################################################
############   ###### ###########################################################################################
#############    ######  ##########################################################################################
####################   #########################################################################################

client = genai.Client(api_key=settings.GEMINI_API_KEY)


def get_gemini_response(module, question=None, user_answers=None):
    
    # try:
    prompt = {
        "listening" : """
                    Create a complete IELTS Listening mock test and return it ONLY as valid JSON. Do NOT include any extra text outside the JSON. The JSON must strictly follow the structure below:

                    {
                    \"sections\": [
                        {
                        \"task_type\": \"section_1\",
                        \"title\": \"<Section Title>\",
                        \"topic\": \"<Main Topic>\",
                        \"difficulty\": \"beginner | intermediate | advanced\",
                        \"transcript\": \"<Detailed transcript of 400–500 words with dialogues. Each dialogue must start with 'Speaker 1:', 'Speaker 2:' etc., separated by two newlines>\",
                        \"questions\": [
                            {
                            \"questionNum\": \"1-4\",
                            \"questionType\": \"Multiple Choice\",
                            \"questionTitle\": \"Choose the correct answer.\",
                            \"actualQuestions\": [
                                {
                                \"order\": \"1\",
                                \"label\": \"Where is the student planning to travel?\",
                                \"options\": [
                                    { \"label\": \"A. Paris\", \"value\": \"a\" },
                                    { \"label\": \"B. Rome\", \"value\": \"b\" },
                                    { \"label\": \"C. Berlin\", \"value\": \"c\" }
                                ]
                                }
                            ]
                            },
                            {
                            \"questionNum\": \"5-7\",
                            \"questionType\": \"True-False-Not-Given\",
                            \"questionTitle\": \"Write TRUE, FALSE, or NOT GIVEN.\",
                            \"actualQuestions\": [
                                {
                                \"order\": \"5\",
                                \"label\": \"The student has visited France before.\",
                                \"options\": [
                                    { \"label\": \"TRUE\", \"value\": \"true\" },
                                    { \"label\": \"FALSE\", \"value\": \"false\" },
                                    { \"label\": \"NOT GIVEN\", \"value\": \"not_given\" }
                                ]
                                }
                            ]
                            },
                            {
                            \"questionNum\": \"8-10\",
                            \"questionType\": \"Short Answer\",
                            \"questionTitle\": \"Answer in no more than two words.\",
                            \"actualQuestions\": [
                                {
                                \"order\": \"8\",
                                \"label\": \"What is the student studying?\",
                                \"options\": []
                                }
                            ]
                            },
                        ],
                        \"answers\": { \"1\": \"b\", \"5\": \"false\", \"8\": \"history\", \"9\": \"museum\" }
                        }
                    ]
                    }

                    ### Listening Test Requirements:
                    - 4 sections, each 400–500 word transcript (realistic scenarios like university orientation, trip booking, lecture, business meeting).
                    - Each section has exactly 10 questions:
                    * Multiple Choice (3–4)
                    * True-False-Not Given (3–4)
                    * Short Answer (1–2)
                    - For T/F/NG, options must be EXACTLY:
                    [{\"label\": \"TRUE\", \"value\": \"true\"}, {\"label\": \"FALSE\", \"value\": \"false\"}, {\"label\": \"NOT GIVEN\", \"value\": \"not_given\"}]
                    - Output ONLY valid JSON.
                    - Vary topics and wording each time.
                    - Keep values and answers in lowercase for consistency.
                    - Do not have space , make like Speaker1, Speaker2
        """,
        "reading" : """
                    Create a complete IELTS Reading mock test and return it ONLY as valid JSON. Do NOT include any extra explanation outside the JSON. The JSON must strictly follow this structure:

                    {
                    \"passages\": [
                        {
                        \"task_type\": \"passage_1\",
                        \"title\": \"<Passage Title>\",
                        \"topic\": \"<Topic>\",
                        \"difficulty\": \"beginner | intermediate | advanced\",
                        \"passage\": \"<Full passage text of 700–900 words, divided into paragraphs labeled Passage A, Passage B, etc., with HTML tags for paragraph separation>\",
                        \"questions\": [
                            {
                            \"questionNum\": \"1-4\",
                            \"questionType\": \"Matching Heading\",
                            \"questionTitle\": \"Choose the correct heading for each paragraph from the list below.\",
                            \"actualQuestions\": [
                                {
                                \"order\": \"1\",
                                \"label\": \"Paragraph A\",
                                \"options\": [
                                    { \"label\": \"Heading 1: The Origins of the Internet\", \"value\": \"heading 1\" },
                                    { \"label\": \"Heading 2: Modern Applications\", \"value\": \"heading 2\" },
                                    { \"label\": \"Heading 3: Early Challenges\", \"value\": \"heading 3\" }
                                ]
                                }
                            ]
                            },
                            {
                            \"questionNum\": \"5-8\",
                            \"questionType\": \"True-False-Not-Given\",
                            \"questionTitle\": \"Write TRUE, FALSE, or NOT GIVEN.\",
                            \"actualQuestions\": [
                                {
                                \"order\": \"5\",
                                \"label\": \"The internet was invented in the 21st century.\",
                                \"options\": [
                                    { \"label\": \"TRUE\", \"value\": \"true\" },
                                    { \"label\": \"FALSE\", \"value\": \"false\" },
                                    { \"label\": \"NOT GIVEN\", \"value\": \"not_given\" }
                                ]
                                }
                            ]
                            },
                            {
                            \"questionNum\": \"9-11\",
                            \"questionType\": \"Multiple Choice\",
                            \"questionTitle\": \"Choose the correct letter.\",
                            \"actualQuestions\": [
                                {
                                \"order\": \"9\",
                                \"label\": \"What was the primary purpose of ARPANET?\",
                                \"options\": [
                                    { \"label\": \"A. Commercial Use\", \"value\": \"a\" },
                                    { \"label\": \"B. Academic Research\", \"value\": \"b\" },
                                    { \"label\": \"C. Entertainment\", \"value\": \"c\" }
                                ]
                                }
                            ]
                            },
                            {
                            \"questionNum\": \"12-13\",
                            \"questionType\": \"Short Answer\",
                            \"questionTitle\": \"Answer in NO MORE THAN TWO WORDS.\",
                            \"actualQuestions\": [
                                {
                                \"order\": \"12\",
                                \"label\": \"What year was ARPANET launched?\",
                                \"options\": []
                                }
                            ]
                            },
                        ],
                        \"answers\": { \"1\": \"heading 1\", \"5\": \"false\", \"9\": \"b\", \"12\": \"1969\", \"13\": \"military\" }
                        }
                    ]
                    }

                    ### Reading Test Requirements:
                    - 3 passages, each 700–900 words.
                    - Passages paragraphs are seperated by html tag and Paragraph name like Paragraph A,Paragraph B.
                    - Total 40 questions strictly (10–15 per passage).
                    - Include ALL question types: Matching Heading,  Multiple Choice, True/False/Not Given, Short Answer.
                    - Use example structures above for consistency all the time.
                    - In Matching Heading stricly follow the options structure.
                    - Don't include html tag in questions label
                    - Output ONLY valid JSON.
                    - Vary topics and question phrasing each time.
                    - Keep values and answers in lowercase for consistency.
                    - For difficulty choices are beginner, intermediate and advanced.
        """,
                        
        "writing" : f"""
                Generate an IELTS Writing Task 1 prompt for a simple or difficulty level test on the any topic.
                The prompt should describe a visual (e.g., a graph, chart, map, or process diagram) and ask the candidate to summarize, describe, or explain the information in their own words.
                Specify a minimum word count of 150 words.

                Generate an IELTS Writing Task 2 prompt for a simple or difficulty  level test on any topic .
                The prompt should present an opinion, argument, or problem and ask the candidate to write an essay in response.
                Specify a minimum word count of 250 words.
                
                For difficulty choices are beginner, intermediate and advanced.

                Format your response as valid JSON with this structure:
                {{
                    "tasks:[
                    {{
                    "title": "Writing Task 1: [Brief Description]",
                    "task_type": "task_1",
                    "topic": "On what topic the passage is",
                    "difficulty":"How difficult is this section",
                    "questions": "Describe the information shown in the [visual type] below...",
                    "min_word_count": 150,
                    "task_url":"Image link"
                    }},
                    {{
                    "title": "Writing Task 2: [Essay Topic]",
                    "task_type": "task_2",
                    "topic": "On what topic the passage is",
                    "difficulty":"How difficult is this section",
                    "questions": "Write an essay on the following topic: [Essay question here]...",
                    "min_word_count": 250
                    }}
                    ]
                }}
        """,
        "speaking" : f"""
            Generate an IELTS speaking test form simple to difficulty level on different topic .
            The test should include:
            1. Part 1: 3-4 general questions about familiar topics.
            2. Part 2: A cue card with a topic and 3-4 bullet points to cover, followed by a general instruction.
            3. Part 3: 3-4 discussion questions related to the Part 2 topic, but more abstract.
            For difficulty choices are beginner, intermediate and advanced.
            Format your response as valid JSON with this structure:
            {{
                "parts":[
                    {{
                        "task_type": "part1",
                        "title": "Part : Title",
                        "topic": "On what topic the part is",
                        "difficulty":"How difficult is this section",
                        "questions": [
                            "Question 1?",
                            "Question 2?"
                        ]
                    }},
                    {{
                        "task_type": "part_2",
                        "title": "Part : Title",
                        "topic": "On what topic the part is",
                        "difficulty":"How difficult is this part",
                        "questions":  "Describe a time when you helped someone...",
                    }},
                    {{
                        "task_type": "part_2_follow_up",
                        "title": "Part : Title",
                        "topic": "On what topic the part is",
                        "difficulty":"How difficult is this part",
                        "questions": [
                            "You should say:",
                            "who the person was",
                            "what the situation was",
                            "how you helped them",
                            "and explain how you felt about helping this person."
                        ],
                    }},
                    {{
                        "task_type": "part_3",
                        "title": "Part : Title",
                        "topic": "On what topic the part is",
                        "difficulty":"How difficult is this part",
                        "questions": [
                            "Let's talk about helping others in general. Why do people help others?",
                            "Do you think people are more or less helpful now than in the past?"
                        ]   
                    }}
                ]
            }},
        """,
        "writing_answers" : f"""
                You are an IELTS writing examiner. Evaluate the following user response for IELTS.
                Provide a band score (0-9) and detailed feedback based on the four IELTS writing criteria:
                1. Task Achievement/Response (TR/TA)
                2. Coherence and Cohesion (CC)
                3. Lexical Resource (LR)
                4. Grammatical Range and Accuracy (GRA)

                Task 1:
                Prompt:{{question.get("task_1")}}
                User Response: {{user_answers.get("task_1")}}
                Word Count: {{len(user_answers.split())}} words
                
                Task 2:
                Prompt:{{question.get("task_2")}}
                User Response: {{user_answers.get("task_2")}}
                Word Count: {{len(user_answers.split())}} words
                Format your response as valid JSON with this structure:
                {{
                    "band_score": 7.0,
                    "task_1":{{
                        "detailed_feedback": "Overall feedback on the essay, highlighting strengths and weaknesses.",
                        "criteria_feedback": {{
                            "task_achievement": {{
                                "score":3,
                                "feedback":"Feedback for Task Achievement/Response."
                            }},
                            "coherence_cohesion": {{
                                "score":3,
                                "feedback":"Feedback for Coherence and Cohesion."
                            }},
                            "lexical_resource": {{
                                "score":3,
                                "feedback":"Feedback for Lexical Resource."
                            }},
                            "grammatical_range_accuracy": {{
                                "score":3,
                                "feedback":"Feedback for Grammatical Range and Accuracy."
                            }}
                        }}
                        }}
                    "task_2:{{
                        "detailed_feedback": "Overall feedback on the essay, highlighting strengths and weaknesses.",
                        "criteria_feedback": {{
                            "task_achievement": {{
                                "score":3,
                                "feedback":"Feedback for Task Achievement/Response."
                            }},
                            "coherence_cohesion": {{
                                "score":3,
                                "feedback":"Feedback for Coherence and Cohesion."
                            }},
                            "lexical_resource": {{
                                "score":3,
                                "feedback":"Feedback for Lexical Resource."
                            }},
                            "grammatical_range_accuracy": {{
                                "score":3,
                                "feedback":"Feedback for Grammatical Range and Accuracy."
                            }}
                        }}
                    }}
                }}
        """,
        "speaking_answers" : f"""
            You are an IELTS speaking examiner. Evaluate the following transcription of a candidate's response to an IELTS speaking test.
            Provide a band score (0-9) and detailed feedback based on the four IELTS speaking criteria:
            1. Fluency and Coherence (FC)
            2. Lexical Resource (LR)
            3. Grammatical Range and Accuracy (GRA)
            4. Pronunciation (P)

            Consider the original speaking task context:
            Part 1 Questions: {{task_prompt.get('part1_questions', [])}}
            Part 2 Prompt: {{task_prompt.get('part2_prompt', '')}}
            Part 2 Follow-up: {{task_prompt.get('part2_follow_up_questions', [])}}
            Part 3 Questions: {{task_prompt.get('part3_questions', [])}}

            Candidate's Transcription:
            {{user_answers}}

            Format your response as valid JSON with this structure:
            {{
                "band_score": 7.0,
                "detailed_feedback": "Overall feedback on the speaking performance, highlighting strengths and weaknesses.",
                "criteria_feedback": {{
                    "fluency_coherence": "Feedback for Fluency and Coherence.",
                    "lexical_resource": "Feedback for Lexical Resource.",
                    "grammatical_range_accuracy": "Feedback for Grammatical Range and Accuracy.",
                    "pronunciation": "Feedback for Pronunciation (based on transcription, infer clarity/intonation where possible)."
                }},
                "transcription": "The full transcription of the candidate's speech."
            }}
        """
    }
    module_prompt = prompt[module]
    text_gen_response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=module_prompt
                )
    raw_ai_response = text_gen_response.text
    if raw_ai_response.strip().startswith("```json"):
        raw_ai_response = raw_ai_response.strip()[7:]
        if raw_ai_response.strip().endswith("```"):
            raw_ai_response = raw_ai_response.strip()[:-3]
    return(json.loads(raw_ai_response))

    # except json.JSONDecodeError as e:
    #     # Log the full raw_ai_response here for debugging in production
    #     print(f"JSONDecodeError: {e}")
    #     print(f"Problematic AI response: {raw_ai_response}") # Show the problematic string
    #     return Response({"error": f"Invalid JSON received from AI: {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    # except Exception as e:
    #     # Catch any other unexpected errors during processing or database interaction
    #     print(f"An unexpected error occurred: {e}")
    #     return Response({"error": f"An internal server error occurred: {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



##############   ###################################################################################################
#########   ########   ################################################################################################
#######   ############  ############################################################################################
##########  ######   ##############################################################################################
###############   ##################################################################################################


# Initialize OpenAI client
# client = OpenAI(api_key=settings.OPENAI_API_KEY)

# def get_openai_response(module):
#     try:
#         prompt = {
#         "listening" : f"""
#             Create four IELTS listening test about different topics from simple to difficulty level.
#             The scenario should be realistic and engaging, such as a university lecture, job interview, or everyday conversation.

#             Generate:
#             1. A detailed transcript of a 3-4 minute audio scenario for each test
#             2. 10 questions of mixed types (multiple choice, fill in the blank, short answer) for each test
#             3. Correct answers for each question

#             Format your response as valid JSON with this structure:
#             {{
#                 "test":"Modelset title",
#                 "sections:[
#                 {{
#                 "title": "test title 1",
#                 "topic": "On what topic the transcript is",
#                 "difficulty":"How difficult is this section",
#                 "transcript": "detailed transcript here",
#                 "questions": [
#                     {{
#                         "type": "multiple_choice",
#                         "question": "question text",
#                         "options": ["A", "B", "C", "D"],
#                         "correct_answer": "A"
#                     }},
#                     {{
#                         "type": "fill_blank",
#                         "question": "Complete the sentence: The meeting is scheduled for ____",
#                         "correct_answer": "3 PM"
#                     }}
#                 }},
#                 {{
#                 "title": "test title 2",
#                 "topic": "On what topic the transcript is",
#                 "difficulty":"How difficult is this section",
#                 "transcript": "detailed transcript here",
#                 "questions": [
#                     {{
#                         "type": "multiple_choice",
#                         "question": "question text",
#                         "options": ["A", "B", "C", "D"],
#                         "correct_answer": "A"
#                     }},
#                     {{
#                         "type": "fill_blank",
#                         "question": "Complete the sentence: The meeting is scheduled for ____",
#                         "correct_answer": "3 PM"
#                     }}
#                 }},
#                 {{
#                 "title": "test title 3",
#                 "transcript": "detailed transcript here",
#                 "topic": "On what topic the transcript is",
#                 "difficulty":"How difficult is this section",
#                 "questions": [
#                     {{
#                         "type": "multiple_choice",
#                         "question": "question text",
#                         "options": ["A", "B", "C", "D"],
#                         "correct_answer": "A"
#                     }},
#                     {{
#                         "type": "fill_blank",
#                         "question": "Complete the sentence: The meeting is scheduled for ____",
#                         "correct_answer": "3 PM"
#                     }}
#                 }},
#                 {{
#                 "title": "test title 4",
#                 "transcript": "detailed transcript here",
#                 "topic": "On what topic the transcript is",
#                 "difficulty":"How difficult is this section",
#                 "questions": [
#                     {{
#                         "type": "multiple_choice",
#                         "question": "question text",
#                         "options": ["A", "B", "C", "D"],
#                         "correct_answer": "A"
#                     }},
#                     {{
#                         "type": "fill_blank",
#                         "question": "Complete the sentence: The meeting is scheduled for ____",
#                         "correct_answer": "3 PM"
#                     }}
#                 }}
#                 ]
#             }}
#             """,
        
#         "reading" : f"""
#             Create an IELTS reading test about different topics with normal to difficulty level.
#             The test should include:
#             1. A three reading passage (around 700-900 words) on a relevant academic or general topic.
#             2. 10-15 questions of mixed IELTS reading types for each passage, including:
#                 - Multiple Choice (at least 3-4 questions)
#                 - True/False/Not Given (at least 3-4 questions)
#                 - Short Answer (1-2 words, or a short phrase)
#                 - Matching Headings (if applicable, provide a list of headings and sections to match)
#                 - Summary Completion (if applicable, provide a summary with blanks)

#             For each question, provide the correct answer(s). For matching headings, the correct answer should be a list of strings. For summary completion, the correct answer should be the missing word(s).

#             Format your response as valid JSON with this structure:
#             {{
#                 [
#                 {{
#                     "title": "Reading passage 1 Title",
#                     "passage": "Full reading passage text here, with paragraphs separated by double newlines.",
#                     "topic": "On what topic the passage is",
#                     "difficulty":"How difficult is this section",
#                     "questions": [
#                         {{
#                             "type": "multiple_choice",
#                             "question": "What is the main idea of paragraph 1?",
#                             "options": ["Option A", "Option B", "Option C", "Option D"],
#                             "correct_answer": "Option A",
#                             "passage_section": "Paragraph 1"
#                         }},
#                         {{
#                             "type": "true_false_not_given",
#                             "question": "The author believes technology will solve all problems.",
#                             "correct_answer": "False",
#                             "passage_section": "Paragraph 3"
#                         }},
#                         {{
#                             "type": "short_answer",
#                             "question": "According to the text, what is the primary benefit of renewable energy?",
#                             "correct_answer": "reduced carbon emissions",
#                             "passage_section": "Paragraph 5"
#                         }},
#                         {{
#                             "type": "matching_headings",
#                             "question": "Match the following headings to paragraphs A-D:",
#                             "options": ["I. The history of AI", "II. Ethical considerations", "III. Future applications"],
#                             "correct_answer": ["I", "II", "III"],
#                             "passage_section": "Paragraphs A-D"
#                         }},
#                         {{
#                             "type": "summary_completion",
#                             "question": "Complete the summary: The study found that regular exercise leads to improved physical health and mental ____.",
#                             "correct_answer": "well-being",
#                             "passage_section": "Paragraph 2"
#                         }}
#                 }},
#                 {{
#                     "title": "Reading passage 2 Title",
#                     "passage": "Full reading passage text here, with paragraphs separated by double newlines.",
#                     "topic": "On what topic the passage is",
#                     "difficulty":"How difficult is this section",
#                     "questions": [
#                         {{
#                             "type": "multiple_choice",
#                             "question": "What is the main idea of paragraph 1?",
#                             "options": ["Option A", "Option B", "Option C", "Option D"],
#                             "correct_answer": "Option A",
#                             "passage_section": "Paragraph 1"
#                         }},
#                         {{
#                             "type": "true_false_not_given",
#                             "question": "The author believes technology will solve all problems.",
#                             "correct_answer": "False",
#                             "passage_section": "Paragraph 3"
#                         }},
#                         {{
#                             "type": "short_answer",
#                             "question": "According to the text, what is the primary benefit of renewable energy?",
#                             "correct_answer": "reduced carbon emissions",
#                             "passage_section": "Paragraph 5"
#                         }},
#                         {{
#                             "type": "matching_headings",
#                             "question": "Match the following headings to paragraphs A-D:",
#                             "options": ["I. The history of AI", "II. Ethical considerations", "III. Future applications"],
#                             "correct_answer": ["I", "II", "III"],
#                             "passage_section": "Paragraphs A-D"
#                         }},
#                         {{
#                             "type": "summary_completion",
#                             "question": "Complete the summary: The study found that regular exercise leads to improved physical health and mental ____.",
#                             "correct_answer": "well-being",
#                             "passage_section": "Paragraph 2"
#                         }}
#                 }},
#                 {{
#                     "title": "Reading passage 3 Title",
#                     "passage": "Full reading passage text here, with paragraphs separated by double newlines.",
#                     "topic": "On what topic the passage is",
#                     "difficulty":"How difficult is this section",
#                     "questions": [
#                         {{
#                             "type": "multiple_choice",
#                             "question": "What is the main idea of paragraph 1?",
#                             "options": ["Option A", "Option B", "Option C", "Option D"],
#                             "correct_answer": "Option A",
#                             "passage_section": "Paragraph 1"
#                         }},
#                         {{
#                             "type": "true_false_not_given",
#                             "question": "The author believes technology will solve all problems.",
#                             "correct_answer": "False",
#                             "passage_section": "Paragraph 3"
#                         }},
#                         {{
#                             "type": "short_answer",
#                             "question": "According to the text, what is the primary benefit of renewable energy?",
#                             "correct_answer": "reduced carbon emissions",
#                             "passage_section": "Paragraph 5"
#                         }},
#                         {{
#                             "type": "matching_headings",
#                             "question": "Match the following headings to paragraphs A-D:",
#                             "options": ["I. The history of AI", "II. Ethical considerations", "III. Future applications"],
#                             "correct_answer": ["I", "II", "III"],
#                             "passage_section": "Paragraphs A-D"
#                         }},
#                         {{
#                             "type": "summary_completion",
#                             "question": "Complete the summary: The study found that regular exercise leads to improved physical health and mental ____.",
#                             "correct_answer": "well-being",
#                             "passage_section": "Paragraph 2"
#                         }}
#                 }}
#                 ]
#             }}
#                     """,
#         "writing" : f"""
#                 Generate an IELTS Writing Task 1 prompt for a simple or difficulty level test on the any topic.
#                 The prompt should describe a visual (e.g., a graph, chart, map, or process diagram) and ask the candidate to summarize, describe, or explain the information in their own words.
#                 Specify a minimum word count of 150 words.

#                 Generate an IELTS Writing Task 2 prompt for a simple or difficulty  level test on any topic .
#                 The prompt should present an opinion, argument, or problem and ask the candidate to write an essay in response.
#                 Specify a minimum word count of 250 words.

#                 Format your response as valid JSON with this structure:
#                 {{
#                     [
#                     {{
#                     "title": "Writing Task 1: [Brief Description]",
#                     "task_type": "Task 1",
#                     "prompt": "Describe the information shown in the [visual type] below...",
#                     "word_count_min": 150,
#                     "image":"Image link"
#                     }},
#                     {{
#                     "title": "Writing Task 2: [Essay Topic]",
#                     "task_type": "Task 2",
#                     "prompt": "Write an essay on the following topic: [Essay question here]...",
#                     "word_count_min": 250
#                     }}
#                     ]
#                 }}
#                 """,
#         "speaking" : f"""
#             Generate an IELTS speaking test form simple to difficulty level on different topic .
#             The test should include:
#             1. Part 1: 3-4 general questions about familiar topics.
#             2. Part 2: A cue card with a topic and 3-4 bullet points to cover, followed by a general instruction.
#             3. Part 3: 3-4 discussion questions related to the Part 2 topic, but more abstract.

#             Format your response as valid JSON with this structure:
#             {{
#                 "title": "Speaking Test: [Topic]",
#                 "part1_questions": [
#                     "Question 1?",
#                     "Question 2?"
#                 ],
#                 "part2_prompt": "Describe a time when you helped someone...",
#                 "part2_follow_up_questions": [
#                     "You should say:",
#                     "who the person was",
#                     "what the situation was",
#                     "how you helped them",
#                     "and explain how you felt about helping this person."
#                 ],
#                 "part3_questions": [
#                     "Let's talk about helping others in general. Why do people help others?",
#                     "Do you think people are more or less helpful now than in the past?"
#                 ]
#             }}
#             """
#             }
        
#         # Call OpenAI API for text generation
#         text_gen_response = client.chat.completions.create(
#             model="gpt-4",
#             messages=[
#                 {"role": "system", "content": f"You are an IELTS {module} test creator. Generate realistic IELTS {module} tests."},
#                 {"role": "user", "content": prompt[module]}
#             ],
#             temperature=0.7,
#             response_format={"type": "json_object"} 
#         )
#         task_content = json.loads(text_gen_response.choices[0].message.content)
#         return task_content

#     except Exception as e:
#         return Response(
#             {'error': f'Failed to generate speaking test: {str(e)}'}, 
#             status=status.HTTP_500_INTERNAL_SERVER_ERROR
#         )


# def get_openai_audio_response(transcript):
#     audio_response = client.audio.speech.create(
#                 model="tts-1", # or tts-1-hd for higher quality
#                 voice="alloy", # or 'nova', 'shimmer', 'echo', 'fable', 'onyx'
#                 input=transcript,
#             )
#     return audio_response