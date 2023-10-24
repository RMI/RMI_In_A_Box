from flask import Flask, render_template, request, redirect, url_for
import qa

app = Flask(__name__)

@app.route("/", methods=['GET', 'POST'])
def home():
    user_input = ""
    bot_response = ""
    if request.method == 'POST':
        user_input = request.form.get('user_input')
        bot_response = chatbot.get_response(user_input)  # Assuming get_response is a function in chatbot.py
    return render_template("home.html", user_input=user_input, bot_response=bot_response)

if __name__ == "__main__":
    app.run(debug=True)