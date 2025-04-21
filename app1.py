from flask import Flask, render_template, request, jsonify
from openai import OpenAI
import os

app = Flask(__name__)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# List of subtopics for each topic (manually set)
SUBTOPICS = {
    "brewing": ["french_press", "pour_over"],
    "espresso": ["espresso_shot", "espresso_machine"],
    "milk_steaming": ["milk_basics", "foam_consistency"],
    "latte_art": ["basic_pours", "advanced_techniques"],
    "grinding": ["grind_basics", "grind_consistency"]
}

# Links (also manually set, gpt can't generate the correct links)
LEARNING_SOURCES = {
    'brewing': [
        'https://www.aboutcoffee.org/brewing/',
        'https://en.wikipedia.org/wiki/French_press'
    ],
    'espresso': [
        'https://methodicalcoffee.com/blogs/coffee-culture/how-to-enjoy-espresso-the-complete-guide-to-drinking-espresso-for-beginners',
        'https://en.wikipedia.org/wiki/Espresso',
        'https://methodicalcoffee.com/blogs/coffee-culture/espresso-machine-vs-coffee-maker-which-is-best-for-home-use',
        'https://en.wikipedia.org/wiki/Espresso_machine'
    ],
    'milk_steaming': [
        'https://espressocoffeeguide.com/all-about-espresso/how-to-make-espresso/steaming-and-frothing-milk/',
        'https://espresso-works.com/blogs/coffee-life/understanding-the-difference-between-steaming-and-frothing-milk?',
        'https://methodicalcoffee.com/blogs/brew-guides/how-to-steam-milk-for-latte'
    ],
    'latte_art': [
        'https://www.coffeescience.org/latte-art-beginners-guide/',
        'https://methodicalcoffee.com/blogs/brew-guides/how-to-pour-latte-art-pro-tips-for-beginners?',
        'https://www.rossocoffeeroasters.com/en-us/blogs/rosso-journal/advanced-latte-art-tips?',
        'https://rockcreekcoffee.com/blogs/blog/the-art-of-latte'
    ],
    'grinding': [
        'https://levelground.com/blogs/blog/coffee-grinds?',
        'https://counterculturecoffee.com/blogs/counter-culture-coffee/coffee-basics-grind-size?'
    ]
}

def generate_openai_response(prompt):
    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a helpful barista tutor."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=80,
            temperature=0
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"OpenAI error: {e}")
        return "N/A"

@app.route('/')
def index():
    return render_template('index1.html')

@app.route('/get_questions')
def get_questions():
    topic = request.args.get('topic')
    subtopic = request.args.get('subtopic')
    difficulty = request.args.get('difficulty')

    # Generate topic and subtopic descriptions
    topic_prompt = f"Explain the topic '{topic}' in simple terms."
    topic_description = generate_openai_response(topic_prompt)

    subtopic_prompt = f"Give a short educational explanation of the subtopic '{subtopic}' under the topic '{topic}'."
    subtopic_description = generate_openai_response(subtopic_prompt)

    # Generate quiz questions
    question_prompt = f"Generate 3 {difficulty} quiz questions for the subtopic '{subtopic}' under topic '{topic}'."
    questions_text = generate_openai_response(question_prompt)

    questions = [q.strip() for q in questions_text.split("\n") if q.strip()] if questions_text != "N/A" else []

    return jsonify({
        "description": topic_description,
        "subtopic_description": subtopic_description,
        "questions": questions
    })

@app.route('/evaluate', methods=['POST'])
def evaluate():
    data = request.get_json()
    question = data.get('question')
    answer = data.get('answer')
    topic = data.get('topic')

    prompt = f"Question: {question}\nStudent's Answer: {answer}\nGive formative feedback on this answer and suggest improvements."
    feedback_text = generate_openai_response(prompt)

    sources = LEARNING_SOURCES.get(topic, [])

    return jsonify({
        "feedback": feedback_text,
        "sources": sources
    })

if __name__ == '__main__':
    app.run(debug=True)
