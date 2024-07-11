# The QuizManager Generative AI App ⭐️

## 1. What is the QuizManager App 🤷?
This project generates quizzes on different topics using generative AI. The application also grades quizzes taken by users. This project demonstrates the significant impact of well-crafted prompts on AI-generated content, highlighting the importance of prompt engineering in maximizing the potential of generative AI systems.

This project is intended for educational purposes only and not for production use.

## 2. Prompt Engineering 🏗️
Prompt engineering is a crucial skill in working with generative AI models. It involves crafting effective inputs (prompts) to guide AI models in producing desired outputs. 

Prompt engineering techniques include zero-shot prompting, few-shot prompting, chain-of-thought prompting, and ReAct (reasoning and acting). This app makes use of the few-shot prompting technique, which provides a few examples of the task before asking the model to perform it.

## 3. Solution Overview 🛠️
The following figure shows the architecture of the QuizManager app.

![Architecture diagram](images/architecture.png)

This app utilizes the following patterns:
- Packages: For a hierarchical structuring of the module namespace.
- Application factory: An application factory in [Flask](https://flask.palletsprojects.com) is a design pattern useful in scaling Flask projects. It helps in creating and configuring Flask projects flexibly and efficiently, making it easier to develop, test, and maintain as it grows and evolves.
- Blueprints: Blueprints are a way to organize Flask applications into reusable and maintainable units.
- Templates: Templates are files that contain static data as well as placeholders for dynamic data. A template is rendered with specific data to produce a final document. This app makes use of the [Jinja](https://jinja.palletsprojects.com) template engine.

### 3.1 Model Selection
A selection of models was reviewed, with consideration for use cases, model attributes, maximum tokens, cost, accuracy, performance, and supported languages. Based on this, Anthropic Claude-3 Sonnet was selected as best suited for this use case, as it strikes a balance between intelligence and speed, and it optimizes on speed and cost.

### 3.2 Prerequisites

You first need to set up an AWS account and configure your [AWS Identity and Access Management](https://aws.amazon.com/iam) (IAM) permissions correctly. You then need to [request](https://catalog.workshops.aws/building-with-amazon-bedrock/en-US/prerequisites/bedrock-setup) Anthropic Claude 3 Sonnet model access on [Amazon Bedrock](https://aws.amazon.com/bedrock). You can find the code samples in the [GitHub repository](https://github.com/adelanajohn/QuizManager).

#### Python virtual environment setup
Establish a [Python venv module](https://docs.python.org/3/library/venv.html) virtual environment in the project directory and then proceed to install all necessary dependencies. By using a project-specific virtual environment, you ensure that all dependencies are installed exclusively within that environment, rather than system-wide.

Windows PowerShell
```shell
python -m venv venv
.\venv\Scripts\activate
```

macOS
```shell
python -m venv venv
source venv/bin/activate
```

You should see a parenthesized **(venv)** in front of the prompt after running the command, which indicates that you’ve successfully activated the virtual environment.

#### Add dependencies
Once you have activated your virtual environment, proceed with installing Flask.

```shell
python -m pip install Flask
```

#### Install requirements
```shell
python -m pip install -r requirements.txt
```

#### Configure AWS CLI options
Next, configure AWS CLI options. If this command is run with no arguments, you will be prompted for configuration values such as your AWS Access Key Id and your AWS Secret Access Key.
```shell
aws configure
```

```shell
AWS Access Key ID [****]:
AWS Secret Access Key [****]:
Default region name [us-east-1]: us-east-1
Default output format [json]: json
```

#### Run the Flask project

Windows PowerShell
```shell
python -m flask --app QuizManagerPackage run --port 8000 --debug
```

macOS
```shell
export FLASK_APP=QuizManagerPackage
python -m flask —app QuizManagerPackage run —port 8000 —debug
```

#### Quit the app
Press CTRL+C or ^C on the terminal. 

#### Exit the Python virtual environment
```shell
deactivate
```

### 3.3 Building the application

#### Application factory (/QuizManagerPackage/__init__.py)
Application Factory is a function that is responsible for creating the application object and its configuration.

```python
from flask import Flask

from QuizManagerPackage import (
    errors,
    pages
)

def create_app():
    app = Flask(__name__)
    app.secret_key = 'k0H$-2$Rb2*v'

    app.register_blueprint(pages.bp)
    app.register_error_handler(404, errors.page_not_found)
    return app
```

#### Blueprints (/QuizManagerPackage/pages.py)
Blueprints are modular components in Flask that encapsulate a collection of related views. They can be easily imported in the init file, providing a convenient way to organize and structure the application's routes and functionality.

```python
from flask import Blueprint, render_template, redirect, request, session, url_for
import boto3
import json

bp = Blueprint("pages", __name__)

# Home page
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
    
    prompt_data="Please generate 5 questions on " + topic + ". Difficulty level is " + difficulty_level + ". Please include four options and the correct answer. Output response is json format." + prompt_example

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
```
#### Page not found (/QuizManagerPackage/errors.py)
```python
from flask import render_template

def page_not_found(e):
    return render_template("errors/404.html"), 404
```

#### Base template (/QuizManagerPackage/templates/base.html)
The base template is designed to establish a uniform structure for your project while allowing flexibility in certain content areas through Jinja's block functionality.

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <title>Quiz Manager - {% block title %}{% endblock title %}</title>
  <link rel="stylesheet" href="{{ url_for('static', filename='styles.css') }}">
</head>
<body>
<h1>Quiz Manager</h1>
<section>
  <header>
    {% block header %}{% endblock header %}
  </header>
  <main>
    {% block content %}<p>No messages.</p>{% endblock content %}
  </main>
</section>
</body>
</html>
```

#### Child templates (/QuizManagerPackage/templates/pages)
Template inheritance allows you to build a base “skeleton” template that contains all the common elements of your site and defines blocks that child templates can override.

## 4. Conclusion 🌅

This guide walks you through how to build a Quiz Manager app powered by generative AI. It explores 
prompt engineering techniques leveraging the capabilities of Anthropic's Claude 3 Sonnet Large Language Model.