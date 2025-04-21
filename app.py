from flask import Flask, render_template, request, jsonify
from openai import OpenAI
import os

app = Flask(__name__)

# question database
questions_db = {
    'brewing': {
        'easy': {
            'french_press': ['What is a French press?', 'Describe the pour-over brewing method.'],
            'pour_over': ['What is pour-over brewing?', 'Describe the drip brewing method.']
        },
        'medium': {
            'french_press': ['How do you adjust the grind size for pour-over?', 'What is the ideal water temperature for brewing French press?'],
            'pour_over': ['How do you adjust the grind size for pour-over?', 'What factors affect the pour-over brewing process?']
        },
        'hard': {
            'french_press': ['Explain the science behind the French press extraction process.', 'How does water quality impact brewing methods?'],
            'pour_over': ['What is the impact of the pouring technique on pour-over coffee extraction?', 'How does the water temperature affect pour-over extraction?']
        }
    },
    'espresso': {
        'easy': {
            'espresso_shot': ['What is an espresso shot?', 'Name the main components of an espresso machine.'],
            'espresso_machine': ['What are the basic functions of an espresso machine?', 'How does a steam wand work?']
        },
        'medium': {
            'espresso_shot': ['Describe the process of extracting a perfect espresso shot.', 'How do you measure espresso grind size?'],
            'espresso_machine': ['What are the key adjustments you can make on an espresso machine?', 'Explain the role of pressure in espresso extraction.']
        },
        'hard': {
            'espresso_shot': ['Explain how pressure affects espresso extraction.', 'What is the role of temperature in espresso brewing?'],
            'espresso_machine': ['How do you adjust the machine for optimal espresso extraction?', 'What are the challenges in extracting a perfect espresso shot?']
        }
    },
    'milk_steaming': {
        'easy': {
            'milk_basics': ['What is microfoam?', 'Why is milk temperature important?']
        },
        'medium': {
            'milk_basics': ['Describe how to steam milk for a cappuccino.']
        },
        'hard': {
            'milk_basics': ['Explain the science behind milk frothing and protein denaturation.']
        }
    },
    'latte_art': {
        'easy': {
            'basic_pours': ['What is a heart pour?', 'What milk texture is ideal for latte art?']
        },
        'medium': {
            'basic_pours': ['How do you pour a rosetta?']
        },
        'hard': {
            'advanced_techniques': ['Explain the technique of free pour tulips.']
        }
    },
    'grinding': {
        'easy': {
            'grind_basics': ['What does grind size affect?', 'Name grind sizes for French press and espresso.']
        },
        'medium': {
            'grind_basics': ['How does grind consistency impact brewing?']
        },
        'hard': {
            'grind_basics': ['Explain how grinder burr types affect grind quality.']
        }
    }
}

topic_descriptions = {
    'brewing': 'Learn about various brewing methods like pour-over, French press, and more.',
    'espresso': 'Explore the world of espresso, from extraction to perfecting your shot.',
    'milk_steaming': 'Master milk steaming techniques for perfect microfoam and latte texture.',
    'latte_art': 'Learn how to create beautiful latte art with various pouring techniques.',
    'grinding': 'Understand how grind size and consistency affect your coffee quality.'
}

