import requests
from django.conf import settings
from rest_framework import status
from rest_framework.response import Response


def evaluate_with_llm(**kwargs):
        if kwargs.get("llm_model"):
            if module:=kwargs.get("module"):
                task_questions = kwargs.get("task_prompts")
                task_answers = kwargs.get("task_answers")
                prompt = get_prompt(module, task_questions, task_answers)
                print(prompt)
                
            url = settings.AI_SERVICE_URL
            api_key = settings.AI_SERVICE_KEY

            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json",
                "x-api-key": api_key,
            }
            response = requests.post(
                    url,
                    json={
                        "service": kwargs.get("service"),
                        "provider_name": kwargs.get("llm_model"),
                        "model": kwargs.get("model"),
                        "payload": {
                            "text": prompt,
                            "voice": "alloy",
                            "speed": 1.0
                        },
                        "cost": 0,
                    },
                    headers=headers
                )
            print("****************")
            print(response)
            print("****************")
            print(response.json())
            print("****************")
            print(response.content )
            print("****************")
            if response.status_code != 200:
                return {"band_score":0,"error":response.json()}   
            return response.json()["result"]
        else:
            return Response({"error":"Select AI model"}, status=status.HTTP_400_BAD_REQUEST)
        
    
    
####################   #########################################################################################
#################   ############################################################################################
############   ###### ###########################################################################################
#############    ######  ##########################################################################################
####################   #########################################################################################


