from openai import OpenAI
import streamlit as st
import re
PROMPT = """
you are an IELTS examiner. your task is to evaluate a writing section in an IELTS academic
exam. you have to provide overall band score in <BAND_SCORE> </BAND_SCORE> tags and detailed evaluation in <EVALUATION></EVALUATION> tags . I will provide you the grading
criteria in <CRITERIA> </CRITERIA> tags. The user will send you the task and his answer and you should respond with a feedback on how well does the user follow the grading criteria and his score. Provide his score in this format <Score>Score</Score>.
<CRITERIA>
TASK RESPONSE (TR)
For Task 2 of both AC and GT Writing tests, candidates are required to formulate and
develop a position in relation to a given prompt in the form of a question or
statement, using a minimum of 250 words. Ideas should be supported by evidence,
and examples may be drawn from a candidate’s own experience.
The TR criterion assesses:
▪ how fully the candidate responds to the task.
▪ how adequately the main ideas are extended and supported.
▪ how relevant the candidate’s ideas are to the task.
▪ how clearly the candidate opens the discourse, establishes their position and
formulates conclusions.
▪ how appropriate the format of the response is to the task.
COHERENCE AND COHESION (CC)
This criterion is concerned with the overall organisation and logical development of
the message: how the response organises and links information, ideas and language.
Coherence refers to the linking of ideas through logical sequencing, while cohesion
refers to the varied and appropriate use of cohesive devices (e.g. logical connectors,
conjunctions and pronouns) to assist in making clear the relationships between and
within sentences.
The CC criterion assesses:
▪ the coherence of the response via the logical organisation of information
and/or ideas, or the logical progression of the argument.
▪ the appropriate use of paragraphing for topic organisation and presentation.
▪ the logical sequencing of ideas and/or information within and across
paragraphs.
▪ the flexible use of reference and substitution (e.g. definite articles, pronouns).
▪ the appropriate use of discourse markers to clearly mark the stages in a
response, e.g. [First of all | In conclusion], and to signal the relationship between ideas and/or information, e.g. [as a result | similarly].

LEXICAL RESOURCE (LR)
This criterion refers to the range of vocabulary the candidate has used and the
accuracy and appropriacy of that use in terms of the specific task.
The LR criterion assesses:
▪ the range of general words used (e.g. the use of synonyms to avoid repetition).
▪ the adequacy and appropriacy of the vocabulary (e.g. topic-specific items,
indicators of writer’s attitude).
▪ the precision of word choice and expression.
▪ the control and use of collocations, idiomatic expressions and sophisticated
phrasing.
▪ the density and communicative effect of errors in spelling.
▪ the density and communicative effect of errors in word formation.
GRAMMATICAL RANGE AND ACCURACY (GRA)
This criterion refers to the range and accurate use of the candidate’s grammatical
resource via the candidate’s writing at sentence level.
The GRA criterion assesses:
▪ the range and appropriacy of structures used in a given response (e.g. simple,
compound and complex sentences).
▪ the accuracy of simple, compound and complex sentences.
▪ the density and communicative effect of grammatical errors.
▪ the accurate and appropriate use of punctuation.
</CRITERIA>
"""

def get_text(display_text):
    text = st.text_input(display_text, "")
    if text:
        return text
    return None

def extract_score(text):
    """
      Extracting the score from the model's answer
    """
    numbers = re.findall(r'\d+\.\d+|\d+', text.lower())
    return float(numbers[-1]) if numbers and float(numbers[-1]) <= 9 else 6.5


def get_response(messages, client, model_name):
    if "davinci-002" not in model_name:
        response = client.chat.completions.create(
            messages=messages,
            model=model_name,
        )
        return response.choices[0].message.content
    else:
        prompt = ""
        for x in messages:
            prompt += f'{x["role"]} : {x["content"]}\n'
        prompt += "assistant: "
        response = client.completions.create(
           prompt=prompt,
            model=model_name,
        )
        return response.choices[0].text.strip()

def display_text(header, text):
    st.text_area(header, text)

def remove_tags(text):
    cleaned_text = re.sub(r'<[^>]*>', '', text)
    return cleaned_text
def main():
    global PROMPT
    st.title("Ielts-chatbot")

    client = OpenAI(api_key=st.session_state.openai_api_key)
    task = get_text("Enter Your Task:")
    answer = get_text("Enter Your Answer:")
    model_options = ["gpt-3.5-turbo", "davinci-002", "fine-tuned davinci-002", "fine-tuned gpt3.5"]
    selected_model = st.selectbox("Select Model:", model_options)
    st.session_state.openai_model = selected_model

    if selected_model == "fine-tuned gpt3.5":
        selected_model = st.session_state.finetuned_gpt_key
        st.session_state.openai_model = st.session_state.finetuned_gpt_key

    if selected_model == "fine-tuned davinci-002":
        selected_model = st.session_state.finetuned_dv02
        st.session_state.openai_model = st.session_state.finetuned_dv02

    if "openai_model" not in st.session_state:
        st.session_state["openai_model"] = "gpt-3.5-turbo"

    if task and answer:

        initial_feedback = get_response([{"role": "system", "content": PROMPT},
                   {"role": "user",
                    "content": f"Here is the task:\n <Task>{task}</Task> \n And here is my answer: \n <Answer>{answer}</Answer>"},
         ], client, st.session_state.openai_model)

        display_text("band_score", extract_score(initial_feedback))
        display_text("evaluation", remove_tags(initial_feedback))



    if "messages" not in st.session_state:
        st.session_state.messages = []
    if st.button("Generate Feedback"):
        if task and answer:
            st.session_state.messages = []
            st.session_state.messages.append({"role": "system", "content": PROMPT})
            st.session_state.messages.append({"role":"user",
                                                  "content": f"Here is the task:\n <Task>{task}</Task> \n And here is my answer: \n <Answer>{answer}</Answer>"})
            st.session_state.messages.append( {"role": "assistant", "content": initial_feedback})
        else:
            st.warning("Please enter a task and an answer before generating a feedback.")

    for index, message in enumerate(st.session_state.messages):
        if index > 2:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

    if prompt := st.chat_input("What is up?"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            print(st.session_state.messages)
            full_response = get_response(st.session_state.messages, client, st.session_state.openai_model)
                #message_placeholder.markdown(full_response + "▌")
            message_placeholder.markdown(full_response)
        st.session_state.messages.append({"role": "assistant", "content": full_response})

def login():
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False

    openai_api_key = st.text_input("Enter your OpenAI API", type="password")
    finetuned_gpt_key = st.text_input("Enter your finetuned GPT API", type="password")
    finetuned_dv02 = st.text_input("Enter your finetuned Dv02 API", type="password")
    if st.button("Login"):
        if openai_api_key and finetuned_gpt_key and finetuned_dv02:
            st.session_state.openai_api_key = openai_api_key
            st.session_state.finetuned_gpt_key = finetuned_gpt_key
            st.session_state.finetuned_dv02 = finetuned_dv02
            st.session_state.authenticated = True

        else:
            st.error("Enter all fields")
if __name__ == "__main__":
    if "authenticated" in st.session_state and st.session_state.authenticated:
        main()
    else:
        login()