subtopic_descriptions = {
    'brewing': {
        'french_press': 'French press coffee is made using a French press coffee maker, '
        'a simple but effective coffee brewing method. French press coffee makers '
        'typically consist of a glass or stainless steel carafe (sometimes stoneware or ceramic) '
        'and a lid which includes both a plunger and mesh filter. Coffee made with a French press '
        'is rich and flavorful with a smooth mouthfeel and robust body.',
        'pour_over': 'Pour over coffee is made by pouring hot water over coffee grounds '
        'held in a brew basket. As the water is poured, gravity works to pull the water through '
        'the grounds and extracts freshly brewed coffee directly into a mug or carafe. '
        'When brewing pour over coffee, it’s important to do 3-4 circular pours over the grounds; '
        'the initial pour is to “bloom” the coffee grounds and extract flavor, while the subsequent pours '
        'help to develop a consistent brew.'
    },
    'espresso': {
        'espresso_shot': 'Espresso refers to a concentrated shot of coffee with a rich body and '
        'a layer of foamy crema on top. A proper shot of espresso is made using an espresso machine, '
        'where pressurized hot water passes through a puck of finely ground and densely packed coffee, '
        'usually in a ratio of two parts water to one part coffee. The resulting shot of espresso is typically only .75 to 2 ounces.',
        'espresso_machine': 'An espresso machine is a specialized coffee brewing appliance that uses '
        'high pressure to force hot water through finely-ground coffee, resulting in a concentrated, '
        'flavorful shot called espresso. This rich, aromatic beverage serves as the base for a variety '
        'of specialty coffee drinks like lattes, macchiatos, and cappuccinos. '
    },
    'milk_steaming': {
        'milk_basics': 'Steamed milk differs from frothed milk in that it is always hot and '
        'is slightly more watery. Foam is created by either frothing milk or steaming it. '
        'But while frothed milk has a thick foam, streaming milk creates a finer, '
        'more delicate type of foam — which experienced baristas call “microfoam.” '
        'Steaming milk creates very small air bubbles, and milk that has been steamed '
        'is heavier and acquires a velvety texture. Milk steaming is the process of steaming and frothing milk involves '
        'heating milk while simultaneously injecting air into it to prepare it for use '
        'in an espresso-based specialty coffee drink (espresso drink).'
    },
    'latte_art': {
        'basic_pours': 'Latte art is the design made on top of milk-based espresso drinks '
        'created by a technique used by baristas. Using a specific pouring technique, '
        'baristas make hearts, rosettas, and more out of steamed milk and espresso. '
        'Though latte art doesn’t affect the taste of your beverage, it does add '
        'an aesthetic experience intended to elevate the enjoyment of the beverage '
        'while demonstrating mastery of milk frothing, which does influence the quality of a latte.',
        'advanced_techniques': 'Free-pouring is a more advanced technique that involves pouring milk '
        'directly into the espresso without using tools to manipulate the design. This requires a lot '
        'of practice and control over your milk frothing and pouring technique to create sophisticated '
        'designs like multi-layered tulips or intricate swans.'
    },
    'grinding': {
        'grind_basics': 'The grind size you use ultimately impacts the coffees taste once it comes '
        'into contact with water. How fine or how coarse the beans are ground affects how fast '
        'the water will pass through them, determining the strength of your coffee. '
        'Grind size is just one variable that affects coffee extraction. The shape of a coffee brewer, '
        'depth of the brew bed, type of filter used, water temperature, ratio of coffee to water,'
        ' and contact time are some factors that can also impact extraction. As a result, grind size '
        'must always be considered in concert with these other brewing variables. '
    }
}

learning_sources = {
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

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/get_questions')
def get_questions():
    topic = request.args.get('topic')
    difficulty = request.args.get('difficulty')
    subtopic = request.args.get('subtopic')

    if topic and difficulty:
        questions = questions_db.get(topic, {}).get(difficulty, {}).get(subtopic, [])
        description = topic_descriptions.get(topic, "")
        subtopic_description = subtopic_descriptions.get(topic, {}).get(subtopic, "")
        return jsonify({
            'description': description,
            'subtopic_description': subtopic_description,
            'questions': questions
        })
    else:
        return jsonify({'description': "", 'subtopic_description': "", 'questions': []})

@app.route('/get_subtopics')
def get_subtopics():
    topic = request.args.get('topic')
    difficulties = questions_db.get(topic, {})
    subtopics = set()

    for level in difficulties.values():
        subtopics.update(level.keys())

    return jsonify({'subtopics': sorted(subtopics)})

@app.route('/evaluate', methods=['POST'])
def evaluate():
    data = request.get_json()
    question = data.get('question')
    answer = data.get('answer')
    difficulty = data.get('difficulty')
    topic = data.get('topic')

    prompt = f"""
    You are an expert barista tutor. Evaluate the following answer based on its accuracy, completeness, and clarity.

    **Question:** {question}  
    **User's Answer:** {answer}  
    **Topic:** {topic}  
    **Difficulty:** {difficulty}  

    Provide formative feedback in 2-3 sentences.
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "system", "content": "You are a helpful barista tutor."},
                      {"role": "user", "content": prompt}],
            temperature=0.7
        )
        feedback = response.choices[0].message.content.strip()

    except Exception as e:
        feedback = "Sorry, there was an error processing your answer. Please try again."

    return jsonify({
    'feedback': feedback,
    'sources': learning_sources.get(topic, [])
    })


if __name__ == '__main__':
    app.run(debug=True)