def get_prompt(module, task_questions=None, task_answers=None):
    prompt = {
        "writing" : f"""
                You are an IELTS writing examiner. Evaluate the following user response for IELTS.
                Provide a band score (0-9) and detailed feedback based on the four IELTS writing criteria:
                1. Task Achievement/Response (TR/TA)
                2. Coherence and Cohesion (CC)
                3. Lexical Resource (LR)
                4. Grammatical Range and Accuracy (GRA)

                Task 1:
                Prompt:{task_questions.get("task_1")}
                User Response: {task_answers.get("task_1")}
                
                
                Task 2:
                Prompt:{task_questions.get("task_2")}
                User Response: {task_answers.get("task_2")}
                
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
        "speaking" : f"""
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
    return prompt[module]



def calculate_ielts_band(module: str, correct_answers: int) -> float:
    if not (0 <= correct_answers <= 40):
        raise ValueError("Correct answers must be between 0 and 40.")

    module = module.lower()

    # Listening band conversion
    listening_bands = {
        range(39, 40): 9.0,
        range(37, 38): 8.5,
        range(35, 36): 8.0,
        range(32, 34): 7.5,
        range(30, 31): 7.0,
        range(25, 29): 6.5,
        range(23, 24): 6.0,
        range(18, 22): 5.5,
        range(16, 17): 5.0,
        range(13, 15): 4.5,
        range(10, 12): 4.0,
    }

    # Academic Reading band conversion
    reading_bands = {
        range(39, 41): 9.0,
        range(37, 39): 8.5,
        range(35, 37): 8.0,
        range(33, 35): 7.5,
        range(30, 32): 7.0,
        range(27, 29): 6.5,
        range(23, 26): 6.0,
        range(19, 22): 5.5,
        range(15, 18): 5.0,
        range(13, 14): 4.5,
        range(10, 12): 4.0
    }


    band_tables = {
        "listening": listening_bands,
        "reading": reading_bands,
    }

    bands = band_tables.get(module)
    if not bands:
        raise ValueError("Invalid module. Choose from 'reading' or 'listening'.")

    for score_range, band in bands.items():
        if correct_answers in score_range:
            return band

    return 0.0 



# "listening" : """
#                     Create a complete IELTS Listening mock test and return it ONLY as valid JSON. Do NOT include any extra text outside the JSON. The JSON must strictly follow the structure below:

#                     {
#                     \"sections\": [
#                         {
#                         \"task_type\": \"section_1\",
#                         \"title\": \"<Section Title>\",
#                         \"topic\": \"<Main Topic>\",
#                         \"difficulty\": \"beginner | intermediate | advanced\",
#                         \"transcript\": \"<Detailed transcript of 400–500 words with dialogues. Each dialogue must start with 'Speaker 1:', 'Speaker 2:' etc., separated by two newlines>\",
#                         \"questions\": [
#                             {
#                             \"questionNum\": \"1-4\",
#                             \"questionType\": \"Multiple Choice\",
#                             \"questionTitle\": \"Choose the correct answer.\",
#                             \"actualQuestions\": [
#                                 {
#                                 \"order\": \"1\",
#                                 \"label\": \"Where is the student planning to travel?\",
#                                 \"options\": [
#                                     { \"label\": \"A. Paris\", \"value\": \"a\" },
#                                     { \"label\": \"B. Rome\", \"value\": \"b\" },
#                                     { \"label\": \"C. Berlin\", \"value\": \"c\" }
#                                 ]
#                                 }
#                             ]
#                             },
#                             {
#                             \"questionNum\": \"5-7\",
#                             \"questionType\": \"True-False-Not-Given\",
#                             \"questionTitle\": \"Write TRUE, FALSE, or NOT GIVEN.\",
#                             \"actualQuestions\": [
#                                 {
#                                 \"order\": \"5\",
#                                 \"label\": \"The student has visited France before.\",
#                                 \"options\": [
#                                     { \"label\": \"TRUE\", \"value\": \"true\" },
#                                     { \"label\": \"FALSE\", \"value\": \"false\" },
#                                     { \"label\": \"NOT GIVEN\", \"value\": \"not_given\" }
#                                 ]
#                                 }
#                             ]
#                             },
#                             {
#                             \"questionNum\": \"8-10\",
#                             \"questionType\": \"Short Answer\",
#                             \"questionTitle\": \"Answer in no more than two words.\",
#                             \"actualQuestions\": [
#                                 {
#                                 \"order\": \"8\",
#                                 \"label\": \"What is the student studying?\",
#                                 \"options\": []
#                                 }
#                             ]
#                             },
#                         ],
#                         \"answers\": { \"1\": \"b\", \"5\": \"false\", \"8\": \"history\", \"9\": \"museum\" }
#                         }
#                     ]
#                     }

#                     ### Listening Test Requirements:
#                     - 4 sections, each 400–500 word transcript (realistic scenarios like university orientation, trip booking, lecture, business meeting).
#                     - Each section has exactly 10 questions:
#                     * Multiple Choice (3–4)
#                     * True-False-Not Given (3–4)
#                     * Short Answer (1–2)
#                     - For T/F/NG, options must be EXACTLY:
#                     [{\"label\": \"TRUE\", \"value\": \"true\"}, {\"label\": \"FALSE\", \"value\": \"false\"}, {\"label\": \"NOT GIVEN\", \"value\": \"not_given\"}]
#                     - Output ONLY valid JSON.
#                     - Vary topics and wording each time.
#                     - Keep values and answers in lowercase for consistency.
#                     - Do not have space , make like Speaker1, Speaker2
#         """,
#         "reading" : """
#                     Create a complete IELTS Reading mock test and return it ONLY as valid JSON. Do NOT include any extra explanation outside the JSON. The JSON must strictly follow this structure:

#                     {
#                     \"passages\": [
#                         {
#                         \"task_type\": \"passage_1\",
#                         \"title\": \"<Passage Title>\",
#                         \"topic\": \"<Topic>\",
#                         \"difficulty\": \"beginner | intermediate | advanced\",
#                         \"passage\": \"<Full passage text of 700–900 words, divided into paragraphs labeled Passage A, Passage B, etc., with HTML tags for paragraph separation>\",
#                         \"questions\": [
#                             {
#                             \"questionNum\": \"1-4\",
#                             \"questionType\": \"Matching Heading\",
#                             \"questionTitle\": \"Choose the correct heading for each paragraph from the list below.\",
#                             \"actualQuestions\": [
#                                 {
#                                 \"order\": \"1\",
#                                 \"label\": \"Paragraph A\",
#                                 \"options\": [
#                                     { \"label\": \"Heading 1: The Origins of the Internet\", \"value\": \"heading 1\" },
#                                     { \"label\": \"Heading 2: Modern Applications\", \"value\": \"heading 2\" },
#                                     { \"label\": \"Heading 3: Early Challenges\", \"value\": \"heading 3\" }
#                                 ]
#                                 }
#                             ]
#                             },
#                             {
#                             \"questionNum\": \"5-8\",
#                             \"questionType\": \"True-False-Not-Given\",
#                             \"questionTitle\": \"Write TRUE, FALSE, or NOT GIVEN.\",
#                             \"actualQuestions\": [
#                                 {
#                                 \"order\": \"5\",
#                                 \"label\": \"The internet was invented in the 21st century.\",
#                                 \"options\": [
#                                     { \"label\": \"TRUE\", \"value\": \"true\" },
#                                     { \"label\": \"FALSE\", \"value\": \"false\" },
#                                     { \"label\": \"NOT GIVEN\", \"value\": \"not_given\" }
#                                 ]
#                                 }
#                             ]
#                             },
#                             {
#                             \"questionNum\": \"9-11\",
#                             \"questionType\": \"Multiple Choice\",
#                             \"questionTitle\": \"Choose the correct letter.\",
#                             \"actualQuestions\": [
#                                 {
#                                 \"order\": \"9\",
#                                 \"label\": \"What was the primary purpose of ARPANET?\",
#                                 \"options\": [
#                                     { \"label\": \"A. Commercial Use\", \"value\": \"a\" },
#                                     { \"label\": \"B. Academic Research\", \"value\": \"b\" },
#                                     { \"label\": \"C. Entertainment\", \"value\": \"c\" }
#                                 ]
#                                 }
#                             ]
#                             },
#                             {
#                             \"questionNum\": \"12-13\",
#                             \"questionType\": \"Short Answer\",
#                             \"questionTitle\": \"Answer in NO MORE THAN TWO WORDS.\",
#                             \"actualQuestions\": [
#                                 {
#                                 \"order\": \"12\",
#                                 \"label\": \"What year was ARPANET launched?\",
#                                 \"options\": []
#                                 }
#                             ]
#                             },
#                         ],
#                         \"answers\": { \"1\": \"heading 1\", \"5\": \"false\", \"9\": \"b\", \"12\": \"1969\", \"13\": \"military\" }
#                         }
#                     ]
#                     }

#                     ### Reading Test Requirements:
#                     - 3 passages, each 700–900 words.
#                     - Passages paragraphs are seperated by html tag and Paragraph name like Paragraph A,Paragraph B.
#                     - Total 40 questions strictly (10–15 per passage).
#                     - Include ALL question types: Matching Heading,  Multiple Choice, True/False/Not Given, Short Answer.
#                     - Use example structures above for consistency all the time.
#                     - In Matching Heading stricly follow the options structure.
#                     - Don't include html tag in questions label
#                     - Output ONLY valid JSON.
#                     - Vary topics and question phrasing each time.
#                     - Keep values and answers in lowercase for consistency.
#                     - For difficulty choices are beginner, intermediate and advanced.
#         """,
                        
#         "writing" : f"""
#                 Generate an IELTS Writing Task 1 prompt for a simple or difficulty level test on the any topic.
#                 The prompt should describe a visual (e.g., a graph, chart, map, or process diagram) and ask the candidate to summarize, describe, or explain the information in their own words.
#                 Specify a minimum word count of 150 words.

#                 Generate an IELTS Writing Task 2 prompt for a simple or difficulty  level test on any topic .
#                 The prompt should present an opinion, argument, or problem and ask the candidate to write an essay in response.
#                 Specify a minimum word count of 250 words.
                
#                 For difficulty choices are beginner, intermediate and advanced.

#                 Format your response as valid JSON with this structure:
#                 {{
#                     "tasks:[
#                     {{
#                     "title": "Writing Task 1: [Brief Description]",
#                     "task_type": "task_1",
#                     "topic": "On what topic the passage is",
#                     "difficulty":"How difficult is this section",
#                     "questions": "Describe the information shown in the [visual type] below...",
#                     "min_word_count": 150,
#                     "task_url":"Image link"
#                     }},
#                     {{
#                     "title": "Writing Task 2: [Essay Topic]",
#                     "task_type": "task_2",
#                     "topic": "On what topic the passage is",
#                     "difficulty":"How difficult is this section",
#                     "questions": "Write an essay on the following topic: [Essay question here]...",
#                     "min_word_count": 250
#                     }}
#                     ]
#                 }}
#         """,
#         "speaking" : f"""
#             Generate an IELTS speaking test form simple to difficulty level on different topic .
#             The test should include:
#             1. Part 1: 3-4 general questions about familiar topics.
#             2. Part 2: A cue card with a topic and 3-4 bullet points to cover, followed by a general instruction.
#             3. Part 3: 3-4 discussion questions related to the Part 2 topic, but more abstract.
#             For difficulty choices are beginner, intermediate and advanced.
#             Format your response as valid JSON with this structure:
#             {{
#                 "parts":[
#                     {{
#                         "task_type": "part1",
#                         "title": "Part : Title",
#                         "topic": "On what topic the part is",
#                         "difficulty":"How difficult is this section",
#                         "questions": [
#                             "Question 1?",
#                             "Question 2?"
#                         ]
#                     }},
#                     {{
#                         "task_type": "part_2",
#                         "title": "Part : Title",
#                         "topic": "On what topic the part is",
#                         "difficulty":"How difficult is this part",
#                         "questions":  "Describe a time when you helped someone...",
#                     }},
#                     {{
#                         "task_type": "part_2_follow_up",
#                         "title": "Part : Title",
#                         "topic": "On what topic the part is",
#                         "difficulty":"How difficult is this part",
#                         "questions": [
#                             "You should say:",
#                             "who the person was",
#                             "what the situation was",
#                             "how you helped them",
#                             "and explain how you felt about helping this person."
#                         ],
#                     }},
#                     {{
#                         "task_type": "part_3",
#                         "title": "Part : Title",
#                         "topic": "On what topic the part is",
#                         "difficulty":"How difficult is this part",
#                         "questions": [
#                             "Let's talk about helping others in general. Why do people help others?",
#                             "Do you think people are more or less helpful now than in the past?"
#                         ]   
#                     }}
#                 ]
#             }},
#         """,