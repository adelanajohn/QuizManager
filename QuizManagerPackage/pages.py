from flask import Blueprint, render_template, redirect, request, session, url_for
import boto3
import json

bp = Blueprint("pages", __name__)

@bp.route("/", methods=("GET", "POST"))
def home():
    session['quizFlag']="1"
    if request.method == "POST":
        topic = request.form["topic"]
        difficulty = request.form["difficulty"]

        if topic:
            return redirect(url_for("pages.quiz"))
        
    return render_template("pages/home.html")


@bp.route("/result")
def result():
    return render_template("pages/result.html")


@bp.route("/quiz", methods=("GET", "POST"))
def quiz():
    if request.method == "POST":
        if session['quizFlag']=="1": # Ensure that LLM is called only at the beginning of the quiz
            topic=request.form.get('topic')
            difficulty=request.form.get('difficulty')
            jsonResponse=get_response(topic, difficulty) # Call LLM

            # Extract questions from JSON response
            startPosition = jsonResponse.index("[")
            endPosition = jsonResponse.rindex("]")
            questions = jsonResponse[startPosition:endPosition+1]

            session['questions'] = questions # LLM response    
            session['questionIndex'] = 1 # Question counter      
            session['quizFlag']="0" # To ensure that LLM is called only at the beginning of the quiz
            session['answer']=""
            session['score']=0

        questionIndex = session['questionIndex']

        # Convert JSON data to a Python object 
        data = json.loads(session['questions']) 
        questionCount = len(data) # Number of questions  
        session['questionCount'] = questionCount  

        # Iterate through the JSON array 
        i=0
        for item in data: 
            i+=1
            question=item["question"]
            answer=item["answer"]
            options=item["options"]
            j=0
            for item in options: 
                j+=1
                if j==1:
                    option1=options[0]
                if j==2:
                    option2=options[1]
                if j==3:
                    option3=options[2]
                if j==4:
                    option4=options[3]    

            if questionIndex==i:
                break  
                
        # Scoring
        userResponse=request.form.get('QuestionOptions')
        if i>1 and len(session['answer'])>=1:
            if userResponse==session['answer'][0]:
                session['score']+=1
        session['answer']=answer # Save answer        
        
        if questionIndex==questionCount+1: # Last question                
            score=session['score']
            scorePercent=(score/questionCount)*100
            resultMessage=""
            if scorePercent==100:
                resultMessage="Congrats🙂! You passed: " + str(round(scorePercent, 2)) + "%. ⭐️⭐️⭐️⭐️⭐️"
            elif scorePercent>=80:
                resultMessage="Congrats🙂! You passed: " + str(round(scorePercent, 2)) + "%."
            else:
                resultMessage="Sorry🙁! You failed: " + str(round(scorePercent, 2)) + "%."
            return render_template("pages/result.html",resultMessage=resultMessage) # Show result
        else:
            session['questionIndex'] = questionIndex + 1 # Next question
          
        return render_template("pages/quiz.html", questionIndex=questionIndex, questionCount=questionCount, question=question, answer=answer, option1=option1, option2=option2, option3=option3, option4=option4, score=session['score'])
    return render_template("pages/home.html")
        

def get_response(topic, difficulty_level): #
    bedrock=boto3.client(service_name="bedrock-runtime")

    prompt_example = """
    <example>
    {
			"question": "What is the primary goal of DevOps?",
			"options": [
				"A. To improve collaboration between development and operations teams",
				"B. To automate software deployment processes",
				"C. To reduce software development costs",
				"D. To increase software development speed"
			],
			"answer": "A. To improve collaboration between development and operations teams"
		}
    </example>
    """
    
    prompt_data="Please generate 5 questions on " + topic + ". Difficulty level is " + difficulty_level + ". Please include four options and the correct answer. Ensure that the options are unique. Output response is json format." + prompt_example

    payload={
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 2000,
        "temperature": 0.8,
        "messages": [
            {
                "role": "user",
                "content": [{ "type": "text", "text": prompt_data}]
            }
        ],
    }

    body=json.dumps(payload)
    model_id="anthropic.claude-3-sonnet-20240229-v1:0"
    response=bedrock.invoke_model(
        modelId=model_id,
        contentType="application/json",
        accept="application/json",
        body=body
    )

    response_body=json.loads(response.get("body").read())
    response_text=response_body.get("content")[0].get("text")
    return response_text
